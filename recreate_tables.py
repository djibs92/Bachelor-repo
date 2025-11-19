"""
Script pour recréer les tables de la base de données.
ATTENTION : Ce script supprime toutes les données existantes !
"""
import sys
sys.path.insert(0, 'CloudiagnozeApp')

from api.database.connection import engine
from api.database.models import Base
from loguru import logger

logger.info("⚠️  ATTENTION : Ce script va supprimer toutes les tables et les recréer !")
logger.info("📊 Suppression des tables existantes...")

# Supprimer toutes les tables
Base.metadata.drop_all(bind=engine)
logger.success("✅ Tables supprimées")

logger.info("📊 Création des nouvelles tables...")
# Recréer toutes les tables
Base.metadata.create_all(bind=engine)
logger.success("✅ Tables créées avec succès !")

logger.info("✨ Migration terminée !")

