from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from api.database import get_db, ScanRun, EC2Instance, EC2Performance, S3Bucket, S3Performance, VPCInstance, VPCPerformance, RDSInstance, RDSPerformance, User
from api.endpoints.auth import get_current_user

router = APIRouter()

# ========================================
# ENDPOINTS DE RÉCUPÉRATION (Base de données)
# ========================================

@router.get("/scans/latest-session")
async def get_latest_scan_session(
    scan_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère la dernière SESSION de scan (tous les services scannés en même temps).

    Une session de scan = tous les scans lancés dans une fenêtre de 30 secondes.
    Cela permet d'afficher uniquement les services réellement scannés lors du dernier scan.

    Si vous scannez seulement EC2, seul EC2 sera affiché (S3=0, VPC=0).
    Si vous scannez EC2+S3 ensemble, les deux seront affichés.

    Args:
        scan_id: Si fourni, récupère la session contenant ce scan spécifique

    Returns:
        {
            "session_timestamp": "2024-01-15T10:30:00",
            "services": ["ec2", "s3"],  # Services scannés dans cette session
            "scans": [...]  # Détails de chaque scan
        }
    """
    try:
        # Récupérer le scan de référence
        if scan_id:
            # Récupérer le scan spécifique
            reference_scan = db.query(ScanRun).filter(
                ScanRun.id == scan_id,
                ScanRun.user_id == current_user.id
            ).first()

            if not reference_scan:
                return {
                    "session_timestamp": None,
                    "services": [],
                    "scans": []
                }
        else:
            # Récupérer le dernier scan (peu importe le service)
            reference_scan = db.query(ScanRun).filter(
                ScanRun.user_id == current_user.id
            ).order_by(ScanRun.scan_timestamp.desc()).first()

            if not reference_scan:
                return {
                    "session_timestamp": None,
                    "services": [],
                    "scans": []
                }

        # Fenêtre de temps : uniquement les scans lancés dans la même session utilisateur
        # On prend uniquement les scans dans les 30 secondes AVANT et APRÈS le scan de référence
        # Cela permet de grouper les scans multi-services lancés ensemble
        from datetime import timedelta
        session_window = timedelta(seconds=30)  # 30 secondes pour capturer tous les scans multi-services
        session_start = reference_scan.scan_timestamp - session_window
        session_end = reference_scan.scan_timestamp + session_window

        # Récupérer tous les scans terminés dans cette fenêtre étroite
        session_scans = db.query(ScanRun).filter(
            ScanRun.user_id == current_user.id,
            ScanRun.scan_timestamp >= session_start,
            ScanRun.scan_timestamp <= session_end,
            ScanRun.status.in_(['success', 'partial', 'failed'])  # ✅ Uniquement les scans terminés
        ).order_by(ScanRun.scan_timestamp.desc()).all()

        # Extraire les services uniques
        services = list(set([scan.service_type for scan in session_scans]))

        # Formater la réponse
        scans_details = []
        for scan in session_scans:
            scans_details.append({
                "scan_id": scan.id,
                "service_type": scan.service_type,
                "scan_timestamp": scan.scan_timestamp.isoformat() if scan.scan_timestamp else None,
                "total_resources": scan.total_resources,
                "status": scan.status
            })

        return {
            "session_timestamp": reference_scan.scan_timestamp.isoformat() if reference_scan.scan_timestamp else None,
            "services": services,
            "scans": scans_details
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de la session: {str(e)}")


@router.get("/scans/history")
async def get_scans_history(
    client_id: Optional[str] = None,
    service_type: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique des scans depuis la base de données.

    ⚠️ ISOLATION DES COMPTES : Seuls les scans de l'utilisateur connecté sont retournés.

    Args:
        client_id: Filtrer par client (optionnel)
        service_type: Filtrer par type de service (ec2, s3, vpc) (optionnel)
        limit: Nombre maximum de scans à retourner (défaut: 10)
        current_user: Utilisateur connecté (injecté automatiquement)

    Returns:
        Liste des scans avec leurs métadonnées
    """
    try:
        # Construire la requête - FILTRER PAR USER_ID
        query = db.query(ScanRun).filter(ScanRun.user_id == current_user.id)

        if client_id:
            query = query.filter(ScanRun.client_id == client_id)

        if service_type:
            query = query.filter(ScanRun.service_type == service_type)

        # Trier par date décroissante et limiter
        scans = query.order_by(ScanRun.scan_timestamp.desc()).limit(limit).all()

        # Formater la réponse
        result = []
        for scan in scans:
            result.append({
                "scan_id": scan.id,
                "client_id": scan.client_id,
                "service_type": scan.service_type,
                "scan_timestamp": scan.scan_timestamp.isoformat() if scan.scan_timestamp else None,
                "total_resources": scan.total_resources,
                "status": scan.status
            })

        return {
            "total_scans": len(result),
            "scans": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des scans: {str(e)}")


@router.get("/ec2/instances")
async def get_ec2_instances(
    client_id: Optional[str] = None,
    region: Optional[str] = None,
    state: Optional[str] = None,
    latest_only: bool = True,
    scan_id: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les instances EC2 depuis la base de données.

    ⚠️ ISOLATION DES COMPTES : Seules les instances de l'utilisateur connecté sont retournées.

    Args:
        client_id: Filtrer par client (optionnel)
        region: Filtrer par région (optionnel)
        state: Filtrer par état (running, stopped, etc.) (optionnel)
        latest_only: Si True, récupère uniquement les instances du dernier scan (défaut: True)
        limit: Nombre maximum d'instances à retourner (défaut: 50)
        current_user: Utilisateur connecté (injecté automatiquement)

    Returns:
        Liste des instances EC2 avec leurs performances
    """
    try:
        if scan_id:
            # Récupérer un scan spécifique par son ID
            specific_scan = db.query(ScanRun).filter(
                ScanRun.id == scan_id,
                ScanRun.service_type == 'ec2',
                ScanRun.user_id == current_user.id
            ).first()

            if not specific_scan:
                return {
                    "total_instances": 0,
                    "instances": [],
                    "scan_id": None,
                    "scan_timestamp": None
                }

            # Construire la requête pour ce scan spécifique
            query = db.query(EC2Instance).filter(EC2Instance.scan_run_id == specific_scan.id)
            latest_scan = specific_scan
        elif latest_only:
            # Récupérer le dernier scan EC2 DE L'UTILISATEUR CONNECTÉ
            latest_scan = db.query(ScanRun).filter(
                ScanRun.service_type == 'ec2',
                ScanRun.user_id == current_user.id
            ).order_by(ScanRun.scan_timestamp.desc()).first()

            if not latest_scan:
                return {
                    "total_instances": 0,
                    "instances": [],
                    "scan_id": None,
                    "scan_timestamp": None
                }

            # Construire la requête pour le dernier scan EC2 uniquement
            query = db.query(EC2Instance).filter(EC2Instance.scan_run_id == latest_scan.id)
        else:
            # Mode historique : récupérer toutes les instances
            query = db.query(EC2Instance)
            latest_scan = None

        if client_id:
            query = query.filter(EC2Instance.client_id == client_id)

        if region:
            query = query.filter(EC2Instance.region == region)

        if state:
            query = query.filter(EC2Instance.state == state)

        # Trier par date de scan décroissante et limiter
        instances = query.order_by(EC2Instance.scan_timestamp.desc()).limit(limit).all()

        # Formater la réponse
        result = []
        for instance in instances:
            instance_data = {
                "instance_id": instance.instance_id,
                "instance_type": instance.instance_type,
                "state": instance.state,
                "region": instance.region,
                "availability_zone": instance.availability_zone,
                "vpc_id": instance.vpc_id,
                "subnet_id": instance.subnet_id,
                "private_ip": instance.private_ip,
                "public_ip": instance.public_ip,
                "ami_id": instance.ami_id,
                "launch_time": instance.launch_time.isoformat() if instance.launch_time else None,
                "scan_timestamp": instance.scan_timestamp.isoformat() if instance.scan_timestamp else None,
                "tags": instance.tags,
                "ebs_volumes": instance.ebs_volumes
            }

            # Ajouter les performances si disponibles
            if instance.performance:
                instance_data["performance"] = {
                    "cpu_utilization_avg": instance.performance.cpu_utilization_avg,
                    "memory_utilization_avg": instance.performance.memory_utilization_avg,
                    "network_in_bytes": instance.performance.network_in_bytes,
                    "network_out_bytes": instance.performance.network_out_bytes
                }

            result.append(instance_data)

        return {
            "total_instances": len(result),
            "instances": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des instances EC2: {str(e)}")


@router.get("/ec2/instances/{instance_id}")
async def get_ec2_instance_by_id(
    instance_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique d'une instance EC2 spécifique.

    Args:
        instance_id: ID de l'instance EC2

    Returns:
        Historique complet de l'instance avec toutes ses métriques
    """
    try:
        # Récupérer toutes les entrées pour cette instance (historique)
        instances = db.query(EC2Instance).filter(
            EC2Instance.instance_id == instance_id
        ).order_by(EC2Instance.scan_timestamp.desc()).all()

        if not instances:
            raise HTTPException(status_code=404, detail=f"Instance {instance_id} non trouvée")

        # Formater la réponse
        result = []
        for instance in instances:
            instance_data = {
                "instance_id": instance.instance_id,
                "instance_type": instance.instance_type,
                "state": instance.state,
                "region": instance.region,
                "scan_timestamp": instance.scan_timestamp.isoformat() if instance.scan_timestamp else None,
            }

            if instance.performance:
                instance_data["performance"] = {
                    "cpu_utilization_avg": instance.performance.cpu_utilization_avg,
                    "memory_utilization_avg": instance.performance.memory_utilization_avg,
                    "network_in_bytes": instance.performance.network_in_bytes,
                    "network_out_bytes": instance.performance.network_out_bytes
                }

            result.append(instance_data)

        return {
            "instance_id": instance_id,
            "total_scans": len(result),
            "history": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'instance: {str(e)}")


@router.get("/s3/buckets")
async def get_s3_buckets(
    client_id: Optional[str] = None,
    region: Optional[str] = None,
    latest_only: bool = True,
    scan_id: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les buckets S3 depuis la base de données.

    ⚠️ ISOLATION DES COMPTES : Seuls les buckets de l'utilisateur connecté sont retournés.

    Args:
        client_id: Filtrer par client (optionnel)
        region: Filtrer par région (optionnel)
        latest_only: Si True, récupère uniquement les buckets du dernier scan (défaut: True)
        limit: Nombre maximum de buckets à retourner (défaut: 50)
        current_user: Utilisateur connecté (injecté automatiquement)

    Returns:
        Liste des buckets S3 avec leurs performances
    """
    try:
        if scan_id:
            # Récupérer un scan spécifique par son ID
            specific_scan = db.query(ScanRun).filter(
                ScanRun.id == scan_id,
                ScanRun.service_type == 's3',
                ScanRun.user_id == current_user.id
            ).first()

            if not specific_scan:
                return {
                    "total_buckets": 0,
                    "buckets": [],
                    "scan_id": None,
                    "scan_timestamp": None
                }

            # Construire la requête pour ce scan spécifique
            query = db.query(S3Bucket).filter(S3Bucket.scan_run_id == specific_scan.id)
            latest_scan = specific_scan
        elif latest_only:
            # Récupérer le dernier scan S3 DE L'UTILISATEUR CONNECTÉ
            latest_scan = db.query(ScanRun).filter(
                ScanRun.service_type == 's3',
                ScanRun.user_id == current_user.id
            ).order_by(ScanRun.scan_timestamp.desc()).first()

            if not latest_scan:
                return {
                    "total_buckets": 0,
                    "buckets": [],
                    "scan_id": None,
                    "scan_timestamp": None
                }

            # Construire la requête pour le dernier scan S3 uniquement
            query = db.query(S3Bucket).filter(S3Bucket.scan_run_id == latest_scan.id)
        else:
            # Mode historique : récupérer tous les buckets
            query = db.query(S3Bucket)
            latest_scan = None

        if client_id:
            query = query.filter(S3Bucket.client_id == client_id)

        if region:
            query = query.filter(S3Bucket.region == region)

        # Trier par date de scan décroissante et limiter
        buckets = query.order_by(S3Bucket.scan_timestamp.desc()).limit(limit).all()

        # Formater la réponse
        result = []
        for bucket in buckets:
            bucket_data = {
                "bucket_name": bucket.bucket_name,
                "region": bucket.region,
                "creation_date": bucket.creation_date.isoformat() if bucket.creation_date else None,
                "encryption_enabled": bucket.encryption_enabled,
                "versioning_enabled": bucket.versioning_enabled,
                "public_access_blocked": bucket.public_access_blocked,
                "public_read_enabled": bucket.public_read_enabled,
                "bucket_policy_enabled": bucket.bucket_policy_enabled,
                "lifecycle_enabled": bucket.lifecycle_enabled,
                "cors_enabled": bucket.cors_enabled,
                "website_enabled": bucket.website_enabled,
                "logging_enabled": bucket.logging_enabled,
                "notifications_enabled": bucket.notifications_enabled,
                "replication_enabled": bucket.replication_enabled,
                "scan_timestamp": bucket.scan_timestamp.isoformat() if bucket.scan_timestamp else None
            }

            # Ajouter les performances si disponibles
            if bucket.performance:
                bucket_data["performance"] = {
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

            result.append(bucket_data)

        return {
            "total_buckets": len(result),
            "buckets": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des buckets S3: {str(e)}")


@router.get("/s3/buckets/{bucket_name}")
async def get_s3_bucket_by_name(
    bucket_name: str,
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique d'un bucket S3 spécifique.

    Args:
        bucket_name: Nom du bucket S3

    Returns:
        Historique complet du bucket avec toutes ses métriques
    """
    try:
        # Récupérer toutes les entrées pour ce bucket (historique)
        buckets = db.query(S3Bucket).filter(
            S3Bucket.bucket_name == bucket_name
        ).order_by(S3Bucket.scan_timestamp.desc()).all()

        if not buckets:
            raise HTTPException(status_code=404, detail=f"Bucket {bucket_name} non trouvé")

        # Formater la réponse
        result = []
        for bucket in buckets:
            bucket_data = {
                "bucket_name": bucket.bucket_name,
                "region": bucket.region,
                "encryption_enabled": bucket.encryption_enabled,
                "versioning_enabled": bucket.versioning_enabled,
                "scan_timestamp": bucket.scan_timestamp.isoformat() if bucket.scan_timestamp else None,
            }

            if bucket.performance:
                bucket_data["performance"] = {
                    "all_requests": bucket.performance.all_requests,
                    "get_requests": bucket.performance.get_requests,
                    "bytes_downloaded": bucket.performance.bytes_downloaded,
                    "bytes_uploaded": bucket.performance.bytes_uploaded
                }

            result.append(bucket_data)

        return {
            "bucket_name": bucket_name,
            "total_scans": len(result),
            "history": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du bucket: {str(e)}")


@router.get("/vpc/instances")
async def get_vpc_instances(
    client_id: Optional[str] = None,
    region: Optional[str] = None,
    latest_only: bool = True,
    scan_id: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les VPCs depuis la base de données.

    ⚠️ ISOLATION DES COMPTES : Seuls les VPCs de l'utilisateur connecté sont retournés.

    Args:
        client_id: Filtrer par client (optionnel)
        region: Filtrer par région (optionnel)
        latest_only: Si True, récupère uniquement les VPCs du dernier scan (défaut: True)
        limit: Nombre maximum de VPCs à retourner (défaut: 50)
        current_user: Utilisateur connecté (injecté automatiquement)

    Returns:
        Liste des VPCs avec leurs métadonnées
    """
    try:
        if scan_id:
            # Récupérer un scan spécifique par son ID
            specific_scan = db.query(ScanRun).filter(
                ScanRun.id == scan_id,
                ScanRun.service_type == 'vpc',
                ScanRun.user_id == current_user.id
            ).first()

            if not specific_scan:
                return {
                    "total_vpcs": 0,
                    "vpcs": [],
                    "scan_id": None,
                    "scan_timestamp": None
                }

            # Récupérer les VPCs de ce scan spécifique
            query = db.query(VPCInstance).filter(VPCInstance.scan_run_id == specific_scan.id)
            latest_scan = specific_scan
        elif latest_only:
            # Récupérer le dernier scan VPC DE L'UTILISATEUR CONNECTÉ
            latest_scan = db.query(ScanRun).filter(
                ScanRun.service_type == 'vpc',
                ScanRun.user_id == current_user.id
            ).order_by(ScanRun.scan_timestamp.desc()).first()

            if not latest_scan:
                return {
                    "total_vpcs": 0,
                    "vpcs": [],
                    "scan_id": None,
                    "scan_timestamp": None
                }

            # Récupérer les VPCs de ce scan
            query = db.query(VPCInstance).filter(VPCInstance.scan_run_id == latest_scan.id)
        else:
            # Récupérer tous les VPCs DE L'UTILISATEUR CONNECTÉ
            query = db.query(VPCInstance).join(ScanRun).filter(ScanRun.user_id == current_user.id)
            latest_scan = None

        # Appliquer les filtres optionnels
        if client_id:
            query = query.filter(VPCInstance.client_id == client_id)

        if region:
            query = query.filter(VPCInstance.region == region)

        # Limiter le nombre de résultats
        vpcs = query.limit(limit).all()

        # Formater la réponse
        result = []
        for vpc in vpcs:
            vpc_data = {
                "id": vpc.id,
                "vpc_id": vpc.vpc_id,
                "client_id": vpc.client_id,
                "cidr_block": vpc.cidr_block,
                "state": vpc.state,
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
                "region": vpc.region,
                "tags": vpc.tags,
                "scan_timestamp": vpc.scan_timestamp.isoformat() if vpc.scan_timestamp else None
            }

            # Ajouter les performances si disponibles
            if vpc.performance:
                vpc_data["performance"] = {
                    "network_in_bytes": vpc.performance.network_in_bytes,
                    "network_out_bytes": vpc.performance.network_out_bytes,
                    "network_packets_in": vpc.performance.network_packets_in,
                    "network_packets_out": vpc.performance.network_packets_out,
                    "nat_gateway_bytes_in": vpc.performance.nat_gateway_bytes_in,
                    "nat_gateway_bytes_out": vpc.performance.nat_gateway_bytes_out
                }

            result.append(vpc_data)

        return {
            "total_vpcs": len(result),
            "vpcs": result,
            "scan_id": latest_scan.id if latest_only and latest_scan else None,
            "scan_timestamp": latest_scan.scan_timestamp.isoformat() if latest_only and latest_scan else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des VPCs: {str(e)}")


@router.get("/rds/instances")
async def get_rds_instances(
    client_id: Optional[str] = None,
    region: Optional[str] = None,
    latest_only: bool = True,
    scan_id: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les instances RDS depuis la base de données.

    ⚠️ ISOLATION DES COMPTES : Seules les instances RDS de l'utilisateur connecté sont retournées.

    Args:
        client_id: Filtrer par client (optionnel)
        region: Filtrer par région (optionnel)
        latest_only: Si True, récupère uniquement les instances du dernier scan (défaut: True)
        limit: Nombre maximum d'instances à retourner (défaut: 50)
        current_user: Utilisateur connecté (injecté automatiquement)

    Returns:
        Liste des instances RDS avec leurs métadonnées
    """
    try:
        if scan_id:
            # Récupérer un scan spécifique par son ID
            specific_scan = db.query(ScanRun).filter(
                ScanRun.id == scan_id,
                ScanRun.service_type == 'rds',
                ScanRun.user_id == current_user.id
            ).first()

            if not specific_scan:
                return {
                    "total_instances": 0,
                    "instances": [],
                    "scan_id": None,
                    "scan_timestamp": None
                }

            # Récupérer les instances RDS de ce scan spécifique
            query = db.query(RDSInstance).filter(RDSInstance.scan_run_id == specific_scan.id)
            latest_scan = specific_scan
        elif latest_only:
            # Récupérer le dernier scan RDS DE L'UTILISATEUR CONNECTÉ
            latest_scan = db.query(ScanRun).filter(
                ScanRun.service_type == 'rds',
                ScanRun.user_id == current_user.id
            ).order_by(ScanRun.scan_timestamp.desc()).first()

            if not latest_scan:
                return {
                    "total_instances": 0,
                    "instances": [],
                    "scan_id": None,
                    "scan_timestamp": None
                }

            # Récupérer les instances RDS de ce scan
            query = db.query(RDSInstance).filter(RDSInstance.scan_run_id == latest_scan.id)
        else:
            # Récupérer toutes les instances RDS DE L'UTILISATEUR CONNECTÉ
            query = db.query(RDSInstance).join(ScanRun).filter(ScanRun.user_id == current_user.id)
            latest_scan = None

        # Appliquer les filtres optionnels
        if client_id:
            query = query.filter(RDSInstance.client_id == client_id)

        if region:
            query = query.filter(RDSInstance.region == region)

        # Limiter le nombre de résultats
        instances = query.limit(limit).all()

        # Formater la réponse
        result = []
        for instance in instances:
            instance_data = {
                "id": instance.id,
                "db_instance_identifier": instance.db_instance_identifier,
                "client_id": instance.client_id,
                "db_instance_class": instance.db_instance_class,
                "engine": instance.engine,
                "engine_version": instance.engine_version,
                "db_instance_status": instance.db_instance_status,
                "allocated_storage": instance.allocated_storage,
                "storage_type": instance.storage_type,
                "storage_encrypted": instance.storage_encrypted,
                "iops": instance.iops,
                "vpc_id": instance.vpc_id,
                "db_subnet_group_name": instance.db_subnet_group_name,
                "availability_zone": instance.availability_zone,
                "multi_az": instance.multi_az,
                "publicly_accessible": instance.publicly_accessible,
                "endpoint_address": instance.endpoint_address,
                "endpoint_port": instance.endpoint_port,
                "master_username": instance.master_username,
                "iam_database_authentication_enabled": instance.iam_database_authentication_enabled,
                "deletion_protection": instance.deletion_protection,
                "backup_retention_period": instance.backup_retention_period,
                "preferred_backup_window": instance.preferred_backup_window,
                "preferred_maintenance_window": instance.preferred_maintenance_window,
                "latest_restorable_time": instance.latest_restorable_time.isoformat() if instance.latest_restorable_time else None,
                "auto_minor_version_upgrade": instance.auto_minor_version_upgrade,
                "enhanced_monitoring_resource_arn": instance.enhanced_monitoring_resource_arn,
                "monitoring_interval": instance.monitoring_interval,
                "performance_insights_enabled": instance.performance_insights_enabled,
                "region": instance.region,
                "tags": instance.tags,
                "security_groups": instance.security_groups,
                "parameter_groups": instance.parameter_groups,
                "option_groups": instance.option_groups,
                "instance_create_time": instance.instance_create_time.isoformat() if instance.instance_create_time else None,
                "scan_timestamp": instance.scan_timestamp.isoformat() if instance.scan_timestamp else None
            }

            # Ajouter les performances si disponibles
            if instance.performance:
                instance_data["performance"] = {
                    "cpu_utilization_avg": instance.performance.cpu_utilization_avg,
                    "freeable_memory_bytes": instance.performance.freeable_memory_bytes,
                    "free_storage_space_bytes": instance.performance.free_storage_space_bytes,
                    "database_connections": instance.performance.database_connections,
                    "read_iops_avg": instance.performance.read_iops_avg,
                    "write_iops_avg": instance.performance.write_iops_avg,
                    "read_latency_avg": instance.performance.read_latency_avg,
                    "write_latency_avg": instance.performance.write_latency_avg,
                    "read_throughput_bytes": instance.performance.read_throughput_bytes,
                    "write_throughput_bytes": instance.performance.write_throughput_bytes,
                    "network_receive_throughput_bytes": instance.performance.network_receive_throughput_bytes,
                    "network_transmit_throughput_bytes": instance.performance.network_transmit_throughput_bytes
                }

            result.append(instance_data)

        return {
            "total_instances": len(result),
            "instances": result,
            "scan_id": latest_scan.id if latest_only and latest_scan else None,
            "scan_timestamp": latest_scan.scan_timestamp.isoformat() if latest_only and latest_scan else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des instances RDS: {str(e)}")


# ========================================
# ENDPOINTS D'ADMINISTRATION
# ========================================

@router.delete("/admin/clear-database")
async def clear_database(
    confirm: bool = False,
    db: Session = Depends(get_db)
):
    """
    ⚠️ DANGER : Supprime TOUTES les données de la base de données.

    Cet endpoint est utile en développement pour repartir de zéro.
    Il supprime tous les scans et toutes les ressources associées.

    Args:
        confirm: Doit être True pour confirmer la suppression (obligatoire)

    Returns:
        Statistiques de suppression

    Exemple:
        DELETE /api/v1/admin/clear-database?confirm=true
    """
    # Vérifier la confirmation
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="⚠️ Vous devez confirmer la suppression avec ?confirm=true"
        )

    try:
        # Compter les éléments avant suppression
        users_count = db.query(User).count()
        scan_runs_count = db.query(ScanRun).count()
        ec2_instances_count = db.query(EC2Instance).count()
        ec2_performance_count = db.query(EC2Performance).count()
        s3_buckets_count = db.query(S3Bucket).count()
        s3_performance_count = db.query(S3Performance).count()
        vpc_instances_count = db.query(VPCInstance).count()
        vpc_performance_count = db.query(VPCPerformance).count()
        rds_instances_count = db.query(RDSInstance).count()
        rds_performance_count = db.query(RDSPerformance).count()

        # Utiliser TRUNCATE pour réinitialiser les AUTO_INCREMENT
        # TRUNCATE supprime toutes les lignes ET remet les compteurs à 0
        db.execute("SET FOREIGN_KEY_CHECKS = 0")
        db.execute("TRUNCATE TABLE ec2_performance")
        db.execute("TRUNCATE TABLE s3_performance")
        db.execute("TRUNCATE TABLE vpc_performance")
        db.execute("TRUNCATE TABLE rds_performance")
        db.execute("TRUNCATE TABLE ec2_instances")
        db.execute("TRUNCATE TABLE s3_buckets")
        db.execute("TRUNCATE TABLE vpc_instances")
        db.execute("TRUNCATE TABLE rds_instances")
        db.execute("TRUNCATE TABLE scan_runs")
        db.execute("TRUNCATE TABLE users")
        db.execute("SET FOREIGN_KEY_CHECKS = 1")

        # Commit de la transaction
        db.commit()

        return {
            "status": "success",
            "message": "✅ Base de données vidée avec succès (IDs réinitialisés)",
            "deleted": {
                "users": users_count,
                "scan_runs": scan_runs_count,
                "ec2_instances": ec2_instances_count,
                "ec2_performance": ec2_performance_count,
                "s3_buckets": s3_buckets_count,
                "s3_performance": s3_performance_count,
                "vpc_instances": vpc_instances_count,
                "vpc_performance": vpc_performance_count,
                "rds_instances": rds_instances_count,
                "rds_performance": rds_performance_count,
                "total": (
                    users_count +
                    scan_runs_count +
                    ec2_instances_count +
                    ec2_performance_count +
                    s3_buckets_count +
                    s3_performance_count +
                    vpc_instances_count +
                    vpc_performance_count +
                    rds_instances_count +
                    rds_performance_count
                )
            }
        }

    except Exception as e:
        # Rollback en cas d'erreur
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"❌ Erreur lors de la suppression: {str(e)}"
        )


@router.delete("/admin/clear-user-data")
async def clear_user_data(
    confirm: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🧹 Supprime UNIQUEMENT les données de l'utilisateur connecté.

    Cet endpoint est utile en phase de testing pour nettoyer ses propres données
    sans affecter les autres utilisateurs. Il supprime :
    - Tous les scans de l'utilisateur
    - Toutes les instances EC2 associées
    - Toutes les métriques EC2 associées
    - Tous les buckets S3 associés
    - Toutes les métriques S3 associées

    ⚠️ Le compte utilisateur est CONSERVÉ (seules les données de scan sont supprimées).

    Args:
        confirm: Doit être True pour confirmer la suppression (obligatoire)
        current_user: Utilisateur connecté (injecté automatiquement)

    Returns:
        Statistiques de suppression

    Exemple:
        DELETE /api/v1/admin/clear-user-data?confirm=true
        Headers: Authorization: Bearer <token>
    """
    # Vérifier la confirmation
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="⚠️ Vous devez confirmer la suppression avec ?confirm=true"
        )

    try:
        # Récupérer tous les scan_runs de l'utilisateur
        user_scans = db.query(ScanRun).filter(ScanRun.user_id == current_user.id).all()
        scan_ids = [scan.id for scan in user_scans]

        if not scan_ids:
            return {
                "status": "success",
                "message": "✅ Aucune donnée à supprimer pour cet utilisateur",
                "user_email": current_user.email,
                "deleted": {
                    "scan_runs": 0,
                    "ec2_instances": 0,
                    "ec2_performance": 0,
                    "s3_buckets": 0,
                    "s3_performance": 0,
                    "vpc_instances": 0,
                    "vpc_performance": 0,
                    "rds_instances": 0,
                    "rds_performance": 0,
                    "total": 0
                }
            }

        # Compter les éléments avant suppression
        scan_runs_count = len(scan_ids)
        ec2_instances_count = db.query(EC2Instance).filter(EC2Instance.scan_run_id.in_(scan_ids)).count()
        s3_buckets_count = db.query(S3Bucket).filter(S3Bucket.scan_run_id.in_(scan_ids)).count()
        vpc_instances_count = db.query(VPCInstance).filter(VPCInstance.scan_run_id.in_(scan_ids)).count()
        rds_instances_count = db.query(RDSInstance).filter(RDSInstance.scan_run_id.in_(scan_ids)).count()

        # Compter les métriques (via les instances/buckets/vpcs/rds)
        ec2_instance_ids = [inst.id for inst in db.query(EC2Instance.id).filter(EC2Instance.scan_run_id.in_(scan_ids)).all()]
        s3_bucket_ids = [bucket.id for bucket in db.query(S3Bucket.id).filter(S3Bucket.scan_run_id.in_(scan_ids)).all()]
        vpc_instance_ids = [vpc.id for vpc in db.query(VPCInstance.id).filter(VPCInstance.scan_run_id.in_(scan_ids)).all()]
        rds_instance_ids = [rds.id for rds in db.query(RDSInstance.id).filter(RDSInstance.scan_run_id.in_(scan_ids)).all()]

        ec2_performance_count = db.query(EC2Performance).filter(EC2Performance.ec2_instance_id.in_(ec2_instance_ids)).count() if ec2_instance_ids else 0
        s3_performance_count = db.query(S3Performance).filter(S3Performance.s3_bucket_id.in_(s3_bucket_ids)).count() if s3_bucket_ids else 0
        vpc_performance_count = db.query(VPCPerformance).filter(VPCPerformance.vpc_instance_id.in_(vpc_instance_ids)).count() if vpc_instance_ids else 0
        rds_performance_count = db.query(RDSPerformance).filter(RDSPerformance.rds_instance_id.in_(rds_instance_ids)).count() if rds_instance_ids else 0

        # Supprimer dans l'ordre (des enfants vers les parents pour respecter les foreign keys)

        # 1. Supprimer les métriques EC2
        if ec2_instance_ids:
            db.query(EC2Performance).filter(EC2Performance.ec2_instance_id.in_(ec2_instance_ids)).delete(synchronize_session=False)

        # 2. Supprimer les métriques S3
        if s3_bucket_ids:
            db.query(S3Performance).filter(S3Performance.s3_bucket_id.in_(s3_bucket_ids)).delete(synchronize_session=False)

        # 3. Supprimer les métriques VPC
        if vpc_instance_ids:
            db.query(VPCPerformance).filter(VPCPerformance.vpc_instance_id.in_(vpc_instance_ids)).delete(synchronize_session=False)

        # 4. Supprimer les métriques RDS
        if rds_instance_ids:
            db.query(RDSPerformance).filter(RDSPerformance.rds_instance_id.in_(rds_instance_ids)).delete(synchronize_session=False)

        # 5. Supprimer les instances EC2
        db.query(EC2Instance).filter(EC2Instance.scan_run_id.in_(scan_ids)).delete(synchronize_session=False)

        # 6. Supprimer les buckets S3
        db.query(S3Bucket).filter(S3Bucket.scan_run_id.in_(scan_ids)).delete(synchronize_session=False)

        # 7. Supprimer les VPCs
        db.query(VPCInstance).filter(VPCInstance.scan_run_id.in_(scan_ids)).delete(synchronize_session=False)

        # 8. Supprimer les instances RDS
        db.query(RDSInstance).filter(RDSInstance.scan_run_id.in_(scan_ids)).delete(synchronize_session=False)

        # 9. Supprimer les scan_runs
        db.query(ScanRun).filter(ScanRun.user_id == current_user.id).delete(synchronize_session=False)

        # Commit de la transaction
        db.commit()

        return {
            "status": "success",
            "message": f"✅ Données de l'utilisateur {current_user.email} supprimées avec succès",
            "user_email": current_user.email,
            "user_id": current_user.id,
            "deleted": {
                "scan_runs": scan_runs_count,
                "ec2_instances": ec2_instances_count,
                "ec2_performance": ec2_performance_count,
                "s3_buckets": s3_buckets_count,
                "s3_performance": s3_performance_count,
                "vpc_instances": vpc_instances_count,
                "vpc_performance": vpc_performance_count,
                "rds_instances": rds_instances_count,
                "rds_performance": rds_performance_count,
                "total": (
                    scan_runs_count +
                    ec2_instances_count +
                    ec2_performance_count +
                    s3_buckets_count +
                    s3_performance_count +
                    vpc_instances_count +
                    vpc_performance_count +
                    rds_instances_count +
                    rds_performance_count
                )
            }
        }

    except Exception as e:
        # Rollback en cas d'erreur
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"❌ Erreur lors de la suppression des données utilisateur: {str(e)}"
        )
