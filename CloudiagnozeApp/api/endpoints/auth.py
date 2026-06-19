"""
Endpoints d'authentification pour CloudDiagnoze.

Ce module fournit les endpoints pour :
- Inscription (signup)
- Connexion (login)
- Récupération des infos utilisateur (me)
- Réinitialisation de mot de passe (forgot-password, reset-password)
"""

import os

from fastapi import APIRouter, HTTPException, Depends, Header, Request, Response, Cookie
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
from loguru import logger

from api.utils.limiter import limiter

from api.database import get_db, User
from api.utils import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    generate_reset_token,
    create_reset_token_expiry,
    is_reset_token_valid,
    validate_password_strength,
    validate_email,
)

router = APIRouter()

# ========================================
# CONFIGURATION COOKIE JWT
# ========================================
ACCESS_TOKEN_COOKIE_NAME = "access_token"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").lower()


def _set_access_token_cookie(response: Response, token: str) -> None:
    """Pose le cookie httpOnly contenant le JWT sur la réponse."""
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )


def _clear_access_token_cookie(response: Response) -> None:
    """Supprime le cookie httpOnly contenant le JWT."""
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

# ========================================
# MODÈLES PYDANTIC (SCHÉMAS)
# ========================================


class SignupRequest(BaseModel):
    """Schéma pour l'inscription d'un nouvel utilisateur"""

    email: EmailStr = Field(..., description="Email de l'utilisateur", example="user@example.com")
    password: str = Field(
        ..., min_length=8, description="Mot de passe (min 8 caractères, 1 majuscule, 1 chiffre)", example="SecurePass123"
    )
    full_name: Optional[str] = Field(None, description="Nom complet", example="Jean Dupont")
    company_name: Optional[str] = Field(None, description="Nom de l'entreprise", example="Ma Startup SAS")
    role_arn: Optional[str] = Field(None, description="Role ARN AWS pour les scans", example="arn:aws:iam::123456789012:role/CloudDiagnozeRole")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "full_name": "Jean Dupont",
                "company_name": "Ma Startup SAS"
            }
        }


class LoginRequest(BaseModel):
    """Schéma pour la connexion utilisateur"""

    email: EmailStr = Field(..., description="Email de l'utilisateur", example="user@example.com")
    password: str = Field(..., description="Mot de passe", example="SecurePass123")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class LoginResponse(BaseModel):
    """Schéma pour la réponse de connexion avec token JWT"""

    access_token: str = Field(..., description="Token JWT à utiliser dans le header Authorization", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(default="bearer", description="Type de token", example="bearer")
    user: dict = Field(..., description="Informations de l'utilisateur connecté")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZXhwIjoxNzA0MDY3MjAwfQ.abc123",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "full_name": "Jean Dupont",
                    "company_name": "Ma Startup SAS"
                }
            }
        }


class UserResponse(BaseModel):
    """Schéma pour les informations utilisateur complètes"""

    id: int = Field(..., example=1)
    email: str = Field(..., example="user@example.com")
    full_name: Optional[str] = Field(None, example="Jean Dupont")
    company_name: Optional[str] = Field(None, example="Ma Startup SAS")
    role_arn: Optional[str] = Field(None, example="arn:aws:iam::123456789012:role/CloudDiagnozeRole")
    created_at: datetime
    last_login: Optional[datetime]


class ForgotPasswordRequest(BaseModel):
    """Schéma pour la demande de réinitialisation de mot de passe"""

    email: EmailStr = Field(..., description="Email de l'utilisateur", example="user@example.com")


class ResetPasswordRequest(BaseModel):
    """Schéma pour la réinitialisation de mot de passe avec token"""

    token: str = Field(..., description="Token de réinitialisation reçu par email", example="abc123def456...")
    new_password: str = Field(..., min_length=8, description="Nouveau mot de passe", example="NewSecurePass456")


class MessageResponse(BaseModel):
    """Schéma pour les réponses simples"""

    message: str


# ========================================
# FONCTIONS UTILITAIRES
# ========================================


