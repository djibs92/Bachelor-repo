
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid
from api.config.supported_services import SUPPORTED_PROVIDERS, SUPPORTED_SERVICES_AWS, SUPPORTED_AUTH_MODES
from api.services.scan_engine import scan_list_service
from api.database import User
from api.endpoints.auth import get_current_user

router = APIRouter()

class AuthMode(BaseModel):
    type: str
    role_arn: str = Field(..., description="ARN du rôle AWS à assumer")

class ScanRequest(BaseModel):
    provider: str
    services: List[str]
    auth_mode: AuthMode
    client_id: str = Field(..., description="Identifiant du client")
    regions: List[str] = Field(default=None,description="Régions spécifiques à scanner (optionnel)")

class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str

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

