
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid
from sqlalchemy.orm import Session
from api.config.supported_services import SUPPORTED_PROVIDERS, SUPPORTED_SERVICES_AWS, SUPPORTED_AUTH_MODES
from api.services.scan_engine import scan_list_service
from api.database import User, get_db
from api.endpoints.auth import get_current_user

router = APIRouter()

class AuthMode(BaseModel):
    """Mode d'authentification AWS via STS AssumeRole"""
    type: str = Field(..., description="Type d'authentification", example="sts")
    role_arn: str = Field(..., description="ARN du rôle AWS à assumer", example="arn:aws:iam::123456789012:role/CloudDiagnozeRole")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "sts",
                "role_arn": "arn:aws:iam::123456789012:role/CloudDiagnozeRole"
            }
        }


class ScanRequest(BaseModel):
    """Requête pour lancer un scan d'infrastructure AWS"""
    provider: str = Field(..., description="Fournisseur cloud (actuellement uniquement 'aws')", example="aws")
    services: List[str] = Field(..., description="Liste des services à scanner", example=["ec2", "s3"])
    auth_mode: AuthMode = Field(..., description="Mode d'authentification AWS")
    client_id: str = Field(..., description="Identifiant du client/projet", example="MonProjet-Production")
    regions: List[str] = Field(default=None, description="Régions AWS à scanner (toutes si non spécifié)", example=["eu-west-1", "eu-west-3"])

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "aws",
                "services": ["ec2", "s3"],
                "auth_mode": {
                    "type": "sts",
                    "role_arn": "arn:aws:iam::123456789012:role/CloudDiagnozeRole"
                },
                "client_id": "MonProjet-Production",
                "regions": ["eu-west-1", "eu-west-3"]
            }
        }


class ScanResponse(BaseModel):
    """Réponse après le lancement d'un scan"""
    scan_id: str = Field(..., description="Identifiant unique du scan", example="a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    status: str = Field(..., description="Statut du scan", example="QUEUED")
    message: str = Field(..., description="Message descriptif", example="Scan EC2, S3 démarré en arrière-plan")

    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "status": "QUEUED",
                "message": "Scan EC2, S3 démarré en arrière-plan"
            }
        }