def get_current_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Récupère l'utilisateur actuel à partir du token JWT.

    Le token est lu en priorité dans le cookie httpOnly `access_token` ;
    le header `Authorization: Bearer <token>` reste accepté pour la
    rétro-compatibilité (Swagger, clients CLI, intégrations).

    Args:
        authorization: Header Authorization optionnel (format: "Bearer <token>")
        access_token: Cookie httpOnly contenant le JWT
        db: Session de base de données

    Returns:
        Utilisateur connecté

    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur n'existe pas
    """
    token: Optional[str] = None
    header_token: Optional[str] = None

    # 1. Si un header Authorization est fourni, on valide systématiquement
    #    sa syntaxe (`Bearer <token>`) avant toute autre logique, même si
    #    un cookie valide est présent (sécurité : un header malformé doit
    #    toujours être rejeté).
    if authorization:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401, detail="Format du header Authorization invalide"
            )
        header_token = parts[1]

    # 2. Priorité au cookie httpOnly, puis fallback sur le header validé
    if access_token:
        token = access_token
    elif header_token:
        token = header_token

    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")

    # Vérifier le token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    # Récupérer l'utilisateur
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    # Vérification anti-replay : le token_version du JWT doit correspondre à la BDD
    token_version = payload.get("token_version", 0)
    if user.token_version != token_version:
        raise HTTPException(status_code=401, detail="Session révoquée — veuillez vous reconnecter")

    return user


# ========================================
# ENDPOINTS
# ========================================


@router.post("/signup", response_model=MessageResponse, status_code=201)
@limiter.limit("5/minute")
async def signup(
    request: Request, signup_data: SignupRequest, db: Session = Depends(get_db)
):
    """
    Inscription d'un nouvel utilisateur.

    Args:
        request: Requête HTTP (pour rate limiting)
        signup_data: Données d'inscription
        db: Session de base de données

    Returns:
        Message de confirmation

    Raises:
        HTTPException: Si l'email existe déjà ou si les données sont invalides
    """
    logger.info(f"📝 Tentative d'inscription pour {signup_data.email}")

    # 1. Valider l'email
    if not validate_email(signup_data.email):
        raise HTTPException(status_code=400, detail="Format d'email invalide")

    # 2. Vérifier que l'email n'existe pas déjà
    existing_user = db.query(User).filter(User.email == signup_data.email).first()
    if existing_user:
        logger.warning(f"⚠️ Email déjà utilisé : {signup_data.email}")
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    # 3. Valider la force du mot de passe
    is_valid, error_message = validate_password_strength(signup_data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # 4. Hasher le mot de passe
    password_hash = hash_password(signup_data.password)

    # 5. Créer l'utilisateur
    new_user = User(
        email=signup_data.email,
        password_hash=password_hash,
        full_name=signup_data.full_name,
        company_name=signup_data.company_name,
        role_arn=signup_data.role_arn,
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.success(f"✅ Utilisateur créé : {new_user.email} (ID: {new_user.id})")

    return MessageResponse(message="Compte créé avec succès")


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Connexion d'un utilisateur.

    Args:
        request: Requête HTTP (pour rate limiting)
        login_data: Données de connexion
        response: Réponse HTTP (pour poser le cookie httpOnly)
        db: Session de base de données

    Returns:
        Token JWT et informations utilisateur

    Raises:
        HTTPException: Si l'email ou le mot de passe est incorrect
    """
    logger.info(f"🔐 Tentative de connexion pour {login_data.email}")

    # 1. Récupérer l'utilisateur
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user:
        logger.warning(f"⚠️ Utilisateur non trouvé : {login_data.email}")
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # 2. Vérifier que le compte est actif
    if not user.is_active:
        logger.warning(f"⚠️ Compte désactivé : {login_data.email}")
        raise HTTPException(status_code=403, detail="Compte désactivé")

    # 3. Vérifier le mot de passe
    if not verify_password(login_data.password, user.password_hash):
        logger.warning(f"⚠️ Mot de passe incorrect pour {login_data.email}")
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    # 4. Mettre à jour la date de dernière connexion
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # 5. Créer le token JWT (token_version inclus pour la révocation)
    access_token = create_access_token({
        "sub": user.email,
        "user_id": user.id,
        "token_version": user.token_version,
    })

    # 6. Poser le cookie httpOnly (méthode d'auth principale côté navigateur)
    _set_access_token_cookie(response, access_token)

    logger.success(f"✅ Connexion réussie pour {user.email}")

    # 7. Retourner le token et les infos utilisateur
    #    (le token reste dans la réponse pour la rétro-compatibilité Swagger/CLI)
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "company_name": user.company_name,
            "role_arn": user.role_arn,
        },
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """
    Déconnexion : supprime le cookie ET incrémente token_version en BDD pour
    invalider tous les tokens existants (protection anti-replay).

    Args:
        response: Réponse HTTP (pour effacer le cookie)
        authorization: Header Authorization optionnel
        access_token: Cookie httpOnly contenant le JWT
        db: Session de base de données

    Returns:
        Message de confirmation
    """
    # Résoudre le token (cookie prioritaire, fallback header)
    token: Optional[str] = access_token
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    # Révoquer le token si valide : incrémenter token_version en BDD
    if token:
        payload = verify_token(token)
        if payload:
            user_id = payload.get("user_id")
            token_ver = payload.get("token_version", 0)
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.token_version == token_ver:
                    user.token_version = user.token_version + 1
                    db.commit()
                    logger.info(f"🔒 Token révoqué pour user {user_id} (version → {user.token_version})")

    _clear_access_token_cookie(response)
    logger.info("🚪 Déconnexion : cookie access_token effacé")
    return MessageResponse(message="Déconnexion réussie")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Récupère les informations de l'utilisateur connecté.

    Args:
        current_user: Utilisateur connecté (injecté par get_current_user)

    Returns:
        Informations utilisateur
    """
    logger.info(f"👤 Récupération des infos pour {current_user.email}")

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        company_name=current_user.company_name,
        role_arn=current_user.role_arn,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request, forgot_data: ForgotPasswordRequest, db: Session = Depends(get_db)
):
    """
    Demande de réinitialisation de mot de passe.

    Args:
        request: Requête HTTP (pour rate limiting)
        forgot_data: Email de l'utilisateur
        db: Session de base de données

    Returns:
        Message de confirmation

    Note:
        Pour des raisons de sécurité, on retourne toujours le même message,
        même si l'email n'existe pas.
    """
    logger.info(
        f"🔑 Demande de réinitialisation de mot de passe pour {forgot_data.email}"
    )

    # Récupérer l'utilisateur
    user = db.query(User).filter(User.email == forgot_data.email).first()

    if user:
        # Générer un token de réinitialisation
        reset_token = generate_reset_token()
        reset_expiry = create_reset_token_expiry(24)  # Valide 24h

        # Stocker le token dans la base de données
        user.reset_token = reset_token
        user.reset_token_expiry = reset_expiry
        db.commit()

        logger.success(f"✅ Token de réinitialisation généré pour {user.email}")

        # TODO: Envoyer un email avec le lien de réinitialisation
        # send_email(user.email, f"Reset link: https://clouddiagnoze.com/reset?token={reset_token}")
        logger.info(f"📧 Email de réinitialisation à envoyer à {user.email}")
        logger.info(f"🔗 Token: {reset_token}")
    else:
        logger.warning(f"⚠️ Email non trouvé : {forgot_data.email}")

    # Toujours retourner le même message (sécurité)
    return MessageResponse(
        message="Si cet email existe, un lien de réinitialisation a été envoyé"
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def reset_password(
    request: Request, reset_data: ResetPasswordRequest, db: Session = Depends(get_db)
):
    """
    Réinitialise le mot de passe avec un token.

    Args:
        request: Requête HTTP (pour rate limiting)
        reset_data: Token et nouveau mot de passe
        db: Session de base de données

    Returns:
        Message de confirmation

    Raises:
        HTTPException: Si le token est invalide ou expiré
    """
    logger.info(f"🔄 Tentative de réinitialisation de mot de passe")

    # 1. Récupérer l'utilisateur avec ce token
    user = db.query(User).filter(User.reset_token == reset_data.token).first()

    if not user:
        logger.warning(f"⚠️ Token de réinitialisation invalide")
        raise HTTPException(status_code=400, detail="Token invalide")

    # 2. Vérifier que le token n'est pas expiré
    if not is_reset_token_valid(user.reset_token_expiry):
        logger.warning(f"⚠️ Token de réinitialisation expiré pour {user.email}")
        raise HTTPException(status_code=400, detail="Token expiré")

    # 3. Valider le nouveau mot de passe
    is_valid, error_message = validate_password_strength(reset_data.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # 4. Hasher le nouveau mot de passe
    new_password_hash = hash_password(reset_data.new_password)

    # 5. Mettre à jour le mot de passe, supprimer le token et invalider les sessions
    user.password_hash = new_password_hash
    user.reset_token = None
    user.reset_token_expiry = None
    user.token_version = user.token_version + 1
    db.commit()

    logger.success(f"✅ Mot de passe réinitialisé pour {user.email} (tokens révoqués)")

    return MessageResponse(message="Mot de passe réinitialisé avec succès")


# ========================================
# ENDPOINT : MISE À JOUR DES INFORMATIONS UTILISATEUR
# ========================================


class UpdateUserRequest(BaseModel):
    """Schéma pour la mise à jour des informations utilisateur"""

    full_name: Optional[str] = Field(None, description="Nom complet")
    company_name: Optional[str] = Field(None, description="Nom de l'entreprise")
    role_arn: Optional[str] = Field(None, description="Role ARN AWS")


@router.patch("/me", response_model=UserResponse)
async def update_user_info(
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Met à jour les informations de l'utilisateur connecté.

    Args:
        request: Données à mettre à jour
        current_user: Utilisateur connecté (via token JWT)
        db: Session de base de données

    Returns:
        Informations utilisateur mises à jour
    """
    logger.info(f"📝 Mise à jour des infos pour {current_user.email}")

    # Mettre à jour les champs fournis
    if request.full_name is not None:
        current_user.full_name = request.full_name
    if request.company_name is not None:
        current_user.company_name = request.company_name
    if request.role_arn is not None:
        current_user.role_arn = request.role_arn

    db.commit()
    db.refresh(current_user)

    logger.success(f"✅ Informations mises à jour pour {current_user.email}")

    return current_user


