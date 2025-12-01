"""
Tests d'intégration pour les endpoints d'authentification
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from main import app
from api.database import get_db, User
from api.database.connection import Base
from api.database import models  # Import pour que SQLAlchemy connaisse tous les modèles
from api.utils import hash_password, generate_reset_token, create_reset_token_expiry


# ========================================
# FIXTURES
# ========================================

@pytest.fixture(scope="function")
def test_db_setup():
    """
    Configure une base de données SQLite en mémoire pour les tests.
    Retourne (engine, SessionLocal).
    """
    # Importer tous les modèles pour que SQLAlchemy les connaisse
    from api.database.models import (
        User, ScanRun, EC2Instance, EC2Performance,
        S3Bucket, S3Performance, VPCInstance, VPCPerformance,
        RDSInstance, RDSPerformance
    )

    # Créer une DB SQLite en mémoire avec StaticPool pour partager entre threads
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool  # Partage la même connexion entre tous les threads
    )

    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)

    # Créer une session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield engine, TestingSessionLocal

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def client(test_db_setup):
    """
    Client de test FastAPI avec DB mockée.
    """
    engine, SessionLocal = test_db_setup

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Reset le rate limiter pour éviter les blocages entre tests
    from api.utils.limiter import limiter
    if hasattr(limiter, '_storage') and limiter._storage:
        limiter._storage.reset()
    elif hasattr(limiter, 'storage') and limiter.storage:
        limiter.storage.reset()

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_db(test_db_setup):
    """
    Retourne la session factory pour les tests qui en ont besoin.
    """
    engine, SessionLocal = test_db_setup
    return SessionLocal


@pytest.fixture
def sample_user(test_db):
    """
    Crée un utilisateur de test dans la DB.
    """
    db = test_db()
    
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123"),
        full_name="Test User",
        company_name="Test Company",
        role_arn="arn:aws:iam::123456789012:role/TestRole",
        created_at=datetime.now(),
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    
    return user


# ========================================
# TESTS : POST /api/v1/auth/signup
# ========================================

class TestSignupEndpoint:
    """Tests pour l'endpoint d'inscription"""
    
    def test_signup_success(self, client):
        """Test : Inscription réussie avec données valides"""
        # ARRANGE
        payload = {
            "email": "newuser@example.com",
            "password": "StrongPass123",
            "full_name": "New User",
            "company_name": "ACME Corp",
            "role_arn": "arn:aws:iam::123456789012:role/MyRole"
        }
        
        # ACT
        response = client.post("/api/v1/auth/signup", json=payload)
        
        # ASSERT
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "créé avec succès" in data["message"].lower()
    
    def test_signup_duplicate_email(self, client, sample_user):
        """Test : Inscription avec email déjà existant"""
        # ARRANGE
        payload = {
            "email": sample_user.email,  # Email déjà utilisé
            "password": "StrongPass123"
        }

        # ACT
        response = client.post("/api/v1/auth/signup", json=payload)

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "déjà utilisé" in data["detail"].lower()
    
    def test_signup_weak_password(self, client):
        """Test : Inscription avec mot de passe faible"""
        # ARRANGE
        payload = {
            "email": "newuser@example.com",
            "password": "weakpassword"  # 8+ caractères mais pas de majuscule ni chiffre
        }

        # ACT
        response = client.post("/api/v1/auth/signup", json=payload)

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_signup_invalid_email(self, client):
        """Test : Inscription avec email invalide"""
        # ARRANGE
        payload = {
            "email": "not-an-email",
            "password": "StrongPass123"
        }
        
        # ACT
        response = client.post("/api/v1/auth/signup", json=payload)
        
        # ASSERT
        assert response.status_code == 422  # Validation error from Pydantic


# ========================================
# TESTS : POST /api/v1/auth/login
# ========================================

class TestLoginEndpoint:
    """Tests pour l'endpoint de connexion"""

    def test_login_success(self, client, sample_user):
        """Test : Connexion réussie avec identifiants valides"""
        # ARRANGE
        payload = {
            "email": sample_user.email,
            "password": "TestPassword123"  # Mot de passe du sample_user
        }

        # ACT
        response = client.post("/api/v1/auth/login", json=payload)

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == sample_user.email

    def test_login_wrong_password(self, client, sample_user):
        """Test : Connexion avec mauvais mot de passe"""
        # ARRANGE
        payload = {
            "email": sample_user.email,
            "password": "WrongPassword123"
        }

        # ACT
        response = client.post("/api/v1/auth/login", json=payload)

        # ASSERT
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_nonexistent_user(self, client):
        """Test : Connexion avec utilisateur inexistant"""
        # ARRANGE
        payload = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123"
        }

        # ACT
        response = client.post("/api/v1/auth/login", json=payload)

        # ASSERT
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_missing_fields(self, client):
        """Test : Connexion avec champs manquants"""
        # ARRANGE
        payload = {
            "email": "test@example.com"
            # password manquant
        }

        # ACT
        response = client.post("/api/v1/auth/login", json=payload)

        # ASSERT
        assert response.status_code == 422  # Validation error


# ========================================
# TESTS : GET /api/v1/auth/me
# ========================================

