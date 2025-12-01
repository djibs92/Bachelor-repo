
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
                "services": ["ec2", "s3", "vpc"],
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
        services: Liste des services séparés par des virgules (ex: "ec2,s3,vpc,rds")

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

    Retourne toutes les ressources scannées (EC2, S3, VPC, RDS) pour une session donnée.
    ⚠️ ISOLATION : Seules les scans de l'utilisateur connecté sont accessibles.

    Args:
        scan_session_id: ID du scan de référence (scan_id du premier scan du groupe)
    """
    from api.database import ScanRun, EC2Instance, S3Bucket, VPCInstance, RDSInstance
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
            "vpc_instances": [],
            "rds_instances": []
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

        elif scan_run.service_type == "vpc":
            vpcs = db.query(VPCInstance).filter(
                VPCInstance.scan_run_id == scan_run.id
            ).all()

            for vpc in vpcs:
                # Convertir les métriques de performance en dict
                perf_data = None
                if vpc.performance:
                    perf_data = {
                        "network_in_bytes": vpc.performance.network_in_bytes,
                        "network_out_bytes": vpc.performance.network_out_bytes,
                        "network_packets_in": vpc.performance.network_packets_in,
                        "network_packets_out": vpc.performance.network_packets_out,
                        "nat_gateway_bytes_in": vpc.performance.nat_gateway_bytes_in,
                        "nat_gateway_bytes_out": vpc.performance.nat_gateway_bytes_out
                    }

                export_data["resources"]["vpc_instances"].append({
                    "client_id": vpc.client_id,
                    "vpc_id": vpc.vpc_id,
                    "cidr_block": vpc.cidr_block,
                    "state": vpc.state,
                    "region": vpc.region,
                    "is_default": vpc.is_default,
                    "tenancy": vpc.tenancy,
                    "subnet_count": vpc.subnet_count,
                    "public_subnets_count": vpc.public_subnets_count,
                    "private_subnets_count": vpc.private_subnets_count,
                    "availability_zones": vpc.availability_zones,
                    "internet_gateway_attached": vpc.internet_gateway_attached,
                    "nat_gateways_count": vpc.nat_gateways_count,
                    "route_tables_count": vpc.route_tables_count,
                    "security_groups_count": vpc.security_groups_count,
                    "network_acls_count": vpc.network_acls_count,
                    "flow_logs_enabled": vpc.flow_logs_enabled,
                    "vpc_endpoints_count": vpc.vpc_endpoints_count,
                    "vpc_peering_connections_count": vpc.vpc_peering_connections_count,
                    "transit_gateway_attachments_count": vpc.transit_gateway_attachments_count,
                    "tags": vpc.tags,
                    "performance": perf_data,
                    "scan_timestamp": vpc.scan_timestamp.isoformat() if vpc.scan_timestamp else None
                })

        elif scan_run.service_type == "rds":
            databases = db.query(RDSInstance).filter(
                RDSInstance.scan_run_id == scan_run.id
            ).all()

            for db_instance in databases:
                # Convertir les métriques de performance en dict
                perf_data = None
                if db_instance.performance:
                    perf_data = {
                        "cpu_utilization_avg": db_instance.performance.cpu_utilization_avg,
                        "freeable_memory_bytes": db_instance.performance.freeable_memory_bytes,
                        "free_storage_space_bytes": db_instance.performance.free_storage_space_bytes,
                        "database_connections": db_instance.performance.database_connections,
                        "read_iops_avg": db_instance.performance.read_iops_avg,
                        "write_iops_avg": db_instance.performance.write_iops_avg,
                        "read_latency_avg": db_instance.performance.read_latency_avg,
                        "write_latency_avg": db_instance.performance.write_latency_avg,
                        "read_throughput_bytes": db_instance.performance.read_throughput_bytes,
                        "write_throughput_bytes": db_instance.performance.write_throughput_bytes,
                        "network_receive_throughput_bytes": db_instance.performance.network_receive_throughput_bytes,
                        "network_transmit_throughput_bytes": db_instance.performance.network_transmit_throughput_bytes
                    }

                export_data["resources"]["rds_instances"].append({
                    "resource_id": db_instance.resource_id,
                    "db_instance_identifier": db_instance.db_instance_identifier,
                    "client_id": db_instance.client_id,
                    "db_instance_class": db_instance.db_instance_class,
                    "engine": db_instance.engine,
                    "engine_version": db_instance.engine_version,
                    "db_instance_status": db_instance.db_instance_status,
                    "region": db_instance.region,
                    "availability_zone": db_instance.availability_zone,
                    "multi_az": db_instance.multi_az,
                    "endpoint_address": db_instance.endpoint_address,
                    "endpoint_port": db_instance.endpoint_port,
                    "allocated_storage": db_instance.allocated_storage,
                    "storage_type": db_instance.storage_type,
                    "storage_encrypted": db_instance.storage_encrypted,
                    "iops": db_instance.iops,
                    "vpc_id": db_instance.vpc_id,
                    "db_subnet_group_name": db_instance.db_subnet_group_name,
                    "publicly_accessible": db_instance.publicly_accessible,
                    "master_username": db_instance.master_username,
                    "iam_database_authentication_enabled": db_instance.iam_database_authentication_enabled,
                    "deletion_protection": db_instance.deletion_protection,
                    "backup_retention_period": db_instance.backup_retention_period,
                    "preferred_backup_window": db_instance.preferred_backup_window,
                    "preferred_maintenance_window": db_instance.preferred_maintenance_window,
                    "latest_restorable_time": db_instance.latest_restorable_time.isoformat() if db_instance.latest_restorable_time else None,
                    "auto_minor_version_upgrade": db_instance.auto_minor_version_upgrade,
                    "enhanced_monitoring_resource_arn": db_instance.enhanced_monitoring_resource_arn,
                    "monitoring_interval": db_instance.monitoring_interval,
                    "performance_insights_enabled": db_instance.performance_insights_enabled,
                    "tags": db_instance.tags,
                    "security_groups": db_instance.security_groups,
                    "parameter_groups": db_instance.parameter_groups,
                    "option_groups": db_instance.option_groups,
                    "performance": perf_data,
                    "instance_create_time": db_instance.instance_create_time.isoformat() if db_instance.instance_create_time else None,
                    "scan_timestamp": db_instance.scan_timestamp.isoformat() if db_instance.scan_timestamp else None
                })

    # Calculer le résumé
    export_data["summary"]["total_resources"] = (
        len(export_data["resources"]["ec2_instances"]) +
        len(export_data["resources"]["s3_buckets"]) +
        len(export_data["resources"]["vpc_instances"]) +
        len(export_data["resources"]["rds_instances"])
    )

    export_data["summary"]["by_service"] = {
        "ec2": len(export_data["resources"]["ec2_instances"]),
        "s3": len(export_data["resources"]["s3_buckets"]),
        "vpc": len(export_data["resources"]["vpc_instances"]),
        "rds": len(export_data["resources"]["rds_instances"])
    }

    # Compter par région (en parcourant les ressources)
    regions = {}

    # Compter les régions depuis les instances EC2
    for instance in export_data["resources"]["ec2_instances"]:
        region = instance.get("region", "unknown")
        regions[region] = regions.get(region, 0) + 1

    # Compter les régions depuis les buckets S3
    for bucket in export_data["resources"]["s3_buckets"]:
        region = bucket.get("region", "unknown")
        regions[region] = regions.get(region, 0) + 1

    # Compter les régions depuis les VPCs
    for vpc in export_data["resources"]["vpc_instances"]:
        region = vpc.get("region", "unknown")
        regions[region] = regions.get(region, 0) + 1

    # Compter les régions depuis les instances RDS
    for rds in export_data["resources"]["rds_instances"]:
        region = rds.get("region", "unknown")
        regions[region] = regions.get(region, 0) + 1

    export_data["summary"]["by_region"] = regions

    return export_data

