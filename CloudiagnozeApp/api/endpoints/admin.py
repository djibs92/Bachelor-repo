from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db, ScanRun, EC2Instance, EC2Performance, S3Bucket, S3Performance, User
from api.endpoints.auth import get_current_user

router = APIRouter()


@router.delete("/admin/clear-database", tags=["⚙️ Admin"])
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
        users_count = db.query(User).count()
        scan_runs_count = db.query(ScanRun).count()
        ec2_instances_count = db.query(EC2Instance).count()
        ec2_performance_count = db.query(EC2Performance).count()
        s3_buckets_count = db.query(S3Bucket).count()
        s3_performance_count = db.query(S3Performance).count()

        db.execute("SET FOREIGN_KEY_CHECKS = 0")
        db.execute("TRUNCATE TABLE ec2_performance")
        db.execute("TRUNCATE TABLE s3_performance")
        db.execute("TRUNCATE TABLE ec2_instances")
        db.execute("TRUNCATE TABLE s3_buckets")
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
                "total": (
                    users_count +
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




@router.delete("/admin/clear-user-data", tags=["⚙️ Admin"])
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
                    "total": 0
                }
            }

        scan_runs_count = len(scan_ids)
        ec2_instances_count = db.query(EC2Instance).filter(EC2Instance.scan_run_id.in_(scan_ids)).count()
        s3_buckets_count = db.query(S3Bucket).filter(S3Bucket.scan_run_id.in_(scan_ids)).count()

        ec2_instance_ids = [inst.id for inst in db.query(EC2Instance.id).filter(EC2Instance.scan_run_id.in_(scan_ids)).all()]
        s3_bucket_ids = [bucket.id for bucket in db.query(S3Bucket.id).filter(S3Bucket.scan_run_id.in_(scan_ids)).all()]

        ec2_performance_count = db.query(EC2Performance).filter(EC2Performance.ec2_instance_id.in_(ec2_instance_ids)).count() if ec2_instance_ids else 0
        s3_performance_count = db.query(S3Performance).filter(S3Performance.s3_bucket_id.in_(s3_bucket_ids)).count() if s3_bucket_ids else 0

        if ec2_instance_ids:
            db.query(EC2Performance).filter(EC2Performance.ec2_instance_id.in_(ec2_instance_ids)).delete(synchronize_session=False)

        if s3_bucket_ids:
            db.query(S3Performance).filter(S3Performance.s3_bucket_id.in_(s3_bucket_ids)).delete(synchronize_session=False)

        db.query(EC2Instance).filter(EC2Instance.scan_run_id.in_(scan_ids)).delete(synchronize_session=False)

        db.query(S3Bucket).filter(S3Bucket.scan_run_id.in_(scan_ids)).delete(synchronize_session=False)

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
            detail=f"❌ Erreur lors de la suppression des données utilisateur: {str(e)}"
        )