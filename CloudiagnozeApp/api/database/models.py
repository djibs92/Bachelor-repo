from sqlalchemy import Column, Integer, String, DateTime, Float, BigInteger, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from api.database.connection import Base

# ========================================
# MODÈLE : User
# ========================================
# Représente la table 'users'
# Stocke les informations des utilisateurs de l'application
class User(Base):
    """
    Utilisateurs de CloudDiagnoze.

    Chaque utilisateur a un compte avec email/mot de passe.
    Il peut configurer son Role ARN AWS pour lancer des scans sur son infrastructure.
    """
    __tablename__ = "users"  # Nom de la table dans MariaDB

    # Colonnes
    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID unique de l'utilisateur")
    email = Column(String(255), unique=True, nullable=False, index=True, comment="Email de l'utilisateur (unique)")
    password_hash = Column(String(255), nullable=False, comment="Mot de passe hashé (bcrypt)")
    full_name = Column(String(255), comment="Nom complet de l'utilisateur")
    company_name = Column(String(255), comment="Nom de l'entreprise")
    role_arn = Column(String(255), comment="Role ARN AWS pour les scans (optionnel)")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="Date de création du compte")
    last_login = Column(DateTime, comment="Date de dernière connexion")
    is_active = Column(Boolean, default=True, comment="Compte actif ou désactivé")
    reset_token = Column(String(255), comment="Token pour réinitialisation du mot de passe")
    reset_token_expiry = Column(DateTime, comment="Date d'expiration du token de réinitialisation")

    # Relations
    # Un User peut avoir plusieurs ScanRun
    scan_runs = relationship("ScanRun", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', company='{self.company_name}')>"

# ========================================
# MODÈLE : ScanRun
# ========================================
# Représente la table 'scan_runs'
# Stocke les informations sur chaque exécution de scan
class ScanRun(Base):
    __tablename__ = "scan_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), nullable=True, index=True)
    client_id = Column(String(100), nullable=False)
    service_type = Column(String(20), nullable=False)
    scan_timestamp = Column(DateTime, nullable=False, default=datetime.now)
    total_resources = Column(Integer, default=0)
    status = Column(Enum('running', 'success', 'partial', 'failed'), default='running')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

    user = relationship("User", back_populates="scan_runs")
    ec2_instances = relationship("EC2Instance", back_populates="scan_run", cascade="all, delete-orphan")
    s3_buckets = relationship("S3Bucket", back_populates="scan_run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ScanRun(id={self.id}, client={self.client_id}, service={self.service_type}, timestamp={self.scan_timestamp})>"


class EC2Instance(Base):
    __tablename__ = "ec2_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_run_id = Column(Integer, ForeignKey('scan_runs.id', ondelete='CASCADE'), nullable=False)
    resource_id = Column(String(255), nullable=False)
    instance_id = Column(String(50), nullable=False, index=True)
    client_id = Column(String(100), nullable=False, index=True)
    instance_type = Column(String(50))
    state = Column(String(20), index=True)
    ami_id = Column(String(50))
    availability_zone = Column(String(50))
    tenancy = Column(String(20))
    architecture = Column(String(20))
    virtualization_type = Column(String(20))
    vpc_id = Column(String(50))
    subnet_id = Column(String(50))
    private_ip = Column(String(15))
    public_ip = Column(String(15))
    iam_profile = Column(String(255))
    root_device_name = Column(String(50))
    launch_time = Column(DateTime)
    region = Column(String(50), index=True)
    ebs_volumes = Column(JSON)
    tags = Column(JSON)
    scan_timestamp = Column(DateTime, nullable=False, default=datetime.now)

    scan_run = relationship("ScanRun", back_populates="ec2_instances")
    performance = relationship("EC2Performance", back_populates="ec2_instance", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EC2Instance(id={self.id}, instance_id={self.instance_id}, type={self.instance_type}, state={self.state})>"


class EC2Performance(Base):
    __tablename__ = "ec2_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ec2_instance_id = Column(Integer, ForeignKey('ec2_instances.id', ondelete='CASCADE'), nullable=False)
    cpu_utilization_avg = Column(Float)
    memory_utilization_avg = Column(Float)
    network_in_bytes = Column(BigInteger)
    network_out_bytes = Column(BigInteger)

    ec2_instance = relationship("EC2Instance", back_populates="performance")

    def __repr__(self):
        return f"<EC2Performance(id={self.id}, cpu={self.cpu_utilization_avg}%)>"


class S3Bucket(Base):
    __tablename__ = "s3_buckets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_run_id = Column(Integer, ForeignKey('scan_runs.id', ondelete='CASCADE'), nullable=False)
    resource_id = Column(String(255), nullable=False)
    bucket_name = Column(String(255), nullable=False, index=True)
    client_id = Column(String(100), nullable=False, index=True)
    creation_date = Column(DateTime)
    region = Column(String(50), index=True)
    encryption_enabled = Column(Boolean, default=False)
    versioning_enabled = Column(Boolean, default=False)
    public_access_blocked = Column(Boolean, default=False)
    public_read_enabled = Column(Boolean, default=False)
    bucket_policy_enabled = Column(Boolean, default=False)
    lifecycle_enabled = Column(Boolean, default=False)
    cors_enabled = Column(Boolean, default=False)
    website_enabled = Column(Boolean, default=False)
    logging_enabled = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=False)
    replication_enabled = Column(Boolean, default=False)
    scan_timestamp = Column(DateTime, nullable=False, default=datetime.now)

    scan_run = relationship("ScanRun", back_populates="s3_buckets")
    performance = relationship("S3Performance", back_populates="s3_bucket", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<S3Bucket(id={self.id}, bucket_name={self.bucket_name}, region={self.region})>"


class S3Performance(Base):
    __tablename__ = "s3_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    s3_bucket_id = Column(Integer, ForeignKey('s3_buckets.id', ondelete='CASCADE'), nullable=False)
    all_requests = Column(BigInteger)
    get_requests = Column(BigInteger)
    put_requests = Column(BigInteger)
    delete_requests = Column(BigInteger)
    errors_4xx = Column(BigInteger)
    errors_5xx = Column(BigInteger)
    first_byte_latency_avg = Column(Float)
    total_request_latency_avg = Column(Float)
    bytes_downloaded = Column(BigInteger)
    bytes_uploaded = Column(BigInteger)

    s3_bucket = relationship("S3Bucket", back_populates="performance")

    def __repr__(self):
        return f"<S3Performance(id={self.id}, requests={self.all_requests})>"

