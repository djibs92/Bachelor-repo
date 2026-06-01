from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.database import get_db, ScanRun, User
from api.endpoints.auth import get_current_user

router = APIRouter()

class ScanUpdate(BaseModel):
    client_id: Optional[str] = None
    status: Optional[str] = None

@router.get("/scans/latest-session", tags=["🔍 Scans"])
async def get_latest_scan_session(
    scan_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère la dernière SESSION de scan (tous les services scannés en même temps).

    Une session de scan = tous les scans lancés dans une fenêtre de 30 secondes.
    Cela permet d'afficher uniquement les services réellement scannés lors du dernier scan.

    Si vous scannez seulement EC2, seul EC2 sera affiché (S3=0).
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

        # Utiliser session_id pour grouper les scans multi-services de manière fiable
        # Le session_id est défini dans scan_engine.py lors du lancement d'un scan
        if reference_scan.session_id:
            # Méthode préférée : grouper par session_id
            session_scans = db.query(ScanRun).filter(
                ScanRun.user_id == current_user.id,
                ScanRun.session_id == reference_scan.session_id,
                ScanRun.status.in_(['success', 'partial', 'failed'])
            ).order_by(ScanRun.scan_timestamp.desc()).all()
        else:
            # Fallback pour les anciens scans sans session_id : utiliser une fenêtre de temps
            from datetime import timedelta
            session_window = timedelta(minutes=5)
            session_start = reference_scan.scan_timestamp - session_window
            session_end = reference_scan.scan_timestamp + session_window

            session_scans = db.query(ScanRun).filter(
                ScanRun.user_id == current_user.id,
                ScanRun.scan_timestamp >= session_start,
                ScanRun.scan_timestamp <= session_end,
                ScanRun.status.in_(['success', 'partial', 'failed'])
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


@router.get("/scans/history", tags=["🔍 Scans"])
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
        service_type: Filtrer par type de service (ec2, s3) (optionnel)
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


@router.patch("/scans/{scan_id}", tags=["🔍 Scans"])
async def update_scan(
    scan_id: int,
    scan_update: ScanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour un scan (ex: changer le nom/client_id).
    """
    scan = db.query(ScanRun).filter(ScanRun.id == scan_id, ScanRun.user_id == current_user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan non trouvé")

    if scan_update.client_id is not None:
        scan.client_id = scan_update.client_id
    if scan_update.status is not None:
        scan.status = scan_update.status

    db.commit()
    db.refresh(scan)
    return {"message": "Scan mis à jour avec succès", "scan_id": scan.id, "new_client_id": scan.client_id}


@router.delete("/scans/{scan_id}", tags=["🔍 Scans"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime un scan et toutes les ressources associées (Cascade).
    """
    scan = db.query(ScanRun).filter(ScanRun.id == scan_id, ScanRun.user_id == current_user.id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan non trouvé")

    db.delete(scan)
    db.commit()
    return None

