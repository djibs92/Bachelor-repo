"""
Script pour créer la table users dans la base de données.
"""

from api.database.connection import engine, Base
from api.database.models import User
from loguru import logger

def create_users_table():
    """Crée la table users dans la base de données"""
    try:
        logger.info("📊 Création de la table 'users'...")
        
        # Créer toutes les tables définies dans Base.metadata
        # (cela créera uniquement les tables qui n'existent pas encore)
        Base.metadata.create_all(bind=engine)
        
        logger.success("✅ Table 'users' créée avec succès !")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de la table 'users': {e}")
        raise

if __name__ == "__main__":
    create_users_table()

