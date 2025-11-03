"""
Configuration de la connexion à la base de données MariaDB.

Ce fichier gère :
- La création de l'engine SQLAlchemy (moteur de connexion)
- La création des sessions (pour interagir avec la BDD)
- Le chargement des variables d'environnement (.env)
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from loguru import logger

# ========================================
# CHARGEMENT DES VARIABLES D'ENVIRONNEMENT
# ========================================
# Charge les variables depuis le fichier .env à la racine du projet
# Remonte de 3 niveaux : api/database/connection.py -> racine
env_path = os.path.join(os.path.dirname(__file__), "../../../.env")
load_dotenv(env_path)

# ========================================
# RÉCUPÉRATION DES CREDENTIALS
# ========================================
# Ces valeurs viennent du fichier .env
DB_HOST = os.getenv("DB_HOST", "localhost")  # Par défaut localhost (Docker expose le port 3306)
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "clouddiagnoze")
DB_USER = os.getenv("DB_USER", "clouddiagnoze_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ========================================
# CONSTRUCTION DE L'URL DE CONNEXION
# ========================================
# Format : mysql+pymysql://user:password@host:port/database
# - mysql+pymysql : Utilise le driver PyMySQL pour se connecter à MariaDB/MySQL
# - user:password : Credentials de connexion
# - host:port : Adresse du serveur (localhost:3306 pour Docker)
# - database : Nom de la base de données
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.info(f"📊 Connexion à la base de données : {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# ========================================
# CRÉATION DE L'ENGINE SQLALCHEMY
# ========================================
# L'engine est le point d'entrée pour toutes les interactions avec la BDD
# 
# Paramètres :
# - pool_pre_ping=True : Vérifie que la connexion est vivante avant de l'utiliser
#   (évite les erreurs "MySQL server has gone away")
# - pool_recycle=3600 : Recycle les connexions après 1h (évite les timeouts)
# - echo=False : Ne pas afficher les requêtes SQL dans les logs (mettre True pour debug)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Vérifie la connexion avant utilisation
    pool_recycle=3600,       # Recycle les connexions après 1h
    echo=False               # Mettre True pour voir les requêtes SQL
)

# ========================================
# CRÉATION DU SESSION MAKER
# ========================================
# SessionLocal est une "factory" qui crée des sessions
# Une session = une transaction avec la BDD
# 
# Paramètres :
# - autocommit=False : Les changements ne sont pas automatiquement sauvegardés
#   (il faut appeler session.commit() explicitement)
# - autoflush=False : Les objets ne sont pas automatiquement envoyés à la BDD
# - bind=engine : Lie la session à notre engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ========================================
# BASE POUR LES MODÈLES ORM
# ========================================
# Base est la classe parente de tous nos modèles (EC2Instance, S3Bucket, etc.)
# Tous les modèles hériteront de cette classe
Base = declarative_base()

# ========================================
# FONCTION POUR OBTENIR UNE SESSION
# ========================================
def get_db():
    """
    Générateur qui fournit une session de base de données.
    
    Utilisation typique (dans FastAPI) :
    ```python
    @app.get("/items")
    def read_items(db: Session = Depends(get_db)):
        items = db.query(Item).all()
        return items
    ```
    
    La session est automatiquement fermée après utilisation grâce au `finally`.
    """
    db = SessionLocal()
    try:
        yield db  # Fournit la session
    finally:
        db.close()  # Ferme la session (libère la connexion)


# ========================================
# FONCTION POUR TESTER LA CONNEXION
# ========================================
def test_connection():
    """
    Teste la connexion à la base de données.
    
    Returns:
        bool: True si la connexion fonctionne, False sinon
    """
    try:
        # Essaie d'exécuter une requête simple
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.success("✅ Connexion à MariaDB réussie !")
            return True
    except Exception as e:
        logger.error(f"❌ Erreur de connexion à MariaDB : {e}")
        return False


# ========================================
# FONCTION POUR CRÉER LES TABLES
# ========================================
def create_tables():
    """
    Crée toutes les tables définies dans les modèles ORM.
    
    Note : Les tables sont déjà créées par init_db.sql au démarrage de Docker.
    Cette fonction est utile si tu veux créer les tables depuis Python.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.success("✅ Tables créées avec succès !")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création des tables : {e}")

