-- ========================================
-- SCRIPT D'INITIALISATION CLOUDDIAGNOZE
-- ========================================
-- Ce script est exécuté automatiquement au premier démarrage de MariaDB
-- Il crée toutes les tables nécessaires pour stocker les résultats des scans

USE clouddiagnoze;

-- ========================================
-- TABLE : scan_runs
-- ========================================
-- Stocke les informations sur chaque exécution de scan
CREATE TABLE IF NOT EXISTS scan_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id VARCHAR(100) NOT NULL COMMENT 'Identifiant du client (ex: ASM-Enterprise)',
    service_type ENUM('ec2', 's3', 'vpc') NOT NULL COMMENT 'Type de service scanné',
    scan_timestamp DATETIME NOT NULL COMMENT 'Date et heure du scan',
    total_resources INT DEFAULT 0 COMMENT 'Nombre total de ressources trouvées',
    status ENUM('success', 'partial', 'failed') DEFAULT 'success' COMMENT 'Statut du scan',
    
    INDEX idx_client_service (client_id, service_type),
    INDEX idx_timestamp (scan_timestamp)
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
-- DONNÉES DE TEST (OPTIONNEL)
-- ========================================
-- Décommenter pour insérer des données de test

-- INSERT INTO scan_runs (client_id, service_type, scan_timestamp, total_resources, status)
-- VALUES ('ASM-Enterprise', 'ec2', NOW(), 5, 'success');

-- ========================================
-- FIN DU SCRIPT
-- ========================================

