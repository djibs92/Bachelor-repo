-- ========================================
-- CRÉATION DE LA TABLE USERS
-- ========================================
-- Cette table stocke les utilisateurs de CloudDiagnoze
-- Chaque utilisateur peut configurer son Role ARN AWS pour lancer des scans

CREATE TABLE IF NOT EXISTS users (
    -- Identifiant unique
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID unique de l\'utilisateur',
    
    -- Informations de connexion
    email VARCHAR(255) UNIQUE NOT NULL COMMENT 'Email de l\'utilisateur (unique)',
    password_hash VARCHAR(255) NOT NULL COMMENT 'Mot de passe hashé (bcrypt)',
    
    -- Informations personnelles
    full_name VARCHAR(255) COMMENT 'Nom complet de l\'utilisateur',
    company_name VARCHAR(255) COMMENT 'Nom de l\'entreprise',
    
    -- Configuration AWS
    role_arn VARCHAR(255) COMMENT 'Role ARN AWS pour les scans (optionnel)',
    
    -- Tracking
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Date de création du compte',
    last_login DATETIME COMMENT 'Date de dernière connexion',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Compte actif ou désactivé',
    
    -- Réinitialisation du mot de passe
    reset_token VARCHAR(255) COMMENT 'Token pour réinitialisation du mot de passe',
    reset_token_expiry DATETIME COMMENT 'Date d\'expiration du token de réinitialisation',
    
    -- Index pour optimiser les recherches
    INDEX idx_email (email),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Utilisateurs de CloudDiagnoze';

-- ========================================
-- DONNÉES DE TEST (OPTIONNEL)
-- ========================================
-- Mot de passe : "password123" (hashé avec bcrypt)
-- Hash généré avec : bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())

-- INSERT INTO users (email, password_hash, full_name, company_name, role_arn, is_active) VALUES
-- ('admin@clouddiagnoze.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/1jrYK', 'Admin CloudDiagnoze', 'CloudDiagnoze', 'arn:aws:iam::730335226954:role/CloudDiagnoze-ScanRole', TRUE),
-- ('john@acme.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/1jrYK', 'John Doe', 'ACME Corp', NULL, TRUE);

