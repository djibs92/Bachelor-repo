"""
Modèles ORM SQLAlchemy pour CloudDiagnoze.

Un modèle ORM = une classe Python qui représente une table SQL.
Chaque attribut de la classe = une colonne de la table.

Exemple :
    class EC2Instance(Base):
        id = Column(Integer, primary_key=True)  # Colonne 'id' de type INT
        instance_id = Column(String(50))        # Colonne 'instance_id' de type VARCHAR(50)

SQLAlchemy traduit automatiquement :
- Python → SQL : instance.save() → INSERT INTO ec2_instances ...
- SQL → Python : db.query(EC2Instance).all() → Liste d'objets Python
"""

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
    """
    Historique des exécutions de scan.

    Chaque fois qu'un scan EC2/S3/VPC est lancé, une entrée est créée ici.
    Permet de tracker quand les scans ont été exécutés et combien de ressources ont été trouvées.
    """
    __tablename__ = "scan_runs"  # Nom de la table dans MariaDB

    # Colonnes
    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID unique du scan")
    client_id = Column(String(100), nullable=False, comment="Identifiant du client (ex: ASM-Enterprise)")
    service_type = Column(Enum('ec2', 's3', 'vpc'), nullable=False, comment="Type de service scanné")
    scan_timestamp = Column(DateTime, nullable=False, default=datetime.now, comment="Date et heure du scan")
    total_resources = Column(Integer, default=0, comment="Nombre total de ressources trouvées")
    status = Column(Enum('success', 'partial', 'failed'), default='success', comment="Statut du scan")
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, comment="ID de l'utilisateur qui a lancé le scan")

    # Relations (liens avec les autres tables)
    # Un ScanRun appartient à un User
    user = relationship("User", back_populates="scan_runs")
    # Un ScanRun peut avoir plusieurs EC2Instance
    ec2_instances = relationship("EC2Instance", back_populates="scan_run", cascade="all, delete-orphan")
    # Un ScanRun peut avoir plusieurs S3Bucket
    s3_buckets = relationship("S3Bucket", back_populates="scan_run", cascade="all, delete-orphan")
    # Un ScanRun peut avoir plusieurs VPCInstance
    vpc_instances = relationship("VPCInstance", back_populates="scan_run", cascade="all, delete-orphan")
    
    def __repr__(self):
        """Représentation textuelle de l'objet (pour le debug)"""
        return f"<ScanRun(id={self.id}, client={self.client_id}, service={self.service_type}, timestamp={self.scan_timestamp})>"


