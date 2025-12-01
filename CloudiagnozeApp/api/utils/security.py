"""
Utilitaires de sécurité pour CloudDiagnoze.

Ce module fournit des fonctions pour :
- Hasher et vérifier les mots de passe (bcrypt)
- Générer et vérifier les tokens JWT
- Générer des tokens de réinitialisation de mot de passe
"""

from datetime import datetime, timedelta
from typing import Optional
import secrets
import os
from passlib.context import CryptContext
from jose import JWTError, jwt
from loguru import logger

# ========================================
# CONFIGURATION
# ========================================

# Configuration du hashing de mot de passe avec bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration JWT
# ✅ SÉCURITÉ : Lecture de la clé secrète depuis les variables d'environnement
SECRET_KEY = os.getenv("SECRET_KEY", "clouddiagnoze-secret-key-change-this-in-production-2024")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))  # 7 jours par défaut

# ⚠️ Avertissement si la clé par défaut est utilisée
if SECRET_KEY == "clouddiagnoze-secret-key-change-this-in-production-2024":
    logger.warning("⚠️ SÉCURITÉ : Utilisation de la clé JWT par défaut ! Définissez SECRET_KEY dans .env")

# ========================================
# FONCTIONS DE HASHING DE MOT DE PASSE
# ========================================

def hash_password(password: str) -> str:
    """
    Hash un mot de passe en utilisant bcrypt.
    
    Args:
        password: Mot de passe en clair
        
    Returns:
        Mot de passe hashé
        
    Example:
        >>> hashed = hash_password("MyPassword123")
        >>> print(hashed)
        $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/1jrYK
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond au hash.
    
    Args:
        plain_password: Mot de passe en clair
        hashed_password: Mot de passe hashé
        
    Returns:
        True si le mot de passe est correct, False sinon
        
    Example:
        >>> hashed = hash_password("MyPassword123")
        >>> verify_password("MyPassword123", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


# ========================================
# FONCTIONS JWT (JSON Web Token)
# ========================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT pour l'authentification.
    
    Args:
        data: Données à encoder dans le token (ex: {"sub": "user@example.com"})
        expires_delta: Durée de validité du token (optionnel)
        
    Returns:
        Token JWT encodé
        
    Example:
        >>> token = create_access_token({"sub": "john@acme.com", "user_id": 1})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()
    
    # Définir la date d'expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Encoder le token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.info(f"🔑 Token JWT créé (expire: {expire})")
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Vérifie et décode un token JWT.
    
    Args:
        token: Token JWT à vérifier
        
    Returns:
        Données décodées du token si valide, None sinon
        
    Example:
        >>> token = create_access_token({"sub": "john@acme.com", "user_id": 1})
        >>> payload = verify_token(token)
        >>> print(payload)
        {'sub': 'john@acme.com', 'user_id': 1, 'exp': 1699123456}
    """
    try:
        # Décoder le token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        logger.info(f"✅ Token JWT valide (user: {payload.get('sub')})")
        
        return payload
        
    except JWTError as e:
        logger.warning(f"❌ Token JWT invalide: {e}")
        return None


def get_user_from_token(token: str) -> Optional[dict]:
    """
    Extrait les informations utilisateur d'un token JWT.
    
    Args:
        token: Token JWT
        
    Returns:
        Dictionnaire avec les infos utilisateur si le token est valide, None sinon
        
    Example:
        >>> token = create_access_token({"sub": "john@acme.com", "user_id": 1})
        >>> user_info = get_user_from_token(token)
        >>> print(user_info)
        {'email': 'john@acme.com', 'user_id': 1}
    """
    payload = verify_token(token)
    
    if payload is None:
        return None
    
    return {
        "email": payload.get("sub"),
        "user_id": payload.get("user_id"),
    }


# ========================================
# FONCTIONS DE RÉINITIALISATION DE MOT DE PASSE
# ========================================

