from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from api.database import get_db, ScanRun, EC2Instance, EC2Performance, S3Bucket, S3Performance

router = APIRouter()

# ========================================
# ENDPOINTS DE RÉCUPÉRATION (Base de données)
# ========================================

@router.get("/scans/history")
async def get_scans_history(
    client_id: Optional[str] = None,
    service_type: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique des scans depuis la base de données.

    Args:
        client_id: Filtrer par client (optionnel)
        service_type: Filtrer par type de service (ec2, s3, vpc) (optionnel)
        limit: Nombre maximum de scans à retourner (défaut: 10)

    Returns:
        Liste des scans avec leurs métadonnées
    """
    try:
        # Construire la requête
        query = db.query(ScanRun)

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
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Récupère les instances EC2 depuis la base de données.

    Args:
        client_id: Filtrer par client (optionnel)
        region: Filtrer par région (optionnel)
        state: Filtrer par état (running, stopped, etc.) (optionnel)
        limit: Nombre maximum d'instances à retourner (défaut: 50)

    Returns:
        Liste des instances EC2 avec leurs performances
    """
    try:
        # Construire la requête
        query = db.query(EC2Instance)

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
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Récupère les buckets S3 depuis la base de données.

    Args:
        client_id: Filtrer par client (optionnel)
        region: Filtrer par région (optionnel)
        limit: Nombre maximum de buckets à retourner (défaut: 50)

    Returns:
        Liste des buckets S3 avec leurs performances
    """
    try:
        # Construire la requête
        query = db.query(S3Bucket)

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
        scan_runs_count = db.query(ScanRun).count()
        ec2_instances_count = db.query(EC2Instance).count()
        ec2_performance_count = db.query(EC2Performance).count()
        s3_buckets_count = db.query(S3Bucket).count()
        s3_performance_count = db.query(S3Performance).count()

        # Supprimer dans l'ordre (à cause des foreign keys)
        # 1. Supprimer les performances (tables enfants)
        db.query(EC2Performance).delete()
        db.query(S3Performance).delete()

        # 2. Supprimer les ressources
        db.query(EC2Instance).delete()
        db.query(S3Bucket).delete()

        # 3. Supprimer les scan runs
        db.query(ScanRun).delete()

        # Commit de la transaction
        db.commit()

        return {
            "status": "success",
            "message": "✅ Base de données vidée avec succès",
            "deleted": {
                "scan_runs": scan_runs_count,
                "ec2_instances": ec2_instances_count,
                "ec2_performance": ec2_performance_count,
                "s3_buckets": s3_buckets_count,
                "s3_performance": s3_performance_count,
                "total": (
                    scan_runs_count +
                    ec2_instances_count +
                    ec2_performance_count +
                    s3_buckets_count +
                    s3_performance_count
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
