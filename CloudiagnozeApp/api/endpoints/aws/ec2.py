from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session

from api.database import get_db, ScanRun, EC2Instance, User
from api.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/ec2/instances", tags=["💻 EC2"])
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




@router.get("/ec2/instances/{instance_id}", tags=["💻 EC2"])
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