# ========================================
# MODÈLE : EC2Instance
# ========================================
# Représente la table 'ec2_instances'
# Stocke toutes les métadonnées d'une instance EC2
class EC2Instance(Base):
    """
    Métadonnées des instances EC2.
    
    Chaque ligne = un snapshot d'une instance EC2 à un moment donné.
    Permet de garder l'historique des instances (création, modification, suppression).
    """
    __tablename__ = "ec2_instances"
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Clé étrangère (lien vers scan_runs)
    scan_run_id = Column(Integer, ForeignKey('scan_runs.id', ondelete='CASCADE'), nullable=False)
    
    # Identifiants
    resource_id = Column(String(255), nullable=False, comment="ARN de la ressource AWS")
    instance_id = Column(String(50), nullable=False, index=True, comment="ID de l'instance EC2 (ex: i-xxx)")
    client_id = Column(String(100), nullable=False, index=True, comment="Identifiant du client")
    
    # Configuration de l'instance
    instance_type = Column(String(50), comment="Type d'instance (ex: t3.micro)")
    state = Column(String(20), index=True, comment="État de l'instance (running, stopped, etc.)")
    ami_id = Column(String(50), comment="ID de l'AMI utilisée")
    availability_zone = Column(String(50), comment="Zone de disponibilité")
    tenancy = Column(String(20), comment="Type de tenancy (default, dedicated, host)")
    architecture = Column(String(20), comment="Architecture (x86_64, arm64)")
    virtualization_type = Column(String(20), comment="Type de virtualisation (hvm, paravirtual)")
    
    # Configuration réseau
    vpc_id = Column(String(50), comment="ID du VPC")
    subnet_id = Column(String(50), comment="ID du subnet")
    private_ip = Column(String(15), comment="Adresse IP privée")
    public_ip = Column(String(15), comment="Adresse IP publique")
    
    # Autres configurations
    iam_profile = Column(String(255), comment="Profil IAM attaché")
    root_device_name = Column(String(50), comment="Nom du device root")
    launch_time = Column(DateTime, comment="Date de lancement de l'instance")
    region = Column(String(50), index=True, comment="Région AWS (ex: eu-west-3)")
    
    # Données JSON (pour flexibilité)
    ebs_volumes = Column(JSON, comment="Liste des volumes EBS attachés")
    tags = Column(JSON, comment="Tags de l'instance")
    
    # Tracking
    scan_timestamp = Column(DateTime, nullable=False, default=datetime.now, comment="Date du scan")
    
    # Relations
    scan_run = relationship("ScanRun", back_populates="ec2_instances")
    performance = relationship("EC2Performance", back_populates="ec2_instance", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EC2Instance(id={self.id}, instance_id={self.instance_id}, type={self.instance_type}, state={self.state})>"


# ========================================
# MODÈLE : EC2Performance
# ========================================
# Représente la table 'ec2_performance'
# Stocke les métriques CloudWatch pour une instance EC2
class EC2Performance(Base):
    """
    Métriques de performance CloudWatch pour EC2.
    
    Chaque ligne = les métriques d'une instance EC2 à un moment donné.
    Lié à EC2Instance par ec2_instance_id.
    """
    __tablename__ = "ec2_performance"
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Clé étrangère (lien vers ec2_instances)
    ec2_instance_id = Column(Integer, ForeignKey('ec2_instances.id', ondelete='CASCADE'), nullable=False)
    
    # Métriques CloudWatch
    cpu_utilization_avg = Column(Float, comment="Utilisation CPU moyenne (%)")
    memory_utilization_avg = Column(Float, comment="Utilisation mémoire moyenne (%)")
    network_in_bytes = Column(BigInteger, comment="Octets reçus sur le réseau")
    network_out_bytes = Column(BigInteger, comment="Octets envoyés sur le réseau")
    
    # Relation
    ec2_instance = relationship("EC2Instance", back_populates="performance")
    
    def __repr__(self):
        return f"<EC2Performance(id={self.id}, cpu={self.cpu_utilization_avg}%, network_in={self.network_in_bytes})>"


# ========================================
# MODÈLE : S3Bucket
# ========================================
# Représente la table 's3_buckets'
# Stocke toutes les métadonnées d'un bucket S3
class S3Bucket(Base):
    """
    Métadonnées des buckets S3.
    
    Chaque ligne = un snapshot d'un bucket S3 à un moment donné.
    Permet de garder l'historique des buckets (création, modification, suppression).
    """
    __tablename__ = "s3_buckets"
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Clé étrangère (lien vers scan_runs)
    scan_run_id = Column(Integer, ForeignKey('scan_runs.id', ondelete='CASCADE'), nullable=False)
    
    # Identifiants
    resource_id = Column(String(255), nullable=False, comment="ARN du bucket S3")
    bucket_name = Column(String(255), nullable=False, index=True, comment="Nom du bucket")
    client_id = Column(String(100), nullable=False, index=True, comment="Identifiant du client")
    
    # Configuration de base
    creation_date = Column(DateTime, comment="Date de création du bucket")
    region = Column(String(50), index=True, comment="Région AWS du bucket")
    
    # Configuration de sécurité
    encryption_enabled = Column(Boolean, default=False, comment="Chiffrement activé")
    versioning_enabled = Column(Boolean, default=False, comment="Versioning activé")
    public_access_blocked = Column(Boolean, default=False, comment="Accès public bloqué")
    public_read_enabled = Column(Boolean, default=False, comment="Lecture publique activée")
    bucket_policy_enabled = Column(Boolean, default=False, comment="Politique de bucket configurée")
    
    # Configuration avancée
    lifecycle_enabled = Column(Boolean, default=False, comment="Règles de cycle de vie configurées")
    cors_enabled = Column(Boolean, default=False, comment="CORS configuré")
    website_enabled = Column(Boolean, default=False, comment="Hébergement web activé")
    logging_enabled = Column(Boolean, default=False, comment="Logging activé")
    notifications_enabled = Column(Boolean, default=False, comment="Notifications configurées")
    replication_enabled = Column(Boolean, default=False, comment="Réplication configurée")
    
    # Tracking
    scan_timestamp = Column(DateTime, nullable=False, default=datetime.now, comment="Date du scan")
    
    # Relations
    scan_run = relationship("ScanRun", back_populates="s3_buckets")
    performance = relationship("S3Performance", back_populates="s3_bucket", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<S3Bucket(id={self.id}, bucket_name={self.bucket_name}, region={self.region})>"


# ========================================
# MODÈLE : S3Performance
# ========================================
# Représente la table 's3_performance'
# Stocke les métriques CloudWatch pour un bucket S3
class S3Performance(Base):
    """
    Métriques de performance CloudWatch pour S3.
    
    Chaque ligne = les métriques d'un bucket S3 à un moment donné.
    Lié à S3Bucket par s3_bucket_id.
    """
    __tablename__ = "s3_performance"
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Clé étrangère (lien vers s3_buckets)
    s3_bucket_id = Column(Integer, ForeignKey('s3_buckets.id', ondelete='CASCADE'), nullable=False)
    
    # Métriques de requêtes
    all_requests = Column(BigInteger, comment="Nombre total de requêtes")
    get_requests = Column(BigInteger, comment="Nombre de requêtes GET")
    put_requests = Column(BigInteger, comment="Nombre de requêtes PUT")
    delete_requests = Column(BigInteger, comment="Nombre de requêtes DELETE")
    
    # Métriques d'erreurs
    errors_4xx = Column(BigInteger, comment="Nombre d'erreurs 4xx")
    errors_5xx = Column(BigInteger, comment="Nombre d'erreurs 5xx")
    
    # Métriques de latence
    first_byte_latency_avg = Column(Float, comment="Latence moyenne du premier octet (ms)")
    total_request_latency_avg = Column(Float, comment="Latence moyenne totale des requêtes (ms)")
    
    # Métriques de transfert
    bytes_downloaded = Column(BigInteger, comment="Octets téléchargés")
    bytes_uploaded = Column(BigInteger, comment="Octets uploadés")
    
    # Relation
    s3_bucket = relationship("S3Bucket", back_populates="performance")

    def __repr__(self):
        return f"<S3Performance(id={self.id}, requests={self.all_requests}, downloads={self.bytes_downloaded})>"


# ========================================
# MODÈLE : VPCInstance
# ========================================
# Représente la table 'vpc_instances'
# Stocke toutes les métadonnées d'un VPC
class VPCInstance(Base):
    """
    Métadonnées des VPCs (Virtual Private Clouds).

    Un VPC est un réseau virtuel isolé dans AWS.
    Cette table stocke toutes les informations sur chaque VPC scanné.
    """
    __tablename__ = "vpc_instances"  # Nom de la table dans MariaDB

    # Clés primaires et étrangères
    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID unique auto-incrémenté")
    scan_run_id = Column(Integer, ForeignKey('scan_runs.id', ondelete='CASCADE'), nullable=False, comment="ID du scan qui a trouvé ce VPC")

    # Identifiants
    client_id = Column(String(100), nullable=False, comment="Identifiant du client")
    vpc_id = Column(String(50), nullable=False, index=True, comment="ID du VPC (ex: vpc-0123456789abcdef0)")

    # Configuration réseau
    cidr_block = Column(String(50), comment="Bloc CIDR principal (ex: 10.0.0.0/16)")
    state = Column(String(20), index=True, comment="État du VPC (available, pending)")
    is_default = Column(Boolean, default=False, comment="VPC par défaut de la région")
    tenancy = Column(String(20), comment="Type de tenancy (default, dedicated)")

    # Subnets
    subnet_count = Column(Integer, default=0, comment="Nombre total de subnets")
    public_subnets_count = Column(Integer, default=0, comment="Nombre de subnets publics")
    private_subnets_count = Column(Integer, default=0, comment="Nombre de subnets privés")
    availability_zones = Column(JSON, comment="Liste des zones de disponibilité utilisées")

    # Gateways et routing
    internet_gateway_attached = Column(Boolean, default=False, comment="Internet Gateway attaché")
    nat_gateways_count = Column(Integer, default=0, comment="Nombre de NAT Gateways")
    route_tables_count = Column(Integer, default=0, comment="Nombre de tables de routage")

    # Sécurité
    security_groups_count = Column(Integer, default=0, comment="Nombre de Security Groups")
    network_acls_count = Column(Integer, default=0, comment="Nombre de Network ACLs")
    flow_logs_enabled = Column(Boolean, default=False, comment="VPC Flow Logs activés")

    # VPC Endpoints
    vpc_endpoints_count = Column(Integer, default=0, comment="Nombre de VPC Endpoints")

    # Peering et Transit Gateway
    vpc_peering_connections_count = Column(Integer, default=0, comment="Nombre de connexions VPC Peering")
    transit_gateway_attachments_count = Column(Integer, default=0, comment="Nombre d'attachements Transit Gateway")

    # Région et localisation
    region = Column(String(50), index=True, comment="Région AWS (ex: eu-west-1)")

    # Données JSON (pour flexibilité)
    tags = Column(JSON, comment="Tags du VPC")

    # Tracking
    scan_timestamp = Column(DateTime, nullable=False, default=datetime.now, comment="Date du scan")

    # Relations
    scan_run = relationship("ScanRun", back_populates="vpc_instances")
    performance = relationship("VPCPerformance", back_populates="vpc_instance", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<VPCInstance(id={self.id}, vpc_id={self.vpc_id}, cidr={self.cidr_block}, region={self.region})>"


# ========================================
# MODÈLE : VPCPerformance
# ========================================
# Représente la table 'vpc_performance'
# Stocke les métriques de performance d'un VPC
class VPCPerformance(Base):
    """
    Métriques de performance des VPCs.

    Stocke les métriques CloudWatch et autres indicateurs de performance.
    """
    __tablename__ = "vpc_performance"  # Nom de la table dans MariaDB

    # Clés primaires et étrangères
    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID unique auto-incrémenté")
    vpc_instance_id = Column(Integer, ForeignKey('vpc_instances.id', ondelete='CASCADE'), nullable=False, unique=True, comment="ID du VPC associé")

    # Métriques de trafic réseau (agrégées de tous les ENIs du VPC)
    network_in_bytes = Column(BigInteger, comment="Octets reçus (total)")
    network_out_bytes = Column(BigInteger, comment="Octets envoyés (total)")
    network_packets_in = Column(BigInteger, comment="Paquets reçus (total)")
    network_packets_out = Column(BigInteger, comment="Paquets envoyés (total)")

    # Métriques NAT Gateway (si présent)
    nat_gateway_bytes_in = Column(BigInteger, comment="Octets reçus via NAT Gateway")
    nat_gateway_bytes_out = Column(BigInteger, comment="Octets envoyés via NAT Gateway")
    nat_gateway_packets_in = Column(BigInteger, comment="Paquets reçus via NAT Gateway")
    nat_gateway_packets_out = Column(BigInteger, comment="Paquets envoyés via NAT Gateway")
    nat_gateway_active_connections = Column(Integer, comment="Connexions actives NAT Gateway")

    # Métriques VPN (si présent)
    vpn_tunnel_state = Column(String(20), comment="État du tunnel VPN (UP, DOWN)")
    vpn_tunnel_data_in = Column(BigInteger, comment="Données reçues via VPN")
    vpn_tunnel_data_out = Column(BigInteger, comment="Données envoyées via VPN")

    # Métriques Transit Gateway (si présent)
    transit_gateway_bytes_in = Column(BigInteger, comment="Octets reçus via Transit Gateway")
    transit_gateway_bytes_out = Column(BigInteger, comment="Octets envoyés via Transit Gateway")
    transit_gateway_packets_in = Column(BigInteger, comment="Paquets reçus via Transit Gateway")
    transit_gateway_packets_out = Column(BigInteger, comment="Paquets envoyés via Transit Gateway")

    # Relation
    vpc_instance = relationship("VPCInstance", back_populates="performance")

    def __repr__(self):
        return f"<VPCPerformance(id={self.id}, network_in={self.network_in_bytes}, network_out={self.network_out_bytes})>"

