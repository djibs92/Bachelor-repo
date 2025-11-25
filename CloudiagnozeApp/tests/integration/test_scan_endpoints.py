"""
Tests d'intégration pour les endpoints de scan
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from main import app
from api.database import get_db, User, ScanRun, EC2Instance, S3Bucket, VPCInstance, RDSInstance
from api.database.connection import Base
from api.utils import hash_password, create_access_token


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


@pytest.fixture
def auth_token(sample_user):
    """
    Génère un token JWT pour l'utilisateur de test.
    """
    token = create_access_token({"sub": sample_user.email, "user_id": sample_user.id})
    return token


@pytest.fixture
def auth_headers(auth_token):
    """
    Headers d'authentification avec token JWT.
    """
    return {"Authorization": f"Bearer {auth_token}"}


# ========================================
# TESTS
# ========================================

class TestCreateScanEndpoint:
    """Tests pour POST /api/v1/scans"""
    
    @patch("api.endpoints.scan.scan_list_service")
    def test_create_scan_success(self, mock_scan_service, client, auth_headers):
        """Test : Création de scan réussie"""
        # ARRANGE
        payload = {
            "provider": "aws",
            "services": ["ec2", "s3"],
            "auth_mode": {
                "type": "sts",
                "role_arn": "arn:aws:iam::123456789012:role/TestRole"
            },
            "client_id": "test-client-123",
            "regions": ["us-east-1", "eu-west-1"]
        }
        
        # ACT
        response = client.post("/api/v1/scans", json=payload, headers=auth_headers)

        # ASSERT
        assert response.status_code == 202
        data = response.json()
        assert "scan_id" in data
        assert data["scan_id"].startswith("scan-")
        assert data["status"] == "QUEUED"
        assert "message" in data

        # Vérifier que le service a été appelé
        mock_scan_service.assert_called_once()

    def test_create_scan_invalid_provider(self, client, auth_headers):
        """Test : Provider invalide"""
        # ARRANGE
        payload = {
            "provider": "azure",  # Provider non supporté
            "services": ["ec2"],
            "auth_mode": {
                "type": "sts",
                "role_arn": "arn:aws:iam::123456789012:role/TestRole"
            },
            "client_id": "test-client-123"
        }

        # ACT
        response = client.post("/api/v1/scans", json=payload, headers=auth_headers)

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "INVALID_PROVIDER"

    def test_create_scan_invalid_services(self, client, auth_headers):
        """Test : Services invalides"""
        # ARRANGE
        payload = {
            "provider": "aws",
            "services": ["ec2", "lambda", "invalid-service"],  # lambda et invalid-service non supportés
            "auth_mode": {
                "type": "sts",
                "role_arn": "arn:aws:iam::123456789012:role/TestRole"
            },
            "client_id": "test-client-123"
        }

        # ACT
        response = client.post("/api/v1/scans", json=payload, headers=auth_headers)

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "INVALID_SERVICES"

    def test_create_scan_invalid_auth_mode(self, client, auth_headers):
        """Test : Mode d'authentification invalide"""
        # ARRANGE
        payload = {
            "provider": "aws",
            "services": ["ec2"],
            "auth_mode": {
                "type": "invalid_auth",  # Mode non supporté
                "role_arn": "arn:aws:iam::123456789012:role/TestRole"
            },
            "client_id": "test-client-123"
        }

        # ACT
        response = client.post("/api/v1/scans", json=payload, headers=auth_headers)

        # ASSERT
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "INVALID_AUTH_MODE"

    def test_create_scan_no_auth(self, client):
        """Test : Création de scan sans authentification"""
        # ARRANGE
        payload = {
            "provider": "aws",
            "services": ["ec2"],
            "auth_mode": {
                "type": "sts",
                "role_arn": "arn:aws:iam::123456789012:role/TestRole"
            },
            "client_id": "test-client-123"
        }

        # ACT
        response = client.post("/api/v1/scans", json=payload)

        # ASSERT
        assert response.status_code == 401


