-- ========================================
-- SCRIPT D'INITIALISATION CLOUDDIAGNOZE
-- ========================================
-- Ce script est exécuté automatiquement au premier démarrage de MariaDB
-- Il crée toutes les tables nécessaires pour stocker les résultats des scans
-- Note: Le script s'exécute automatiquement dans la base définie par MYSQL_DATABASE

-- ========================================
-- TABLE : users
-- ========================================
-- Stocke les informations des utilisateurs de l'application
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE COMMENT 'Email de l utilisateur (unique)',
    password_hash VARCHAR(255) NOT NULL COMMENT 'Mot de passe hashé (bcrypt)',
    full_name VARCHAR(255) COMMENT 'Nom complet de l utilisateur',
    company_name VARCHAR(255) COMMENT 'Nom de l entreprise',
    role_arn VARCHAR(255) COMMENT 'Role ARN AWS pour les scans (optionnel)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Date de création du compte',
    last_login DATETIME COMMENT 'Date de dernière connexion',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Compte actif ou désactivé',
    reset_token VARCHAR(255) COMMENT 'Token pour réinitialisation du mot de passe',
    reset_token_expiry DATETIME COMMENT 'Date d expiration du token de réinitialisation',

    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Utilisateurs de CloudDiagnoze';

-- ========================================
-- TABLE : scan_runs
-- ========================================
-- Stocke les informations sur chaque exécution de scan
CREATE TABLE IF NOT EXISTS scan_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(100) NOT NULL COMMENT 'Identifiant du client (ex: ASM-Enterprise)',
    service_type VARCHAR(20) NOT NULL COMMENT 'Type de service scanné (ec2, s3, vpc, rds)',
    scan_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Date et heure du scan',
    total_resources INT DEFAULT 0 COMMENT 'Nombre total de ressources trouvées',
    status ENUM('running', 'success', 'partial', 'failed') DEFAULT 'running' COMMENT 'Statut du scan',
    user_id INT COMMENT 'ID de l utilisateur qui a lancé le scan',

    INDEX idx_client_service (client_id, service_type),
    INDEX idx_timestamp (scan_timestamp),
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Historique des exécutions de scan';

