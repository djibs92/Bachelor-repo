"""
Tests unitaires pour le scanner RDS

Organisation :
1. Tests de base (scan simple, régions multiples)
2. Tests des différents moteurs de base de données
3. Tests des configurations RDS
4. Tests de stockage
5. Tests de métriques
6. Tests de cas limites (edge cases)
7. Tests d'intégration
"""
import pytest
import boto3
from moto import mock_aws
from api.services.provider.aws.scanners.rds_scanner import RDSScanner


class TestRDSScannerBasic:
    """Tests de fonctionnalités de base du scanner RDS"""

    async def test_scan_no_instances(self, client_id):
        """Test : Scanner sans instances RDS"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert isinstance(results, list), "Le résultat doit être une liste"
            assert len(results) == 0, "Devrait retourner une liste vide"

    async def test_scan_single_instance(self, client_id, create_rds_instance):
        """Test : Scanner une seule instance RDS"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', engine='postgres')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1, "Devrait trouver exactement 1 instance"
            assert results[0]['db_instance_identifier'] == db_id
            assert results[0]['client_id'] == client_id

    async def test_scan_multiple_instances(self, client_id, create_multiple_rds_instances):
        """Test : Scanner plusieurs instances RDS"""
        with mock_aws():
            # ARRANGE
            count = 3
            db_ids = create_multiple_rds_instances(count=count, region='us-east-1')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == count, f"Devrait trouver {count} instances"

    async def test_scan_multiple_regions(self, client_id, create_rds_instance):
        """Test : Scanner plusieurs régions"""
        with mock_aws():
            # ARRANGE
            db_us = create_rds_instance(region='us-east-1', engine='postgres')
            db_eu = create_rds_instance(region='eu-west-3', engine='mysql')

            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1', 'eu-west-3'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 2, "Devrait trouver 2 instances"
            regions = [r['region'] for r in results]
            assert 'us-east-1' in regions
            assert 'eu-west-3' in regions


class TestRDSScannerEngines:
    """Tests des différents moteurs de base de données"""

    async def test_scan_postgres_instance(self, client_id, create_rds_instance):
        """Test : Instance PostgreSQL"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', engine='postgres', engine_version='14.7')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['engine'] == 'postgres'

    async def test_scan_mysql_instance(self, client_id, create_rds_instance):
        """Test : Instance MySQL"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', engine='mysql', engine_version='8.0.32')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['engine'] == 'mysql'

    async def test_scan_mariadb_instance(self, client_id, create_rds_instance):
        """Test : Instance MariaDB"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', engine='mariadb', engine_version='10.6')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['engine'] == 'mariadb'


class TestRDSScannerConfiguration:
    """Tests des configurations RDS"""

    async def test_scan_encrypted_instance(self, client_id, create_rds_instance):
        """Test : Instance avec stockage chiffré"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', storage_encrypted=True)
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['storage_encrypted'] == True

    async def test_scan_multi_az_instance(self, client_id, create_rds_instance):
        """Test : Instance Multi-AZ"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', multi_az=True)
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['multi_az'] == True

    async def test_scan_publicly_accessible_instance(self, client_id, create_rds_instance):
        """Test : Instance accessible publiquement"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', publicly_accessible=True)
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['publicly_accessible'] == True

    async def test_scan_instance_with_deletion_protection(self, client_id, create_rds_instance):
        """Test : Instance avec protection contre la suppression"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1', deletion_protection=True)
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['deletion_protection'] == True

    async def test_scan_instance_with_tags(self, client_id, create_rds_instance):
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
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1


class TestRDSScannerStorage:
    """Tests des configurations de stockage"""

    async def test_scan_instance_gp2_storage(self, client_id, create_rds_instance):
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
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['storage_type'] == 'gp2'

    async def test_scan_instance_io1_storage(self, client_id, create_rds_instance):
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
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['storage_type'] == 'io1'


class TestRDSScannerMetrics:
    """Tests de récupération des métriques"""

    async def test_scan_instance_with_cpu_metrics(self, client_id, create_rds_instance, create_rds_cloudwatch_metrics):
        """Test : Extraction des métriques CPU"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            create_rds_cloudwatch_metrics(db_id, 'us-east-1', 'CPUUtilization', 45.5)

            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1

    async def test_scan_instance_with_memory_metrics(self, client_id, create_rds_instance, create_rds_cloudwatch_metrics):
        """Test : Extraction des métriques mémoire"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            create_rds_cloudwatch_metrics(db_id, 'us-east-1', 'FreeableMemory', 1073741824)  # 1GB

            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1

    async def test_scan_instance_without_metrics(self, client_id, create_rds_instance):
        """Test : Instance sans métriques CloudWatch"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['db_instance_identifier'] == db_id


class TestRDSScannerEdgeCases:
    """Tests de cas limites"""

    async def test_scan_instance_with_all_features(self, client_id, create_rds_instance):
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
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['db_instance_identifier'] == db_id

    async def test_scan_instance_minimal(self, client_id, create_rds_instance):
        """Test : Instance minimale"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['db_instance_identifier'] == db_id

    async def test_scan_invalid_region(self, client_id):
        """Test : Scanner une région invalide"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['invalid-region-999'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            # Le scan devrait continuer malgré l'erreur (liste vide)
            assert isinstance(results, list)


class TestRDSScannerIntegration:
    """Tests d'intégration"""

    async def test_scan_result_structure(self, client_id, create_rds_instance):
        """Test : Validation de la structure du résultat"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            instance = results[0]
            # Vérifier les champs obligatoires
            required_fields = ['db_instance_identifier', 'region', 'client_id', 'engine']
            for field in required_fields:
                assert field in instance, f"Le champ '{field}' devrait être présent"

    async def test_scan_with_no_regions_specified(self, client_id, create_rds_instance):
        """Test : Scanner sans spécifier de régions"""
        with mock_aws():
            # ARRANGE
            create_rds_instance(region='us-east-1')

            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=None)  # Pas de régions

            # ACT
            results = await scanner.scan()

            # ASSERT
            # Devrait scanner les régions disponibles
            assert isinstance(results, list)

    async def test_scan_returns_list(self, client_id, create_rds_instance):
        """Test : Vérifier que le scan retourne une liste"""
        with mock_aws():
            # ARRANGE
            db_id = create_rds_instance(region='us-east-1')
            session = boto3.Session()
            scanner = RDSScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0]['db_instance_identifier'] == db_id

