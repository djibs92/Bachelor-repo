-- Migration : Ajouter 'running' au statut des scans
-- Date : 2025-11-25
-- Description : Permet de tracker les scans en cours d'exécution

-- Modifier la colonne status pour ajouter 'running'
ALTER TABLE scan_runs 
MODIFY COLUMN status ENUM('running', 'success', 'partial', 'failed') DEFAULT 'running' 
COMMENT 'Statut du scan';

-- Vérification
SELECT COLUMN_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'scan_runs' 
AND COLUMN_NAME = 'status';