-- ========================================
-- TABLE : ec2_instances
-- ========================================
-- Stocke les métadonnées des instances EC2
CREATE TABLE IF NOT EXISTS ec2_instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_run_id INT NOT NULL COMMENT 'Référence vers scan_runs',
    
    -- Identifiants
    resource_id VARCHAR(255) NOT NULL COMMENT 'ARN de la ressource AWS',
    instance_id VARCHAR(50) NOT NULL COMMENT 'ID de l\'instance EC2 (ex: i-xxx)',
    client_id VARCHAR(100) NOT NULL COMMENT 'Identifiant du client',
    
    -- Configuration de l'instance
    instance_type VARCHAR(50) COMMENT 'Type d\'instance (ex: t3.micro)',
    state VARCHAR(20) COMMENT 'État de l\'instance (running, stopped, etc.)',
    ami_id VARCHAR(50) COMMENT 'ID de l\'AMI utilisée',
    availability_zone VARCHAR(50) COMMENT 'Zone de disponibilité',
    tenancy VARCHAR(20) COMMENT 'Type de tenancy (default, dedicated, host)',
    architecture VARCHAR(20) COMMENT 'Architecture (x86_64, arm64)',
    virtualization_type VARCHAR(20) COMMENT 'Type de virtualisation (hvm, paravirtual)',
    
    -- Configuration réseau
    vpc_id VARCHAR(50) COMMENT 'ID du VPC',
    subnet_id VARCHAR(50) COMMENT 'ID du subnet',
    private_ip VARCHAR(15) COMMENT 'Adresse IP privée',
    public_ip VARCHAR(15) COMMENT 'Adresse IP publique',
    
    -- Autres configurations
    iam_profile VARCHAR(255) COMMENT 'Profil IAM attaché',
    root_device_name VARCHAR(50) COMMENT 'Nom du device root',
    launch_time DATETIME COMMENT 'Date de lancement de l\'instance',
    region VARCHAR(50) COMMENT 'Région AWS (ex: eu-west-3)',
    
    -- Données JSON (pour flexibilité)
    ebs_volumes JSON COMMENT 'Liste des volumes EBS attachés',
    tags JSON COMMENT 'Tags de l\'instance',
    
    -- Tracking
    scan_timestamp DATETIME NOT NULL COMMENT 'Date du scan',
    
    FOREIGN KEY (scan_run_id) REFERENCES scan_runs(id) ON DELETE CASCADE,
    INDEX idx_instance_id (instance_id),
    INDEX idx_client_timestamp (client_id, scan_timestamp),
    INDEX idx_region (region),
    INDEX idx_state (state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Métadonnées des instances EC2';

-- ========================================
-- TABLE : ec2_performance
-- ========================================
-- Stocke les métriques de performance CloudWatch pour EC2
CREATE TABLE IF NOT EXISTS ec2_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ec2_instance_id INT NOT NULL COMMENT 'Référence vers ec2_instances',
    
    -- Métriques CloudWatch
    cpu_utilization_avg FLOAT COMMENT 'Utilisation CPU moyenne (%)',
    memory_utilization_avg FLOAT COMMENT 'Utilisation mémoire moyenne (%)',
    network_in_bytes BIGINT COMMENT 'Octets reçus sur le réseau',
    network_out_bytes BIGINT COMMENT 'Octets envoyés sur le réseau',
    
    FOREIGN KEY (ec2_instance_id) REFERENCES ec2_instances(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Métriques de performance EC2';

-- ========================================
-- TABLE : s3_buckets
-- ========================================
-- Stocke les métadonnées des buckets S3
CREATE TABLE IF NOT EXISTS s3_buckets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_run_id INT NOT NULL COMMENT 'Référence vers scan_runs',
    
    -- Identifiants
    resource_id VARCHAR(255) NOT NULL COMMENT 'ARN du bucket S3',
    bucket_name VARCHAR(255) NOT NULL COMMENT 'Nom du bucket',
    client_id VARCHAR(100) NOT NULL COMMENT 'Identifiant du client',
    
    -- Configuration de base
    creation_date DATETIME COMMENT 'Date de création du bucket',
    region VARCHAR(50) COMMENT 'Région AWS du bucket',
    
    -- Configuration de sécurité
    encryption_enabled BOOLEAN DEFAULT FALSE COMMENT 'Chiffrement activé',
    versioning_enabled BOOLEAN DEFAULT FALSE COMMENT 'Versioning activé',
    public_access_blocked BOOLEAN DEFAULT FALSE COMMENT 'Accès public bloqué',
    public_read_enabled BOOLEAN DEFAULT FALSE COMMENT 'Lecture publique activée',
    bucket_policy_enabled BOOLEAN DEFAULT FALSE COMMENT 'Politique de bucket configurée',
    
    -- Configuration avancée
    lifecycle_enabled BOOLEAN DEFAULT FALSE COMMENT 'Règles de cycle de vie configurées',
    cors_enabled BOOLEAN DEFAULT FALSE COMMENT 'CORS configuré',
    website_enabled BOOLEAN DEFAULT FALSE COMMENT 'Hébergement web activé',
    logging_enabled BOOLEAN DEFAULT FALSE COMMENT 'Logging activé',
    notifications_enabled BOOLEAN DEFAULT FALSE COMMENT 'Notifications configurées',
    replication_enabled BOOLEAN DEFAULT FALSE COMMENT 'Réplication configurée',
    
    -- Tracking
    scan_timestamp DATETIME NOT NULL COMMENT 'Date du scan',
    
    FOREIGN KEY (scan_run_id) REFERENCES scan_runs(id) ON DELETE CASCADE,
    INDEX idx_bucket_name (bucket_name),
    INDEX idx_client_timestamp (client_id, scan_timestamp),
    INDEX idx_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Métadonnées des buckets S3';

-- ========================================
-- TABLE : s3_performance
-- ========================================
-- Stocke les métriques de performance CloudWatch pour S3
CREATE TABLE IF NOT EXISTS s3_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    s3_bucket_id INT NOT NULL COMMENT 'Référence vers s3_buckets',
    
    -- Métriques de requêtes
    all_requests BIGINT COMMENT 'Nombre total de requêtes',
    get_requests BIGINT COMMENT 'Nombre de requêtes GET',
    put_requests BIGINT COMMENT 'Nombre de requêtes PUT',
    delete_requests BIGINT COMMENT 'Nombre de requêtes DELETE',
    
    -- Métriques d'erreurs
    errors_4xx BIGINT COMMENT 'Nombre d\'erreurs 4xx',
    errors_5xx BIGINT COMMENT 'Nombre d\'erreurs 5xx',
    
    -- Métriques de latence
    first_byte_latency_avg FLOAT COMMENT 'Latence moyenne du premier octet (ms)',
    total_request_latency_avg FLOAT COMMENT 'Latence moyenne totale des requêtes (ms)',
    
    -- Métriques de transfert
    bytes_downloaded BIGINT COMMENT 'Octets téléchargés',
    bytes_uploaded BIGINT COMMENT 'Octets uploadés',
    
    FOREIGN KEY (s3_bucket_id) REFERENCES s3_buckets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Métriques de performance S3';

-- ========================================
-- TABLE : vpc_instances
-- ========================================
-- Stocke les métadonnées des VPCs
CREATE TABLE IF NOT EXISTS vpc_instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_run_id INT NOT NULL COMMENT 'Référence vers scan_runs',
    client_id VARCHAR(100) NOT NULL COMMENT 'Identifiant du client',
    vpc_id VARCHAR(50) NOT NULL COMMENT 'ID du VPC',
    cidr_block VARCHAR(50) COMMENT 'Bloc CIDR principal',
    state VARCHAR(20) COMMENT 'État du VPC',
    is_default BOOLEAN DEFAULT FALSE COMMENT 'VPC par défaut',
    tenancy VARCHAR(20) COMMENT 'Type de tenancy',
    subnet_count INT DEFAULT 0 COMMENT 'Nombre de subnets',
    public_subnets_count INT DEFAULT 0 COMMENT 'Nombre de subnets publics',
    private_subnets_count INT DEFAULT 0 COMMENT 'Nombre de subnets privés',
    availability_zones JSON COMMENT 'Zones de disponibilité',
    internet_gateway_attached BOOLEAN DEFAULT FALSE COMMENT 'Internet Gateway attaché',
    nat_gateways_count INT DEFAULT 0 COMMENT 'Nombre de NAT Gateways',
    route_tables_count INT DEFAULT 0 COMMENT 'Nombre de tables de routage',
    security_groups_count INT DEFAULT 0 COMMENT 'Nombre de Security Groups',
    network_acls_count INT DEFAULT 0 COMMENT 'Nombre de Network ACLs',
    flow_logs_enabled BOOLEAN DEFAULT FALSE COMMENT 'VPC Flow Logs activés',
    vpc_endpoints_count INT DEFAULT 0 COMMENT 'Nombre de VPC Endpoints',
    vpc_peering_connections_count INT DEFAULT 0 COMMENT 'Connexions VPC Peering',
    transit_gateway_attachments_count INT DEFAULT 0 COMMENT 'Attachements Transit Gateway',
    region VARCHAR(50) COMMENT 'Région AWS',
    tags JSON COMMENT 'Tags du VPC',
    scan_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Date du scan',

    FOREIGN KEY (scan_run_id) REFERENCES scan_runs(id) ON DELETE CASCADE,
    INDEX idx_vpc_id (vpc_id),
    INDEX idx_client_timestamp (client_id, scan_timestamp),
    INDEX idx_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Métadonnées des VPCs';

-- ========================================
-- TABLE : vpc_performance
-- ========================================
CREATE TABLE IF NOT EXISTS vpc_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vpc_instance_id INT NOT NULL UNIQUE COMMENT 'Référence vers vpc_instances',
    network_in_bytes BIGINT COMMENT 'Octets reçus',
    network_out_bytes BIGINT COMMENT 'Octets envoyés',
    network_packets_in BIGINT COMMENT 'Paquets reçus',
    network_packets_out BIGINT COMMENT 'Paquets envoyés',
    nat_gateway_bytes_in BIGINT COMMENT 'Octets reçus via NAT Gateway',
    nat_gateway_bytes_out BIGINT COMMENT 'Octets envoyés via NAT Gateway',
    nat_gateway_packets_in BIGINT COMMENT 'Paquets reçus via NAT Gateway',
    nat_gateway_packets_out BIGINT COMMENT 'Paquets envoyés via NAT Gateway',
    nat_gateway_active_connections INT COMMENT 'Connexions actives NAT Gateway',
    vpn_tunnel_state VARCHAR(20) COMMENT 'État du tunnel VPN',
    vpn_tunnel_data_in BIGINT COMMENT 'Données reçues via VPN',
    vpn_tunnel_data_out BIGINT COMMENT 'Données envoyées via VPN',
    transit_gateway_bytes_in BIGINT COMMENT 'Octets reçus via Transit Gateway',
    transit_gateway_bytes_out BIGINT COMMENT 'Octets envoyés via Transit Gateway',
    transit_gateway_packets_in BIGINT COMMENT 'Paquets reçus via Transit Gateway',
    transit_gateway_packets_out BIGINT COMMENT 'Paquets envoyés via Transit Gateway',

    FOREIGN KEY (vpc_instance_id) REFERENCES vpc_instances(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Métriques de performance VPC';

-- ========================================
-- TABLE : rds_instances
-- ========================================
CREATE TABLE IF NOT EXISTS rds_instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_run_id INT NOT NULL COMMENT 'Référence vers scan_runs',
    resource_id VARCHAR(255) NOT NULL COMMENT 'ARN de l instance RDS',
    db_instance_identifier VARCHAR(255) NOT NULL COMMENT 'Identifiant de l instance RDS',
    client_id VARCHAR(100) NOT NULL COMMENT 'Identifiant du client',
    db_instance_class VARCHAR(50) COMMENT 'Classe d instance',
    engine VARCHAR(50) COMMENT 'Moteur de base de données',
    engine_version VARCHAR(50) COMMENT 'Version du moteur',
    db_instance_status VARCHAR(50) COMMENT 'Statut de l instance',
    allocated_storage INT COMMENT 'Stockage alloué (GB)',
    storage_type VARCHAR(50) COMMENT 'Type de stockage',
    storage_encrypted BOOLEAN DEFAULT FALSE COMMENT 'Stockage chiffré',
    iops INT COMMENT 'IOPS provisionnées',
    vpc_id VARCHAR(50) COMMENT 'ID du VPC',
    db_subnet_group_name VARCHAR(255) COMMENT 'Nom du subnet group',
    availability_zone VARCHAR(50) COMMENT 'Zone de disponibilité',
    multi_az BOOLEAN DEFAULT FALSE COMMENT 'Déploiement Multi-AZ',
    publicly_accessible BOOLEAN DEFAULT FALSE COMMENT 'Accessible publiquement',
    endpoint_address VARCHAR(255) COMMENT 'Adresse de l endpoint',
    endpoint_port INT COMMENT 'Port de l endpoint',
    master_username VARCHAR(255) COMMENT 'Nom d utilisateur master',
    iam_database_authentication_enabled BOOLEAN DEFAULT FALSE COMMENT 'Authentification IAM activée',
    deletion_protection BOOLEAN DEFAULT FALSE COMMENT 'Protection contre la suppression',
    backup_retention_period INT COMMENT 'Période de rétention des backups',
    preferred_backup_window VARCHAR(50) COMMENT 'Fenêtre de backup préférée',
    preferred_maintenance_window VARCHAR(50) COMMENT 'Fenêtre de maintenance préférée',
    latest_restorable_time DATETIME COMMENT 'Dernière heure restaurable',
    auto_minor_version_upgrade BOOLEAN DEFAULT FALSE COMMENT 'Mise à jour automatique des versions mineures',
    enhanced_monitoring_resource_arn VARCHAR(255) COMMENT 'ARN Enhanced Monitoring',
    monitoring_interval INT COMMENT 'Intervalle de monitoring',
    performance_insights_enabled BOOLEAN DEFAULT FALSE COMMENT 'Performance Insights activé',
    region VARCHAR(50) COMMENT 'Région AWS',
    tags JSON COMMENT 'Tags de l instance',
    security_groups JSON COMMENT 'Security groups attachés',
    parameter_groups JSON COMMENT 'Parameter groups',
    option_groups JSON COMMENT 'Option groups',
    instance_create_time DATETIME COMMENT 'Date de création de l instance',
    scan_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Date du scan',

    FOREIGN KEY (scan_run_id) REFERENCES scan_runs(id) ON DELETE CASCADE,
    INDEX idx_db_identifier (db_instance_identifier),
    INDEX idx_client_timestamp (client_id, scan_timestamp),
    INDEX idx_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Métadonnées des instances RDS';

-- ========================================
-- TABLE : rds_performance
-- ========================================
CREATE TABLE IF NOT EXISTS rds_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rds_instance_id INT NOT NULL COMMENT 'Référence vers rds_instances',
    cpu_utilization_avg FLOAT COMMENT 'Utilisation CPU moyenne',
    freeable_memory_bytes BIGINT COMMENT 'Mémoire disponible',
    free_storage_space_bytes BIGINT COMMENT 'Espace de stockage libre',
    database_connections INT COMMENT 'Nombre de connexions',
    read_iops_avg FLOAT COMMENT 'IOPS de lecture moyennes',
    write_iops_avg FLOAT COMMENT 'IOPS d écriture moyennes',
    read_latency_avg FLOAT COMMENT 'Latence de lecture moyenne',
    write_latency_avg FLOAT COMMENT 'Latence d écriture moyenne',
    read_throughput_bytes BIGINT COMMENT 'Débit de lecture',
    write_throughput_bytes BIGINT COMMENT 'Débit d écriture',
    network_receive_throughput_bytes BIGINT COMMENT 'Débit réseau reçu',
    network_transmit_throughput_bytes BIGINT COMMENT 'Débit réseau transmis',

    FOREIGN KEY (rds_instance_id) REFERENCES rds_instances(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Métriques de performance RDS';

-- ========================================
-- FIN DU SCRIPT
-- ========================================

