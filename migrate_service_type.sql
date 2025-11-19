-- Migration pour agrandir la colonne service_type
-- Exécuter ce script dans MySQL pour conserver les données existantes

USE clouddiagnoze;

-- Modifier la colonne service_type pour accepter des valeurs plus longues
ALTER TABLE scan_runs 
MODIFY COLUMN service_type VARCHAR(20) NOT NULL 
COMMENT 'Type de service scanné (ec2, s3, vpc, rds, etc.)';

-- Vérifier la modification
DESCRIBE scan_runs;