class TestMeEndpoint:
    """Tests pour l'endpoint de récupération des infos utilisateur"""

    def test_get_me_success(self, client, sample_user):
        """Test : Récupération des infos utilisateur avec token valide"""
        # ARRANGE - Se connecter d'abord pour obtenir un token
        login_payload = {
            "email": sample_user.email,
            "password": "TestPassword123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_payload)
        token = login_response.json()["access_token"]

        # ACT
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user.email
        assert data["full_name"] == sample_user.full_name
        assert data["company_name"] == sample_user.company_name
        assert "id" in data
        assert "created_at" in data

    def test_get_me_no_token(self, client):
        """Test : Récupération des infos sans token"""
        # ACT
        response = client.get("/api/v1/auth/me")

        # ASSERT
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_get_me_invalid_token(self, client):
        """Test : Récupération des infos avec token invalide"""
        # ACT
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token-xyz"}
        )

        # ASSERT
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_get_me_malformed_header(self, client, sample_user):
        """Test : Récupération des infos avec header Authorization malformé"""
        # ARRANGE
        login_payload = {
            "email": sample_user.email,
            "password": "TestPassword123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_payload)
        token = login_response.json()["access_token"]

        # ACT - Header sans "Bearer"
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": token}  # Manque "Bearer "
        )

        # ASSERT
        assert response.status_code == 401


# ========================================
# TESTS : POST /api/v1/auth/forgot-password
# ========================================

class TestForgotPasswordEndpoint:
    """Tests pour l'endpoint de demande de réinitialisation de mot de passe"""

    def test_forgot_password_success(self, client, sample_user):
        """Test : Demande de réinitialisation avec email existant"""
        # ARRANGE
        payload = {
            "email": sample_user.email
        }

        # ACT
        response = client.post("/api/v1/auth/forgot-password", json=payload)

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Pour des raisons de sécurité, on retourne toujours le même message

    def test_forgot_password_nonexistent_email(self, client):
        """Test : Demande de réinitialisation avec email inexistant"""
        # ARRANGE
        payload = {
            "email": "nonexistent@example.com"
        }

        # ACT
        response = client.post("/api/v1/auth/forgot-password", json=payload)

        # ASSERT
        # Pour des raisons de sécurité, on retourne le même message
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_forgot_password_invalid_email(self, client):
        """Test : Demande de réinitialisation avec email invalide"""
        # ARRANGE
        payload = {
            "email": "not-an-email"
        }

        # ACT
        response = client.post("/api/v1/auth/forgot-password", json=payload)

        # ASSERT
        assert response.status_code == 422  # Validation error


# ========================================
# TESTS : POST /api/v1/auth/reset-password
# ========================================

class TestResetPasswordEndpoint:
    """Tests pour l'endpoint de réinitialisation de mot de passe"""

    def test_reset_password_success(self, client, test_db, sample_user):
        """Test : Réinitialisation réussie avec token valide"""
        # ARRANGE - Créer un token de réinitialisation valide
        db = test_db()
        user = db.query(User).filter(User.email == sample_user.email).first()
        user.reset_token = generate_reset_token()
        user.reset_token_expiry = create_reset_token_expiry(24)
        db.commit()
        reset_token = user.reset_token
        db.close()

        payload = {
            "token": reset_token,
            "new_password": "NewStrongPass123"
        }

        # ACT
        response = client.post("/api/v1/auth/reset-password", json=payload)

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Vérifier qu'on peut se connecter avec le nouveau mot de passe
        login_payload = {
            "email": sample_user.email,
            "password": "NewStrongPass123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_payload)
        assert login_response.status_code == 200

    def test_reset_password_invalid_token(self, client):
        """Test : Réinitialisation avec token invalide"""
        # ARRANGE
        payload = {
            "token": "invalid-token-xyz",
            "new_password": "NewStrongPass123"
        }

        # ACT
        response = client.post("/api/v1/auth/reset-password", json=payload)

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_reset_password_expired_token(self, client, test_db, sample_user):
        """Test : Réinitialisation avec token expiré"""
        # ARRANGE - Créer un token expiré
        db = test_db()
        user = db.query(User).filter(User.email == sample_user.email).first()
        user.reset_token = generate_reset_token()
        user.reset_token_expiry = datetime.now() - timedelta(hours=1)  # Expiré il y a 1h
        db.commit()
        reset_token = user.reset_token
        db.close()

        payload = {
            "token": reset_token,
            "new_password": "NewStrongPass123"
        }

        # ACT
        response = client.post("/api/v1/auth/reset-password", json=payload)

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "expiré" in data["detail"].lower()

    def test_reset_password_weak_password(self, client, test_db, sample_user):
        """Test : Réinitialisation avec mot de passe faible"""
        # ARRANGE
        db = test_db()
        user = db.query(User).filter(User.email == sample_user.email).first()
        user.reset_token = generate_reset_token()
        user.reset_token_expiry = create_reset_token_expiry(24)
        db.commit()
        reset_token = user.reset_token
        db.close()

        payload = {
            "token": reset_token,
            "new_password": "weakpassword"  # 8+ caractères mais pas de majuscule ni chiffre
        }

        # ACT
        response = client.post("/api/v1/auth/reset-password", json=payload)

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