@router.post("/scans", response_model=ScanResponse, status_code=202)
async def create_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Lance un scan d'infrastructure cloud.

    ⚠️ ISOLATION DES COMPTES : Le scan est automatiquement lié à l'utilisateur connecté.
    """
    
    # 1. Validation du provider
    if scan_request.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_PROVIDER",
                "message": f"Provider '{scan_request.provider}' not supported. Supported providers: {SUPPORTED_PROVIDERS}",
                "details": {"provided_provider": scan_request.provider}
            }
        )
    
    # 2. Validation des services
    supported_services = SUPPORTED_SERVICES_AWS.get(scan_request.provider, [])
    invalid_services = [service for service in scan_request.services if service not in supported_services]
    
    if invalid_services:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_SERVICES",
                "message": f"Services {invalid_services} not supported for provider '{scan_request.provider}'. Supported services: {supported_services}",
                "details": {
                    "invalid_services": invalid_services,
                    "supported_services": supported_services
                }
            }
        )
    
    # 3. Validation du mode d'authentification
    supported_auth_modes = SUPPORTED_AUTH_MODES.get(scan_request.provider, [])
    if scan_request.auth_mode.type not in supported_auth_modes:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_AUTH_MODE",
                "message": f"Auth mode '{scan_request.auth_mode.type}' not supported for provider '{scan_request.provider}'. Supported modes: {supported_auth_modes}",
                "details": {
                    "provided_auth_mode": scan_request.auth_mode.type,
                    "supported_auth_modes": supported_auth_modes
                }
            }
        )
    
    # 4. Génération du scan_id
    scan_id = f"scan-{str(uuid.uuid4())}"
    
    # 5. Lancement du moteur en arrière-plan avec user_id
    background_tasks.add_task(
        scan_list_service,
        scan_id=scan_id,
        provider=scan_request.provider,
        services=scan_request.services,
        auth_mode=scan_request.auth_mode.dict(),
        client_id=scan_request.client_id,
        regions=scan_request.regions,
        user_id=current_user.id  # ✅ AJOUT DU USER_ID
    )
    
    # 6. Réponse immédiate
    return ScanResponse(
        scan_id=scan_id,
        status="QUEUED",
        message=f"Scan for provider '{scan_request.provider}' and services {scan_request.services} has been queued."
    )


@router.get("/scans/status")
async def get_scan_status(
    services: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Vérifie si tous les services demandés ont terminé leur scan.

    Args:
        services: Liste des services séparés par des virgules (ex: "ec2,s3")

    Returns:
        {
            "completed": true/false,
            "services_status": {
                "ec2": {"completed": true, "total_resources": 10},
                "s3": {"completed": false, "total_resources": 0}
            }
        }
    """
    from api.database import ScanRun
    from datetime import datetime, timedelta

    try:
        services_list = services.split(',')

        # Vérifier les scans des 2 dernières minutes pour chaque service
        time_threshold = datetime.now() - timedelta(minutes=2)

        services_status = {}
        all_completed = True

        for service in services_list:
            # Chercher le dernier scan de ce service
            latest_scan = db.query(ScanRun).filter(
                ScanRun.service_type == service,
                ScanRun.user_id == current_user.id,
                ScanRun.scan_timestamp >= time_threshold
            ).order_by(ScanRun.scan_timestamp.desc()).first()

            if latest_scan and latest_scan.status in ['success', 'partial', 'failed']:
                # Scan terminé (succès, partiel ou échec)
                services_status[service] = {
                    "completed": True,
                    "total_resources": latest_scan.total_resources,
                    "status": latest_scan.status,
                    "scan_id": latest_scan.id
                }
            else:
                # Pas de scan ou scan en cours
                services_status[service] = {
                    "completed": False,
                    "total_resources": latest_scan.total_resources if latest_scan else 0,
                    "status": latest_scan.status if latest_scan else "pending"
                }
                all_completed = False

        return {
            "completed": all_completed,
            "services_status": services_status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la vérification du statut: {str(e)}")


@router.get("/scans/{scan_session_id}/export")
async def export_scan_session(
    scan_session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exporte tous les détails d'une session de scan au format JSON.

    Retourne toutes les ressources scannées (EC2, S3) pour une session donnée.
    ⚠️ ISOLATION : Seules les scans de l'utilisateur connecté sont accessibles.

    Args:
        scan_session_id: ID du scan de référence (scan_id du premier scan du groupe)
    """
    from api.database import ScanRun, EC2Instance, S3Bucket
    from sqlalchemy.orm import joinedload
    from datetime import datetime, timedelta, timezone

    # Récupérer le scan de référence
    reference_scan = db.query(ScanRun).filter(
        ScanRun.id == int(scan_session_id),
        ScanRun.user_id == current_user.id  # ✅ Isolation par user
    ).first()

    if not reference_scan:
        raise HTTPException(
            status_code=404,
            detail=f"Scan '{scan_session_id}' not found or access denied"
        )

    # Récupérer tous les scans dans la même fenêtre de temps (±30 secondes)
    session_start = reference_scan.scan_timestamp - timedelta(seconds=30)
    session_end = reference_scan.scan_timestamp + timedelta(seconds=30)

    scan_runs = db.query(ScanRun).filter(
        ScanRun.user_id == current_user.id,
        ScanRun.scan_timestamp >= session_start,
        ScanRun.scan_timestamp <= session_end
    ).order_by(ScanRun.scan_timestamp.desc()).all()

    if not scan_runs:
        raise HTTPException(
            status_code=404,
            detail=f"No scans found in session"
        )

    # Préparer les données d'export
    export_data = {
        "export_info": {
            "scan_session_id": scan_session_id,
            "export_date": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user.id,
            "user_email": current_user.email,
            "user_name": current_user.full_name,
            "total_scans": len(scan_runs)
        },
        "scans": [],
        "resources": {
            "ec2_instances": [],
            "s3_buckets": [],
        },
        "summary": {
            "total_resources": 0,
            "by_service": {},
            "by_region": {}
        }
    }

    # Parcourir chaque scan de la session
    for scan_run in scan_runs:
        scan_info = {
            "scan_run_id": scan_run.id,
            "service_type": scan_run.service_type,
            "scan_timestamp": scan_run.scan_timestamp.isoformat() if scan_run.scan_timestamp else None,
            "status": scan_run.status,
            "total_resources": scan_run.total_resources or 0
        }
        export_data["scans"].append(scan_info)

        # Récupérer les ressources selon le type de service
        if scan_run.service_type == "ec2":
            instances = db.query(EC2Instance).filter(
                EC2Instance.scan_run_id == scan_run.id
            ).all()

            for instance in instances:
                # Convertir les métriques de performance en dict
                perf_data = None
                if instance.performance:
                    perf_data = {
                        "cpu_utilization_avg": instance.performance.cpu_utilization_avg,
                        "memory_utilization_avg": instance.performance.memory_utilization_avg,
                        "network_in_bytes": instance.performance.network_in_bytes,
                        "network_out_bytes": instance.performance.network_out_bytes
                    }

                export_data["resources"]["ec2_instances"].append({
                    "resource_id": instance.resource_id,
                    "instance_id": instance.instance_id,
                    "client_id": instance.client_id,
                    "instance_type": instance.instance_type,
                    "state": instance.state,
                    "region": instance.region,
                    "availability_zone": instance.availability_zone,
                    "public_ip": instance.public_ip,
                    "private_ip": instance.private_ip,
                    "vpc_id": instance.vpc_id,
                    "subnet_id": instance.subnet_id,
                    "ami_id": instance.ami_id,
                    "tenancy": instance.tenancy,
                    "architecture": instance.architecture,
                    "virtualization_type": instance.virtualization_type,
                    "iam_profile": instance.iam_profile,
                    "root_device_name": instance.root_device_name,
                    "tags": instance.tags,
                    "launch_time": instance.launch_time.isoformat() if instance.launch_time else None,
                    "ebs_volumes": instance.ebs_volumes,
                    "performance": perf_data,
                    "scan_timestamp": instance.scan_timestamp.isoformat() if instance.scan_timestamp else None
                })

        elif scan_run.service_type == "s3":
            buckets = db.query(S3Bucket).filter(
                S3Bucket.scan_run_id == scan_run.id
            ).all()

            for bucket in buckets:
                # Convertir les métriques de performance en dict
                perf_data = None
                if bucket.performance:
                    perf_data = {
                        "all_requests": bucket.performance.all_requests,
                        "get_requests": bucket.performance.get_requests,
                        "put_requests": bucket.performance.put_requests,
                        "delete_requests": bucket.performance.delete_requests,
                        "errors_4xx": bucket.performance.errors_4xx,
                        "errors_5xx": bucket.performance.errors_5xx,
                        "first_byte_latency_avg": bucket.performance.first_byte_latency_avg,
                        "total_request_latency_avg": bucket.performance.total_request_latency_avg,
                        "bytes_downloaded": bucket.performance.bytes_downloaded,
                        "bytes_uploaded": bucket.performance.bytes_uploaded
                    }

                export_data["resources"]["s3_buckets"].append({
                    "resource_id": bucket.resource_id,
                    "bucket_name": bucket.bucket_name,
                    "client_id": bucket.client_id,
                    "region": bucket.region,
                    "creation_date": bucket.creation_date.isoformat() if bucket.creation_date else None,
                    "versioning_enabled": bucket.versioning_enabled,
                    "encryption_enabled": bucket.encryption_enabled,
                    "public_access_blocked": bucket.public_access_blocked,
                    "public_read_enabled": bucket.public_read_enabled,
                    "bucket_policy_enabled": bucket.bucket_policy_enabled,
                    "lifecycle_enabled": bucket.lifecycle_enabled,
                    "cors_enabled": bucket.cors_enabled,
                    "website_enabled": bucket.website_enabled,
                    "logging_enabled": bucket.logging_enabled,
                    "notifications_enabled": bucket.notifications_enabled,
                    "replication_enabled": bucket.replication_enabled,
                    "performance": perf_data,
                    "scan_timestamp": bucket.scan_timestamp.isoformat() if bucket.scan_timestamp else None
                })

    # Calculer le résumé
    export_data["summary"]["total_resources"] = (
        len(export_data["resources"]["ec2_instances"]) +
        len(export_data["resources"]["s3_buckets"])
    )

    export_data["summary"]["by_service"] = {
        "ec2": len(export_data["resources"]["ec2_instances"]),
        "s3": len(export_data["resources"]["s3_buckets"]),
    }

    regions = {}
    for instance in export_data["resources"]["ec2_instances"]:
        region = instance.get("region", "unknown")
        regions[region] = regions.get(region, 0) + 1
    for bucket in export_data["resources"]["s3_buckets"]:
        region = bucket.get("region", "unknown")
        regions[region] = regions.get(region, 0) + 1

    export_data["summary"]["by_region"] = regions

    return export_data


# ── Tarifs EC2 approximatifs ($/heure) ──────────────────────────────────────
EC2_HOURLY_PRICES = {
    "t2.micro": 0.0116, "t2.small": 0.023, "t2.medium": 0.0464,
    "t2.large": 0.0928, "t2.xlarge": 0.1856, "t2.2xlarge": 0.3712,
    "t3.micro": 0.0104, "t3.small": 0.0208, "t3.medium": 0.0416,
    "t3.large": 0.0832, "t3.xlarge": 0.1664, "t3.2xlarge": 0.3328,
    "m5.large": 0.096, "m5.xlarge": 0.192, "m5.2xlarge": 0.384,
    "m5.4xlarge": 0.768, "m5.8xlarge": 1.536,
    "c5.large": 0.085, "c5.xlarge": 0.17, "c5.2xlarge": 0.34,
    "r5.large": 0.126, "r5.xlarge": 0.252, "r5.2xlarge": 0.504,
}
S3_PRICE_PER_GB = 0.023


def _generate_ec2_findings(instance: dict) -> list:
    findings = []
    if instance.get("state") == "stopped":
        findings.append({
            "pillar": "Cost",
            "severity": "HIGH",
            "rule": "EC2_STOPPED_INSTANCE",
            "message": f"Instance {instance.get('instance_id')} is stopped but still incurring EBS costs.",
            "recommendation": "Terminate or snapshot the instance if no longer needed."
        })
    if not instance.get("iam_profile"):
        findings.append({
            "pillar": "Compliance",
            "severity": "MEDIUM",
            "rule": "EC2_NO_IAM_PROFILE",
            "message": f"Instance {instance.get('instance_id')} has no IAM instance profile attached.",
            "recommendation": "Attach an IAM role to avoid hardcoded credentials."
        })
    if not instance.get("tags"):
        findings.append({
            "pillar": "Best Practices",
            "severity": "LOW",
            "rule": "EC2_NO_TAGS",
            "message": f"Instance {instance.get('instance_id')} has no tags.",
            "recommendation": "Add Name, Environment and Owner tags for cost allocation."
        })
    perf = instance.get("performance") or {}
    cpu = perf.get("cpu_utilization_avg")
    if cpu is not None and cpu < 5:
        findings.append({
            "pillar": "Cost",
            "severity": "MEDIUM",
            "rule": "EC2_LOW_CPU_UTILIZATION",
            "message": f"Instance {instance.get('instance_id')} has average CPU utilization of {cpu:.1f}%.",
            "recommendation": "Consider downsizing or terminating this underutilized instance."
        })
    return findings


def _generate_s3_findings(bucket: dict) -> list:
    findings = []
    if not bucket.get("encryption_enabled"):
        findings.append({
            "pillar": "Compliance",
            "severity": "HIGH",
            "rule": "S3_NO_ENCRYPTION",
            "message": f"Bucket {bucket.get('bucket_name')} does not have server-side encryption enabled.",
            "recommendation": "Enable AES-256 or AWS KMS encryption."
        })
    if not bucket.get("public_access_blocked"):
        findings.append({
            "pillar": "Compliance",
            "severity": "CRITICAL",
            "rule": "S3_PUBLIC_ACCESS_NOT_BLOCKED",
            "message": f"Bucket {bucket.get('bucket_name')} does not block public access.",
            "recommendation": "Enable Block Public Access settings immediately."
        })
    if bucket.get("public_read_enabled"):
        findings.append({
            "pillar": "Compliance",
            "severity": "CRITICAL",
            "rule": "S3_PUBLIC_READ_ENABLED",
            "message": f"Bucket {bucket.get('bucket_name')} allows public read access via ACL.",
            "recommendation": "Remove AllUsers read grant from the bucket ACL."
        })
    if not bucket.get("versioning_enabled"):
        findings.append({
            "pillar": "Best Practices",
            "severity": "MEDIUM",
            "rule": "S3_NO_VERSIONING",
            "message": f"Bucket {bucket.get('bucket_name')} does not have versioning enabled.",
            "recommendation": "Enable versioning to protect against accidental deletions."
        })
    if not bucket.get("lifecycle_enabled"):
        findings.append({
            "pillar": "Cost",
            "severity": "MEDIUM",
            "rule": "S3_NO_LIFECYCLE",
            "message": f"Bucket {bucket.get('bucket_name')} has no lifecycle policy.",
            "recommendation": "Add lifecycle rules to transition or expire old objects."
        })
    if not bucket.get("logging_enabled"):
        findings.append({
            "pillar": "Best Practices",
            "severity": "LOW",
            "rule": "S3_NO_LOGGING",
            "message": f"Bucket {bucket.get('bucket_name')} does not have access logging enabled.",
            "recommendation": "Enable server access logging for audit purposes."
        })
    return findings


@router.get("/scans/{scan_session_id}/export/2cbp")
async def export_scan_2cbp(
    scan_session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exporte une session de scan au format 2CBP (Cost / Compliance / Best Practices).
    Inclut resources, metrics, costs estimés et findings par pilier.
    """
    from api.database import ScanRun, EC2Instance, S3Bucket
    from datetime import datetime, timedelta, timezone

    reference_scan = db.query(ScanRun).filter(
        ScanRun.id == int(scan_session_id),
        ScanRun.user_id == current_user.id
    ).first()

    if not reference_scan:
        raise HTTPException(
            status_code=404,
            detail=f"Scan '{scan_session_id}' not found or access denied"
        )

    session_start = reference_scan.scan_timestamp - timedelta(seconds=30)
    session_end   = reference_scan.scan_timestamp + timedelta(seconds=30)

    scan_runs = db.query(ScanRun).filter(
        ScanRun.user_id == current_user.id,
        ScanRun.scan_timestamp >= session_start,
        ScanRun.scan_timestamp <= session_end
    ).order_by(ScanRun.scan_timestamp.desc()).all()

    resources = {"ec2_instances": [], "s3_buckets": []}
    metrics   = {"ec2": [], "s3": []}
    findings  = []
    regions_set = set()

    ec2_cost_total = 0.0
    s3_cost_total  = 0.0

    for scan_run in scan_runs:
        if scan_run.service_type == "ec2":
            instances = db.query(EC2Instance).filter(
                EC2Instance.scan_run_id == scan_run.id
            ).all()
            for inst in instances:
                if inst.region:
                    regions_set.add(inst.region)
                perf = None
                if inst.performance:
                    perf = {
                        "cpu_utilization_avg": inst.performance.cpu_utilization_avg,
                        "memory_utilization_avg": inst.performance.memory_utilization_avg,
                        "network_in_bytes": inst.performance.network_in_bytes,
                        "network_out_bytes": inst.performance.network_out_bytes,
                    }
                    metrics["ec2"].append({
                        "resource_id": inst.resource_id,
                        "instance_id": inst.instance_id,
                        **perf
                    })

                inst_dict = {
                    "resource_id": inst.resource_id,
                    "instance_id": inst.instance_id,
                    "instance_type": inst.instance_type,
                    "state": inst.state,
                    "region": inst.region,
                    "availability_zone": inst.availability_zone,
                    "iam_profile": inst.iam_profile,
                    "tags": inst.tags,
                    "launch_time": inst.launch_time.isoformat() if inst.launch_time else None,
                    "performance": perf,
                }
                resources["ec2_instances"].append(inst_dict)

                hourly = EC2_HOURLY_PRICES.get(inst.instance_type or "", 0.05)
                monthly = hourly * 24 * 30
                ec2_cost_total += monthly

                inst_findings = _generate_ec2_findings(inst_dict)
                findings.extend(inst_findings)

        elif scan_run.service_type == "s3":
            buckets = db.query(S3Bucket).filter(
                S3Bucket.scan_run_id == scan_run.id
            ).all()
            for bkt in buckets:
                if bkt.region:
                    regions_set.add(bkt.region)
                perf = None
                if bkt.performance:
                    perf = {
                        "all_requests": bkt.performance.all_requests,
                        "get_requests": bkt.performance.get_requests,
                        "put_requests": bkt.performance.put_requests,
                        "bytes_downloaded": bkt.performance.bytes_downloaded,
                        "bytes_uploaded": bkt.performance.bytes_uploaded,
                        "errors_4xx": bkt.performance.errors_4xx,
                        "errors_5xx": bkt.performance.errors_5xx,
                    }
                    metrics["s3"].append({
                        "bucket_name": bkt.bucket_name,
                        **perf
                    })

                bkt_dict = {
                    "bucket_name": bkt.bucket_name,
                    "region": bkt.region,
                    "encryption_enabled": bkt.encryption_enabled,
                    "public_access_blocked": bkt.public_access_blocked,
                    "public_read_enabled": bkt.public_read_enabled,
                    "versioning_enabled": bkt.versioning_enabled,
                    "lifecycle_enabled": bkt.lifecycle_enabled,
                    "logging_enabled": bkt.logging_enabled,
                    "cors_enabled": bkt.cors_enabled,
                    "replication_enabled": bkt.replication_enabled,
                    "performance": perf,
                }
                resources["s3_buckets"].append(bkt_dict)

                s3_cost_total += S3_PRICE_PER_GB * 5
                bkt_findings = _generate_s3_findings(bkt_dict)
                findings.extend(bkt_findings)

    findings_by_pillar = {"Cost": 0, "Compliance": 0, "Best Practices": 0}
    for f in findings:
        pillar = f.get("pillar", "")
        if pillar in findings_by_pillar:
            findings_by_pillar[pillar] += 1

    return {
        "client_id": reference_scan.client_id,
        "scan_id": scan_session_id,
        "timestamp": reference_scan.scan_timestamp.isoformat(),
        "provider": "aws",
        "account_id": current_user.email,
        "regions": list(regions_set),
        "resources": resources,
        "metrics": metrics,
        "costs": {
            "currency": "USD",
            "estimated": True,
            "note": "Monthly cost estimates based on public AWS pricing",
            "by_service": {
                "ec2": round(ec2_cost_total, 2),
                "s3": round(s3_cost_total, 2),
            },
            "total": round(ec2_cost_total + s3_cost_total, 2),
        },
        "findings": findings,
        "summary": {
            "total_resources": len(resources["ec2_instances"]) + len(resources["s3_buckets"]),
            "total_findings": len(findings),
            "findings_by_pillar": findings_by_pillar,
            "findings_by_severity": {
                s: sum(1 for f in findings if f.get("severity") == s)
                for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            }
        }
    }

