"""
Module database pour CloudDiagnoze.

Ce fichier rend le dossier 'database' un module Python importable.
Il exporte les éléments principaux pour faciliter les imports.
"""

from api.database.connection import engine, SessionLocal, get_db, test_connection, create_tables
from api.database.models import User, ScanRun, EC2Instance, EC2Performance, S3Bucket, S3Performance

__all__ = [
    # Connexion
    "engine",
    "SessionLocal",
    "get_db",
    "test_connection",
    "create_tables",

    # Modèles
    "User",
    "ScanRun",
    "EC2Instance",
    "EC2Performance",
    "S3Bucket",
    "S3Performance",
]

