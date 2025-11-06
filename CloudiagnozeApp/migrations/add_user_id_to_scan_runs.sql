-- Migration: Ajouter user_id à la table scan_runs pour l'isolation des comptes
-- Date: 2025-11-04
-- Description: Ajoute une colonne user_id (Foreign Key vers users) pour lier chaque scan à un utilisateur

-- 1. Ajouter la colonne user_id (nullable temporairement pour les scans existants)
ALTER TABLE scan_runs
ADD COLUMN user_id INT NULL COMMENT 'ID de l\'utilisateur qui a lancé le scan';

-- 2. Ajouter la contrainte de clé étrangère
ALTER TABLE scan_runs
ADD CONSTRAINT fk_scan_runs_user_id
FOREIGN KEY (user_id) REFERENCES users(id)
ON DELETE CASCADE;

-- 3. Créer un index pour améliorer les performances des requêtes filtrées par user_id
CREATE INDEX idx_scan_runs_user_id ON scan_runs(user_id);

-- 4. (Optionnel) Si vous voulez rendre user_id obligatoire après avoir migré les données existantes :
-- ALTER TABLE scan_runs MODIFY COLUMN user_id INT NOT NULL;

-- Note: Les scans existants auront user_id = NULL
-- Vous pouvez les assigner à un utilisateur spécifique avec :
-- UPDATE scan_runs SET user_id = 1 WHERE user_id IS NULL;