def generate_reset_token() -> str:
    """
    Génère un token sécurisé pour la réinitialisation de mot de passe.
    
    Returns:
        Token aléatoire de 32 caractères hexadécimaux
        
    Example:
        >>> token = generate_reset_token()
        >>> print(token)
        a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
    """
    return secrets.token_urlsafe(32)


def create_reset_token_expiry(hours: int = 24) -> datetime:
    """
    Crée une date d'expiration pour un token de réinitialisation.
    
    Args:
        hours: Nombre d'heures de validité (défaut: 24h)
        
    Returns:
        Date d'expiration
        
    Example:
        >>> expiry = create_reset_token_expiry(24)
        >>> print(expiry)
        2024-11-05 16:30:00
    """
    return datetime.utcnow() + timedelta(hours=hours)


def is_reset_token_valid(expiry: datetime) -> bool:
    """
    Vérifie si un token de réinitialisation est encore valide.
    
    Args:
        expiry: Date d'expiration du token
        
    Returns:
        True si le token est encore valide, False sinon
        
    Example:
        >>> expiry = create_reset_token_expiry(24)
        >>> is_reset_token_valid(expiry)
        True
        >>> # 25 heures plus tard...
        >>> is_reset_token_valid(expiry)
        False
    """
    return datetime.utcnow() < expiry


# ========================================
# FONCTIONS DE VALIDATION
# ========================================

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valide la force d'un mot de passe.
    
    Règles :
    - Au moins 8 caractères
    - Au moins une lettre majuscule
    - Au moins une lettre minuscule
    - Au moins un chiffre
    
    Args:
        password: Mot de passe à valider
        
    Returns:
        Tuple (is_valid, error_message)
        
    Example:
        >>> validate_password_strength("weak")
        (False, "Le mot de passe doit contenir au moins 8 caractères")
        >>> validate_password_strength("StrongPass123")
        (True, "")
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    
    if not any(c.isupper() for c in password):
        return False, "Le mot de passe doit contenir au moins une lettre majuscule"
    
    if not any(c.islower() for c in password):
        return False, "Le mot de passe doit contenir au moins une lettre minuscule"
    
    if not any(c.isdigit() for c in password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    
    return True, ""


def validate_email(email: str) -> bool:
    """
    Valide le format d'un email (validation simple).
    
    Args:
        email: Email à valider
        
    Returns:
        True si l'email est valide, False sinon
        
    Example:
        >>> validate_email("john@acme.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# ========================================
# EXEMPLE D'UTILISATION
# ========================================

if __name__ == "__main__":
    # Test de hashing de mot de passe
    print("=== TEST HASHING ===")
    password = "MyPassword123"
    hashed = hash_password(password)
    print(f"Password: {password}")
    print(f"Hashed: {hashed}")
    print(f"Verify correct: {verify_password(password, hashed)}")
    print(f"Verify wrong: {verify_password('WrongPassword', hashed)}")
    
    # Test de JWT
    print("\n=== TEST JWT ===")
    token = create_access_token({"sub": "john@acme.com", "user_id": 1})
    print(f"Token: {token}")
    payload = verify_token(token)
    print(f"Payload: {payload}")
    user_info = get_user_from_token(token)
    print(f"User info: {user_info}")
    
    # Test de token de réinitialisation
    print("\n=== TEST RESET TOKEN ===")
    reset_token = generate_reset_token()
    print(f"Reset token: {reset_token}")
    expiry = create_reset_token_expiry(24)
    print(f"Expiry: {expiry}")
    print(f"Is valid: {is_reset_token_valid(expiry)}")
    
    # Test de validation
    print("\n=== TEST VALIDATION ===")
    print(f"Password 'weak': {validate_password_strength('weak')}")
    print(f"Password 'StrongPass123': {validate_password_strength('StrongPass123')}")
    print(f"Email 'john@acme.com': {validate_email('john@acme.com')}")
    print(f"Email 'invalid': {validate_email('invalid')}")

