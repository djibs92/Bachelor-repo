"""
Script pour créer les tables VPC dans la base de données.
"""

from api.database.connection import engine, Base
from api.database.models import VPCInstance, VPCPerformance
from loguru import logger

def create_vpc_tables():
    """Crée les tables vpc_instances et vpc_performance dans la base de données"""
    try:
        logger.info("📊 Création des tables VPC...")
        
        # Créer toutes les tables définies dans Base.metadata
        # (cela créera uniquement les tables qui n'existent pas encore)
        Base.metadata.create_all(bind=engine)
        
        logger.success("✅ Tables VPC créées avec succès !")
        logger.info("   - vpc_instances")
        logger.info("   - vpc_performance")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création des tables VPC: {e}")
        raise

if __name__ == "__main__":
    create_vpc_tables()