# ========================================
# ENDPOINT : CHANGEMENT DE MOT DE PASSE
# ========================================


class ChangePasswordRequest(BaseModel):
    """Schéma pour le changement de mot de passe"""

    current_password: str = Field(..., description="Mot de passe actuel")
    new_password: str = Field(..., min_length=8, description="Nouveau mot de passe")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change le mot de passe de l'utilisateur connecté.

    Args:
        request: Mot de passe actuel et nouveau mot de passe
        current_user: Utilisateur connecté (via token JWT)
        db: Session de base de données

    Returns:
        Message de confirmation
    """
    logger.info(f"🔐 Changement de mot de passe pour {current_user.email}")

    # 1. Vérifier le mot de passe actuel
    if not verify_password(request.current_password, current_user.password_hash):
        logger.warning(f"⚠️ Mot de passe actuel incorrect pour {current_user.email}")
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

    # 2. Valider le nouveau mot de passe
    is_valid, error_message = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # 3. Hasher le nouveau mot de passe et invalider tous les tokens existants
    current_user.password_hash = hash_password(request.new_password)
    current_user.token_version = current_user.token_version + 1
    db.commit()

    logger.success(f"✅ Mot de passe changé pour {current_user.email} (tokens révoqués)")

    return MessageResponse(message="Mot de passe changé avec succès")


# ========================================
# ENDPOINT : SUPPRESSION DU COMPTE UTILISATEUR
# ========================================


@router.delete("/me", response_model=MessageResponse)
async def delete_account(
    confirm: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    🗑️ Supprime définitivement le compte de l'utilisateur connecté.

    ⚠️ ATTENTION : Cette action est IRRÉVERSIBLE !

    Supprime :
    - Le compte utilisateur
    - Tous les scans associés
    - Toutes les données d'infrastructure (EC2, S3)

    Args:
        confirm: Doit être True pour confirmer la suppression
        current_user: Utilisateur connecté (via token JWT)
        db: Session de base de données

    Returns:
        Message de confirmation

    Exemple:
        DELETE /api/v1/auth/me?confirm=true
        Headers: Authorization: Bearer <token>
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="⚠️ Vous devez confirmer la suppression avec ?confirm=true"
        )

    user_email = current_user.email
    user_id = current_user.id

    logger.warning(f"🗑️ Suppression du compte demandée pour {user_email} (ID: {user_id})")

    try:
        from api.database import ScanRun, EC2Instance, EC2Performance, S3Bucket, S3Performance

        scan_ids = [s.id for s in db.query(ScanRun).filter(ScanRun.user_id == user_id).all()]

        if scan_ids:
            ec2_ids = [e.id for e in db.query(EC2Instance).filter(EC2Instance.scan_run_id.in_(scan_ids)).all()]
            s3_ids = [s.id for s in db.query(S3Bucket).filter(S3Bucket.scan_run_id.in_(scan_ids)).all()]

            if ec2_ids:
                db.query(EC2Performance).filter(EC2Performance.ec2_instance_id.in_(ec2_ids)).delete(synchronize_session=False)
            if s3_ids:
                db.query(S3Performance).filter(S3Performance.s3_bucket_id.in_(s3_ids)).delete(synchronize_session=False)

            db.query(EC2Instance).filter(EC2Instance.scan_run_id.in_(scan_ids)).delete(synchronize_session=False)
            db.query(S3Bucket).filter(S3Bucket.scan_run_id.in_(scan_ids)).delete(synchronize_session=False)
            db.query(ScanRun).filter(ScanRun.user_id == user_id).delete(synchronize_session=False)

        # 3. Supprimer l'utilisateur
        db.delete(current_user)
        db.commit()

        logger.success(f"✅ Compte {user_email} supprimé définitivement")

        return MessageResponse(
            message=f"Compte {user_email} et toutes les données associées ont été supprimés définitivement"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur lors de la suppression du compte: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression du compte: {str(e)}"
        )
