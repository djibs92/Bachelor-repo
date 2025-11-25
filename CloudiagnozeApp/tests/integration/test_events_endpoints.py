"""
Tests d'intégration pour les endpoints Events (récupération de données).

Endpoints testés :
- GET /api/v1/scans/history - Historique des scans
- GET /api/v1/ec2/instances - Instances EC2
- GET /api/v1/s3/buckets - Buckets S3
- GET /api/v1/vpc/instances - VPCs
- GET /api/v1/rds/instances - Instances RDS
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

from main import app
from api.database.connection import Base
from api.database import get_db, User, ScanRun, EC2Instance, S3Bucket, VPCInstance, RDSInstance
from api.utils.security import hash_password, create_access_token


# ========================================
# FIXTURES
# ========================================

@pytest.fixture
def test_db():
    """Crée une base de données SQLite en mémoire pour les tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal
    
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user(test_db):
    """Crée un utilisateur de test."""
    db = test_db()
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPassword123!"),
        full_name="Test User",
        company_name="Test Company",
        role_arn="arn:aws:iam::123456789012:role/TestRole",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    db.close()
    
    # Return a dict instead of the detached object
    return {"id": user_id, "email": "test@example.com"}


@pytest.fixture
def second_user(test_db):
    """Crée un deuxième utilisateur pour tester l'isolation."""
    db = test_db()
    user = User(
        email="other@example.com",
        password_hash=hash_password("OtherPassword123!"),
        full_name="Other User",
        company_name="Other Company",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    db.close()
    
    return {"id": user_id, "email": "other@example.com"}


@pytest.fixture
def auth_token(sample_user):
    """Génère un token JWT pour l'utilisateur de test."""
    token = create_access_token({"sub": sample_user["email"], "user_id": sample_user["id"]})
    return token


@pytest.fixture
def second_auth_token(second_user):
    """Génère un token JWT pour le deuxième utilisateur."""
    token = create_access_token({"sub": second_user["email"], "user_id": second_user["id"]})
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Headers d'authentification pour les requêtes."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def second_auth_headers(second_auth_token):
    """Headers d'authentification pour le deuxième utilisateur."""
    return {"Authorization": f"Bearer {second_auth_token}"}


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


# ========================================
# TESTS : GET /scans/history
# ========================================

class TestScansHistoryEndpoint:
    """Tests pour l'endpoint GET /scans/history"""
    
    def test_get_scans_history_success(self, client, auth_headers, test_db, sample_user):
        """Test : Récupération de l'historique des scans"""
        db = test_db()

        # Créer 3 scans pour l'utilisateur
        for i in range(3):
            scan = ScanRun(
                client_id=f"test-client-{i}",
                service_type="ec2",
                status="success",
                scan_timestamp=datetime.now(),
                total_resources=10 + i,
                user_id=sample_user["id"]
            )
            db.add(scan)
        db.commit()
        db.close()

        response = client.get("/api/v1/scans/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_scans" in data
        assert "scans" in data
        assert data["total_scans"] == 3
        assert len(data["scans"]) == 3

    def test_get_scans_history_filter_by_service(self, client, auth_headers, test_db, sample_user):
        """Test : Filtrage par type de service"""
        db = test_db()

        # Créer des scans de différents types
        for service in ["ec2", "s3", "vpc"]:
            scan = ScanRun(
                client_id="test-client",
                service_type=service,
                status="success",
                scan_timestamp=datetime.now(),
                total_resources=5,
                user_id=sample_user["id"]
            )
            db.add(scan)
        db.commit()
        db.close()

        response = client.get("/api/v1/scans/history?service_type=ec2", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 1
        assert data["scans"][0]["service_type"] == "ec2"

    def test_get_scans_history_isolation(self, client, auth_headers, second_auth_headers, test_db, sample_user, second_user):
        """Test : Isolation entre utilisateurs"""
        db = test_db()

        # Créer un scan pour chaque utilisateur
        scan1 = ScanRun(
            client_id="user1-client",
            service_type="ec2",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=5,
            user_id=sample_user["id"]
        )
        scan2 = ScanRun(
            client_id="user2-client",
            service_type="s3",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=10,
            user_id=second_user["id"]
        )
        db.add(scan1)
        db.add(scan2)
        db.commit()
        db.close()

        # User 1 ne doit voir que son scan
        response = client.get("/api/v1/scans/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 1
        assert data["scans"][0]["client_id"] == "user1-client"

        # User 2 ne doit voir que son scan
        response = client.get("/api/v1/scans/history", headers=second_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 1
        assert data["scans"][0]["client_id"] == "user2-client"

    def test_get_scans_history_no_auth(self, client):
        """Test : Sans authentification"""
        response = client.get("/api/v1/scans/history")
        assert response.status_code == 401


# ========================================
# TESTS : GET /ec2/instances
# ========================================

class TestEC2InstancesEndpoint:
    """Tests pour l'endpoint GET /ec2/instances"""

    def test_get_ec2_instances_success(self, client, auth_headers, test_db, sample_user):
        """Test : Récupération des instances EC2"""
        db = test_db()

        # Créer un scan
        scan = ScanRun(
            client_id="test-client",
            service_type="ec2",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=2,
            user_id=sample_user["id"]
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Créer 2 instances EC2
        for i in range(2):
            instance = EC2Instance(
                scan_run_id=scan.id,
                resource_id=f"i-{i}23456",
                instance_id=f"i-{i}23456",
                client_id="test-client",
                instance_type="t2.micro",
                state="running",
                region="us-east-1",
                scan_timestamp=datetime.now()
            )
            db.add(instance)
        db.commit()
        db.close()

        response = client.get("/api/v1/ec2/instances", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_instances" in data
        assert "instances" in data
        assert data["total_instances"] == 2

    def test_get_ec2_instances_filter_by_region(self, client, auth_headers, test_db, sample_user):
        """Test : Filtrage par région"""
        db = test_db()

        # Créer un scan
        scan = ScanRun(
            client_id="test-client",
            service_type="ec2",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=2,
            user_id=sample_user["id"]
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Créer des instances dans différentes régions
        for region in ["us-east-1", "eu-west-1"]:
            instance = EC2Instance(
                scan_run_id=scan.id,
                resource_id=f"i-{region}",
                instance_id=f"i-{region}",
                client_id="test-client",
                instance_type="t2.micro",
                state="running",
                region=region,
                scan_timestamp=datetime.now()
            )
            db.add(instance)
        db.commit()
        db.close()

        response = client.get("/api/v1/ec2/instances?region=us-east-1", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_instances"] == 1
        assert data["instances"][0]["region"] == "us-east-1"

    def test_get_ec2_instances_isolation(self, client, auth_headers, second_auth_headers, test_db, sample_user, second_user):
        """Test : Isolation entre utilisateurs"""
        db = test_db()

        # Créer un scan pour chaque utilisateur
        scan1 = ScanRun(
            client_id="user1-client",
            service_type="ec2",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=1,
            user_id=sample_user["id"]
        )
        scan2 = ScanRun(
            client_id="user2-client",
            service_type="ec2",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=1,
            user_id=second_user["id"]
        )
        db.add(scan1)
        db.add(scan2)
        db.commit()
        db.refresh(scan1)
        db.refresh(scan2)

        # Créer une instance pour chaque utilisateur
        instance1 = EC2Instance(
            scan_run_id=scan1.id,
            resource_id="i-user1",
            instance_id="i-user1",
            client_id="user1-client",
            instance_type="t2.micro",
            state="running",
            region="us-east-1",
            scan_timestamp=datetime.now()
        )
        instance2 = EC2Instance(
            scan_run_id=scan2.id,
            resource_id="i-user2",
            instance_id="i-user2",
            client_id="user2-client",
            instance_type="t2.small",
            state="stopped",
            region="eu-west-1",
            scan_timestamp=datetime.now()
        )
        db.add(instance1)
        db.add(instance2)
        db.commit()
        db.close()

        # User 1 ne doit voir que ses instances
        response = client.get("/api/v1/ec2/instances", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_instances"] == 1
        assert data["instances"][0]["instance_id"] == "i-user1"

        # User 2 ne doit voir que ses instances
        response = client.get("/api/v1/ec2/instances", headers=second_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_instances"] == 1
        assert data["instances"][0]["instance_id"] == "i-user2"

    def test_get_ec2_instances_no_auth(self, client):
        """Test : Sans authentification"""
        response = client.get("/api/v1/ec2/instances")
        assert response.status_code == 401


# ========================================
# TESTS : GET /s3/buckets
# ========================================

class TestS3BucketsEndpoint:
    """Tests pour l'endpoint GET /s3/buckets"""

    def test_get_s3_buckets_success(self, client, auth_headers, test_db, sample_user):
        """Test : Récupération des buckets S3"""
        db = test_db()

        # Créer un scan
        scan = ScanRun(
            client_id="test-client",
            service_type="s3",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=2,
            user_id=sample_user["id"]
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Créer 2 buckets S3
        for i in range(2):
            bucket = S3Bucket(
                scan_run_id=scan.id,
                resource_id=f"bucket-{i}",
                bucket_name=f"test-bucket-{i}",
                client_id="test-client",
                region="us-east-1",
                scan_timestamp=datetime.now()
            )
            db.add(bucket)
        db.commit()
        db.close()

        response = client.get("/api/v1/s3/buckets", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_buckets" in data
        assert "buckets" in data
        assert data["total_buckets"] == 2

    def test_get_s3_buckets_isolation(self, client, auth_headers, second_auth_headers, test_db, sample_user, second_user):
        """Test : Isolation entre utilisateurs"""
        db = test_db()

        # Créer un scan pour chaque utilisateur
        scan1 = ScanRun(
            client_id="user1-client",
            service_type="s3",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=1,
            user_id=sample_user["id"]
        )
        scan2 = ScanRun(
            client_id="user2-client",
            service_type="s3",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=1,
            user_id=second_user["id"]
        )
        db.add(scan1)
        db.add(scan2)
        db.commit()
        db.refresh(scan1)
        db.refresh(scan2)

        # Créer un bucket pour chaque utilisateur
        bucket1 = S3Bucket(
            scan_run_id=scan1.id,
            resource_id="bucket-user1",
            bucket_name="user1-bucket",
            client_id="user1-client",
            region="us-east-1",
            scan_timestamp=datetime.now()
        )
        bucket2 = S3Bucket(
            scan_run_id=scan2.id,
            resource_id="bucket-user2",
            bucket_name="user2-bucket",
            client_id="user2-client",
            region="eu-west-1",
            scan_timestamp=datetime.now()
        )
        db.add(bucket1)
        db.add(bucket2)
        db.commit()
        db.close()

        # User 1 ne doit voir que ses buckets
        response = client.get("/api/v1/s3/buckets", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_buckets"] == 1
        assert data["buckets"][0]["bucket_name"] == "user1-bucket"

        # User 2 ne doit voir que ses buckets
        response = client.get("/api/v1/s3/buckets", headers=second_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_buckets"] == 1
        assert data["buckets"][0]["bucket_name"] == "user2-bucket"

    def test_get_s3_buckets_no_auth(self, client):
        """Test : Sans authentification"""
        response = client.get("/api/v1/s3/buckets")
        assert response.status_code == 401


# ========================================
# TESTS : GET /vpc/instances
# ========================================

class TestVPCInstancesEndpoint:
    """Tests pour l'endpoint GET /vpc/instances"""

    def test_get_vpc_instances_success(self, client, auth_headers, test_db, sample_user):
        """Test : Récupération des VPCs"""
        db = test_db()

        # Créer un scan
        scan = ScanRun(
            client_id="test-client",
            service_type="vpc",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=2,
            user_id=sample_user["id"]
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Créer 2 VPCs
        for i in range(2):
            vpc = VPCInstance(
                scan_run_id=scan.id,
                client_id="test-client",
                vpc_id=f"vpc-{i}23456",
                cidr_block=f"10.{i}.0.0/16",
                state="available",
                region="us-east-1",
                scan_timestamp=datetime.now()
            )
            db.add(vpc)
        db.commit()
        db.close()

        response = client.get("/api/v1/vpc/instances", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_vpcs" in data
        assert "vpcs" in data
        assert data["total_vpcs"] == 2

    def test_get_vpc_instances_isolation(self, client, auth_headers, second_auth_headers, test_db, sample_user, second_user):
        """Test : Isolation entre utilisateurs"""
        db = test_db()

        # Créer un scan pour chaque utilisateur
        scan1 = ScanRun(
            client_id="user1-client",
            service_type="vpc",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=1,
            user_id=sample_user["id"]
        )
        scan2 = ScanRun(
            client_id="user2-client",
            service_type="vpc",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=1,
            user_id=second_user["id"]
        )
        db.add(scan1)
        db.add(scan2)
        db.commit()
        db.refresh(scan1)
        db.refresh(scan2)

        # Créer un VPC pour chaque utilisateur
        vpc1 = VPCInstance(
            scan_run_id=scan1.id,
            client_id="user1-client",
            vpc_id="vpc-user1",
            cidr_block="10.0.0.0/16",
            state="available",
            region="us-east-1",
            scan_timestamp=datetime.now()
        )
        vpc2 = VPCInstance(
            scan_run_id=scan2.id,
            client_id="user2-client",
            vpc_id="vpc-user2",
            cidr_block="10.1.0.0/16",
            state="available",
            region="eu-west-1",
            scan_timestamp=datetime.now()
        )
        db.add(vpc1)
        db.add(vpc2)
        db.commit()
        db.close()

        # User 1 ne doit voir que ses VPCs
        response = client.get("/api/v1/vpc/instances", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_vpcs"] == 1
        assert data["vpcs"][0]["vpc_id"] == "vpc-user1"

        # User 2 ne doit voir que ses VPCs
        response = client.get("/api/v1/vpc/instances", headers=second_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_vpcs"] == 1
        assert data["vpcs"][0]["vpc_id"] == "vpc-user2"

    def test_get_vpc_instances_no_auth(self, client):
        """Test : Sans authentification"""
        response = client.get("/api/v1/vpc/instances")
        assert response.status_code == 401


# ========================================
# TESTS : GET /rds/instances
# ========================================

class TestRDSInstancesEndpoint:
    """Tests pour l'endpoint GET /rds/instances"""

    def test_get_rds_instances_success(self, client, auth_headers, test_db, sample_user):
        """Test : Récupération des instances RDS"""
        db = test_db()

        # Créer un scan
        scan = ScanRun(
            client_id="test-client",
            service_type="rds",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=2,
            user_id=sample_user["id"]
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Créer 2 instances RDS
        for i in range(2):
            rds = RDSInstance(
                scan_run_id=scan.id,
                resource_id=f"db-{i}",
                db_instance_identifier=f"test-db-{i}",
                client_id="test-client",
                db_instance_class="db.t3.micro",
                engine="mysql",
                region="us-east-1",
                scan_timestamp=datetime.now()
            )
            db.add(rds)
        db.commit()
        db.close()

        response = client.get("/api/v1/rds/instances", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_instances" in data
        assert "instances" in data
        assert data["total_instances"] == 2

    def test_get_rds_instances_isolation(self, client, auth_headers, second_auth_headers, test_db, sample_user, second_user):
        """Test : Isolation entre utilisateurs"""
        db = test_db()

        # Créer un scan pour chaque utilisateur
        scan1 = ScanRun(
            client_id="user1-client",
            service_type="rds",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=1,
            user_id=sample_user["id"]
        )
        scan2 = ScanRun(
            client_id="user2-client",
            service_type="rds",
            status="success",
            scan_timestamp=datetime.now(),
            total_resources=1,
            user_id=second_user["id"]
        )
        db.add(scan1)
        db.add(scan2)
        db.commit()
        db.refresh(scan1)
        db.refresh(scan2)

        # Créer une instance RDS pour chaque utilisateur
        rds1 = RDSInstance(
            scan_run_id=scan1.id,
            resource_id="db-user1",
            db_instance_identifier="user1-db",
            client_id="user1-client",
            db_instance_class="db.t3.micro",
            engine="mysql",
            region="us-east-1",
            scan_timestamp=datetime.now()
        )
        rds2 = RDSInstance(
            scan_run_id=scan2.id,
            resource_id="db-user2",
            db_instance_identifier="user2-db",
            client_id="user2-client",
            db_instance_class="db.t3.small",
            engine="postgres",
            region="eu-west-1",
            scan_timestamp=datetime.now()
        )
        db.add(rds1)
        db.add(rds2)
        db.commit()
        db.close()

        # User 1 ne doit voir que ses instances
        response = client.get("/api/v1/rds/instances", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_instances"] == 1
        assert data["instances"][0]["db_instance_identifier"] == "user1-db"

        # User 2 ne doit voir que ses instances
        response = client.get("/api/v1/rds/instances", headers=second_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_instances"] == 1
        assert data["instances"][0]["db_instance_identifier"] == "user2-db"

    def test_get_rds_instances_no_auth(self, client):
        """Test : Sans authentification"""
        response = client.get("/api/v1/rds/instances")
        assert response.status_code == 401

