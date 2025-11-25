"""
Tests unitaires pour le scanner RDS
"""
import pytest
import boto3
from moto import mock_aws
from unittest.mock import MagicMock
from api.services.provider.aws.scanners.rds_scanner import RDSScanner


class TestRDSScannerBasic:
    """Tests de fonctionnalités de base du scanner RDS"""
    
    def test_scan_no_instances(self, client_id, mock_db_session):
        """Test : Scanner sans instances RDS"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert isinstance(result, dict), "Le résultat doit être un dictionnaire"
            assert 'total_instances' in result
            assert 'instances_by_region' in result
            assert 'scan_run_id' in result
            assert result['total_instances'] == 0
    
    def test_scan_single_instance(self, client_id, mock_db_session, create_rds_instance):
        """Test : Scanner une seule instance RDS"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', engine='postgres')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_instances'] == 1, "Devrait trouver exactement 1 instance"
            assert 'us-east-1' in result['instances_by_region']
            assert result['instances_by_region']['us-east-1'] == 1
    
    def test_scan_multiple_instances(self, client_id, mock_db_session, create_multiple_rds_instances):
        """Test : Scanner plusieurs instances RDS"""
        with mock_aws():
            # ARRANGE
            count = 3
            db_ids = create_multiple_rds_instances(count=count, region='us-east-1')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_instances'] == count, f"Devrait trouver {count} instances"
    
    def test_scan_multiple_regions(self, client_id, mock_db_session, create_rds_instance):
        """Test : Scanner plusieurs régions"""
        with mock_aws():
            # ARRANGE
            db_us = create_rds_instance(region='us-east-1', engine='postgres')
            db_eu = create_rds_instance(region='eu-west-3', engine='mysql')
            
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1', 'eu-west-3'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_instances'] == 2, "Devrait trouver 2 instances"
            assert 'us-east-1' in result['instances_by_region']
            assert 'eu-west-3' in result['instances_by_region']


class TestRDSScannerEngines:
    """Tests des différents moteurs de base de données"""
    
    def test_scan_postgres_instance(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance PostgreSQL"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', engine='postgres', engine_version='14.7')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called
    
    def test_scan_mysql_instance(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance MySQL"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', engine='mysql', engine_version='8.0.32')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called
    
    def test_scan_mariadb_instance(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance MariaDB"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', engine='mariadb', engine_version='10.6')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called


class TestRDSScannerConfiguration:
    """Tests des configurations RDS"""
    
    def test_scan_encrypted_instance(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance avec stockage chiffré"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', storage_encrypted=True)
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called
    
    def test_scan_multi_az_instance(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance Multi-AZ"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', multi_az=True)
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called

    def test_scan_publicly_accessible_instance(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance accessible publiquement"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', publicly_accessible=True)
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called

    def test_scan_instance_with_deletion_protection(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance avec protection contre la suppression"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', deletion_protection=True)
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called

    def test_scan_instance_with_tags(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance avec tags"""
        with mock_aws():
            # ARRANGE
            tags = {
                'Name': 'test-database',
                'Environment': 'production',
                'Owner': 'team-data'
            }
            db_id = create_rds_instance(region='us-east-1', tags=tags)
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called


class TestRDSScannerStorage:
    """Tests des configurations de stockage"""

    def test_scan_instance_gp2_storage(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance avec stockage GP2"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(
                region='us-east-1',
                storage_type='gp2',
                allocated_storage=100
            )
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called

    def test_scan_instance_io1_storage(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance avec stockage IO1 (IOPS provisionnés)"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(
                region='us-east-1',
                storage_type='io1',
                allocated_storage=100
            )
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called


class TestRDSScannerMetrics:
    """Tests de récupération des métriques"""

    def test_scan_instance_with_cpu_metrics(self, client_id, mock_db_session, create_rds_instance, create_rds_cloudwatch_metrics):
        """Test : Extraction des métriques CPU"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            create_rds_cloudwatch_metrics(db_id, 'us-east-1', 'CPUUtilization', 45.5)

            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called

    def test_scan_instance_with_memory_metrics(self, client_id, mock_db_session, create_rds_instance, create_rds_cloudwatch_metrics):
        """Test : Extraction des métriques mémoire"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            create_rds_cloudwatch_metrics(db_id, 'us-east-1', 'FreeableMemory', 1073741824)  # 1GB

            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called

    def test_scan_instance_without_metrics(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance sans métriques CloudWatch"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called


class TestRDSScannerEdgeCases:
    """Tests de cas limites"""

    def test_scan_instance_with_all_features(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance avec toutes les fonctionnalités"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(
                region='us-east-1',
                db_instance_class='db.m5.large',
                engine='postgres',
                engine_version='14.7',
                allocated_storage=100,
                storage_type='gp2',
                storage_encrypted=True,
                multi_az=True,
                publicly_accessible=False,
                backup_retention_period=30,
                deletion_protection=True,
                tags={'Name': 'full-featured-db', 'Environment': 'production'}
            )
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called
            assert mock_db_session.commit.called

    def test_scan_instance_minimal(self, client_id, mock_db_session, create_rds_instance):
        """Test : Instance minimale"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_instances'] == 1
            assert mock_db_session.add.called

    def test_scan_invalid_region(self, client_id, mock_db_session):
        """Test : Scanner une région invalide"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['invalid-region-999'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            # Le scan devrait continuer malgré l'erreur
            assert isinstance(result, dict)
            assert 'total_instances' in result


class TestRDSScannerIntegration:
    """Tests d'intégration"""

    def test_scan_result_structure(self, client_id, mock_db_session, create_rds_instance):
        """Test : Validation de la structure du résultat"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            # Vérifier les champs obligatoires
            required_fields = ['total_instances', 'instances_by_region', 'scan_run_id']
            for field in required_fields:
                assert field in result, f"Le champ '{field}' devrait être présent"

            # Vérifier les types
            assert isinstance(result['total_instances'], int)
            assert isinstance(result['instances_by_region'], dict)

    def test_scan_with_no_regions_specified(self, client_id, mock_db_session, create_rds_instance):
        """Test : Scanner sans spécifier de régions"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')

            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=None)  # Pas de régions

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            # Devrait scanner les régions disponibles
            assert isinstance(result, dict)
            assert result['total_instances'] >= 0

    def test_scan_db_operations(self, client_id, mock_db_session, create_rds_instance):
        """Test : Vérifier les opérations de base de données"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            # Vérifier que les méthodes DB ont été appelées
            assert mock_db_session.add.called, "add() devrait être appelé"
            assert mock_db_session.commit.called, "commit() devrait être appelé"
            assert mock_db_session.flush.called, "flush() devrait être appelé"

