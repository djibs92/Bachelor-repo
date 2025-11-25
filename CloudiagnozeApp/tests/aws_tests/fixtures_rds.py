"""
Fixtures pytest pour les tests du scanner RDS
"""
import pytest
import boto3
from moto import mock_aws
from faker import Faker
from datetime import datetime


@pytest.fixture
def rds_client():
    """Client RDS mocké pour les tests"""
    def _create_client(region='us-east-1'):
        return boto3.client('rds', region_name=region)
    return _create_client


@pytest.fixture
def cloudwatch_client():
    """Client CloudWatch mocké pour les tests RDS"""
    def _create_client(region='us-east-1'):
        return boto3.client('cloudwatch', region_name=region)
    return _create_client


@pytest.fixture
def create_rds_instance(faker_instance: Faker):
    """
    Factory fixture pour créer une instance RDS mockée.
    
    Usage:
        db_id = create_rds_instance(region='us-east-1', engine='postgres')
    """
    def _create_instance(
        region='us-east-1',
        db_identifier=None,
        db_instance_class='db.t3.micro',
        engine='postgres',
        engine_version='14.7',
        master_username='admin',
        master_password='password123',
        allocated_storage=20,
        storage_type='gp2',
        storage_encrypted=False,
        multi_az=False,
        publicly_accessible=False,
        backup_retention_period=7,
        deletion_protection=False,
        performance_insights=False,
        tags=None
    ):
        """
        Crée une instance RDS mockée.
        
        Args:
            region: Région AWS
            db_identifier: Identifiant de l'instance
            db_instance_class: Classe d'instance (db.t3.micro, db.m5.large, etc.)
            engine: Moteur de base de données (postgres, mysql, mariadb, etc.)
            engine_version: Version du moteur
            master_username: Nom d'utilisateur master
            master_password: Mot de passe master
            allocated_storage: Stockage alloué en GB
            storage_type: Type de stockage (gp2, io1, etc.)
            storage_encrypted: Chiffrement du stockage
            multi_az: Déploiement multi-AZ
            publicly_accessible: Accessible publiquement
            backup_retention_period: Période de rétention des backups
            deletion_protection: Protection contre la suppression
            performance_insights: Performance Insights activé
            tags: Dictionnaire de tags
        
        Returns:
            db_identifier: Identifiant de l'instance créée
        """
        rds_client = boto3.client('rds', region_name=region)
        
        # Générer un identifiant unique si non fourni
        if not db_identifier:
            db_identifier = f"test-db-{faker_instance.uuid4()[:8]}"
        
        # Préparer les paramètres
        params = {
            'DBInstanceIdentifier': db_identifier,
            'DBInstanceClass': db_instance_class,
            'Engine': engine,
            'EngineVersion': engine_version,
            'MasterUsername': master_username,
            'MasterUserPassword': master_password,
            'AllocatedStorage': allocated_storage,
            'StorageType': storage_type,
            'StorageEncrypted': storage_encrypted,
            'MultiAZ': multi_az,
            'PubliclyAccessible': publicly_accessible,
            'BackupRetentionPeriod': backup_retention_period,
            'DeletionProtection': deletion_protection
        }
        
        # Ajouter Performance Insights si supporté
        if performance_insights:
            params['EnablePerformanceInsights'] = True
        
        # Créer l'instance RDS
        response = rds_client.create_db_instance(**params)
        
        # Ajouter des tags si fournis
        if tags:
            db_arn = response['DBInstance']['DBInstanceArn']
            tag_list = [{'Key': k, 'Value': v} for k, v in tags.items()]
            rds_client.add_tags_to_resource(
                ResourceName=db_arn,
                Tags=tag_list
            )
        
        return db_identifier
    
    return _create_instance


@pytest.fixture
def create_multiple_rds_instances(create_rds_instance, faker_instance: Faker):
    """
    Factory fixture pour créer plusieurs instances RDS.
    
    Usage:
        db_ids = create_multiple_rds_instances(count=3, region='us-east-1')
    """
    def _create_multiple(count=3, region='us-east-1', **kwargs):
        db_identifiers = []
        for i in range(count):
            db_id = create_rds_instance(region=region, **kwargs)
            db_identifiers.append(db_id)
        return db_identifiers
    
    return _create_multiple


@pytest.fixture
def create_rds_cloudwatch_metrics(faker_instance: Faker):
    """
    Factory fixture pour créer des métriques CloudWatch pour RDS.
    
    Usage:
        create_rds_cloudwatch_metrics(db_identifier, region, 'CPUUtilization', 45.5)
    """
    def _create_metrics(db_identifier, region, metric_name, value):
        """
        Crée des métriques CloudWatch pour une instance RDS.
        
        Args:
            db_identifier: Identifiant de l'instance RDS
            region: Région AWS
            metric_name: Nom de la métrique (CPUUtilization, FreeableMemory, etc.)
            value: Valeur de la métrique
        """
        cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        
        cloudwatch_client.put_metric_data(
            Namespace='AWS/RDS',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Dimensions': [
                        {
                            'Name': 'DBInstanceIdentifier',
                            'Value': db_identifier
                        }
                    ],
                    'Value': value,
                    'Timestamp': datetime.now()
                }
            ]
        )
    
    return _create_metrics

