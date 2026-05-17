from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session

from api.database import get_db, ScanRun, S3Bucket, User
from api.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/s3/buckets", tags=["🪣 S3"])
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




@router.get("/s3/buckets/{bucket_name}", tags=["🪣 S3"])
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