class TestExportScanEndpoint:
    """Tests pour GET /api/v1/scans/{scan_session_id}/export"""

    def test_export_scan_success(self, client, auth_headers, test_db, sample_user):
        """Test : Export de scan réussi"""
        # ARRANGE - Créer un scan avec des ressources
        db = test_db()

        # Créer un scan run
        scan_run = ScanRun(
            client_id="test-client-123",
            service_type="ec2",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=1,
            user_id=sample_user.id
        )
        db.add(scan_run)
        db.commit()
        db.refresh(scan_run)
        scan_run_id = scan_run.id  # Sauvegarder l'ID avant de fermer la session

        # Créer une instance EC2
        ec2_instance = EC2Instance(
            scan_run_id=scan_run.id,
            resource_id="i-123456",
            instance_id="i-123456",
            client_id="test-client",
            instance_type="t2.micro",
            state="running",
            region="us-east-1",
            scan_timestamp=datetime.now()
        )
        db.add(ec2_instance)
        db.commit()
        db.close()

        # ACT
        response = client.get(f"/api/v1/scans/{scan_run_id}/export", headers=auth_headers)

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "export_info" in data
        assert "scans" in data
        assert "resources" in data
        assert "summary" in data
        assert data["export_info"]["scan_session_id"] == str(scan_run_id)
        assert data["export_info"]["user_id"] == sample_user.id
        assert len(data["resources"]["ec2_instances"]) == 1
        assert data["summary"]["total_resources"] == 1

    def test_export_scan_not_found(self, client, auth_headers):
        """Test : Export d'un scan inexistant"""
        # ACT
        response = client.get("/api/v1/scans/99999/export", headers=auth_headers)

        # ASSERT
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_export_scan_no_auth(self, client, test_db, sample_user):
        """Test : Export sans authentification"""
        # ARRANGE - Créer un scan
        db = test_db()
        scan_run = ScanRun(
            client_id="test-client-456",
            service_type="ec2",
            status="success",
            scan_timestamp=datetime.now(),
            user_id=sample_user.id
        )
        db.add(scan_run)
        db.commit()
        db.refresh(scan_run)
        scan_run_id = scan_run.id  # Sauvegarder l'ID avant de fermer la session
        db.close()

        # ACT
        response = client.get(f"/api/v1/scans/{scan_run_id}/export")

        # ASSERT
        assert response.status_code == 401

    def test_export_scan_isolation(self, client, test_db, sample_user):
        """Test : Isolation - Un utilisateur ne peut pas accéder aux scans d'un autre"""
        # ARRANGE - Créer un autre utilisateur
        db = test_db()

        other_user = User(
            email="other@example.com",
            password_hash=hash_password("OtherPassword123"),
            full_name="Other User",
            created_at=datetime.now(),
            is_active=True
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Créer un scan pour l'autre utilisateur
        scan_run = ScanRun(
            client_id="test-client-789",
            service_type="ec2",
            status="success",
            scan_timestamp=datetime.now(),
            user_id=other_user.id  # Scan appartient à other_user
        )
        db.add(scan_run)
        db.commit()
        db.refresh(scan_run)
        scan_run_id = scan_run.id  # Sauvegarder l'ID avant de fermer la session
        db.close()

        # Créer un token pour sample_user (pas other_user)
        token = create_access_token({"sub": sample_user.email, "user_id": sample_user.id})
        headers = {"Authorization": f"Bearer {token}"}

        # ACT - sample_user essaie d'accéder au scan de other_user
        response = client.get(f"/api/v1/scans/{scan_run_id}/export", headers=headers)

        # ASSERT
        assert response.status_code == 404  # Not found (car isolation par user_id)
        data = response.json()
        assert "detail" in data
        # Le message peut être "Scan session not found or access denied" ou similaire
        assert "not found" in data["detail"].lower() or "non trouvé" in data["detail"].lower()


