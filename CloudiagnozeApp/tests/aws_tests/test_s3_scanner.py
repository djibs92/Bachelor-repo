"""
Tests unitaires pour le scanner S3
"""
import pytest
import boto3
import re
from moto import mock_aws
from api.services.provider.aws.scanners.s3_scan import S3Scanner


class TestS3ScannerBasic:
    """Tests de fonctionnalités de base du scanner S3"""
    
    async def test_scan_no_buckets(self, client_id):
        """Test : Scanner sans buckets"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            results = await scanner.scan()
            
            # ASSERT
            assert isinstance(results, list), "Le résultat doit être une liste"
            assert len(results) == 0, "Devrait retourner une liste vide sans buckets"
    
    async def test_scan_single_bucket(self, client_id, create_s3_bucket):
        """Test : Scanner un seul bucket"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1')
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            results = await scanner.scan()
            
            # ASSERT
            assert len(results) == 1, "Devrait trouver exactement 1 bucket"
            assert results[0]['bucket_name'] == bucket_name
            assert results[0]['client_id'] == client_id
            assert results[0]['region'] == 'us-east-1'
    
    async def test_scan_multiple_buckets(self, client_id, create_multiple_s3_buckets):
        """Test : Scanner plusieurs buckets"""
        with mock_aws():
            # ARRANGE
            count = 5
            bucket_names = create_multiple_s3_buckets(count=count, region='us-east-1')
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            results = await scanner.scan()
            
            # ASSERT
            assert len(results) == count, f"Devrait trouver {count} buckets"
            result_names = [r['bucket_name'] for r in results]
            for bucket_name in bucket_names:
                assert bucket_name in result_names, f"Bucket {bucket_name} devrait être dans les résultats"
    
    async def test_scan_buckets_different_regions(self, client_id, create_s3_bucket):
        """Test : Scanner des buckets dans différentes régions"""
        with mock_aws():
            # ARRANGE
            bucket_us = create_s3_bucket(region='us-east-1')
            bucket_eu = create_s3_bucket(region='eu-west-3')
            
            session = boto3.Session()
            # Scanner uniquement us-east-1
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            results = await scanner.scan()
            
            # ASSERT
            # Devrait trouver uniquement le bucket us-east-1
            assert len(results) == 1, "Devrait trouver uniquement le bucket de la région demandée"
            assert results[0]['bucket_name'] == bucket_us
            assert results[0]['region'] == 'us-east-1'


class TestS3ScannerConfigurations:
    """Tests des différentes configurations de buckets"""
    
    async def test_scan_bucket_with_encryption(self, client_id, create_s3_bucket):
        """Test : Bucket avec encryption activée"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1', encryption=True)
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            results = await scanner.scan()
            
            # ASSERT
            assert len(results) == 1
            assert results[0]['encryption_enabled'] is True
    
    async def test_scan_bucket_with_versioning(self, client_id, create_s3_bucket):
        """Test : Bucket avec versioning activé"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1', versioning=True)
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            results = await scanner.scan()
            
            # ASSERT
            assert len(results) == 1
            assert results[0]['versioning_enabled'] is True
    
    async def test_scan_bucket_with_public_access_block(self, client_id, create_s3_bucket):
        """Test : Bucket avec public access block"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1', public_access_block=True)
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            results = await scanner.scan()
            
            # ASSERT
            assert len(results) == 1
            assert results[0]['public_access_blocked'] is True
    
    async def test_scan_bucket_with_lifecycle(self, client_id, create_s3_bucket):
        """Test : Bucket avec lifecycle policy"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1', lifecycle=True)
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            results = await scanner.scan()
            
            # ASSERT
            assert len(results) == 1
            assert results[0]['lifecycle_enabled'] is True
    
    async def test_scan_bucket_with_website(self, client_id, create_s3_bucket):
        """Test : Bucket configuré comme website"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1', website=True)
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            results = await scanner.scan()
            
            # ASSERT
            assert len(results) == 1
            assert results[0]['website_enabled'] is True


class TestS3ScannerMetrics:
    """Tests de récupération des métriques de performance"""

    async def test_scan_bucket_with_request_metrics(self, client_id, create_s3_bucket, create_s3_cloudwatch_metrics):
        """Test : Extraction des métriques de requêtes"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1')
            create_s3_cloudwatch_metrics(bucket_name, 'us-east-1', 'AllRequests', 1000)
            create_s3_cloudwatch_metrics(bucket_name, 'us-east-1', 'GetRequests', 800)

            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            bucket_data = results[0]
            assert 'performance' in bucket_data, "Devrait contenir des données de performance"
            assert 'all_requests' in bucket_data['performance']
            assert 'get_requests' in bucket_data['performance']

    async def test_scan_bucket_with_error_metrics(self, client_id, create_s3_bucket, create_s3_cloudwatch_metrics):
        """Test : Extraction des métriques d'erreurs"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1')
            create_s3_cloudwatch_metrics(bucket_name, 'us-east-1', '4xxErrors', 10)
            create_s3_cloudwatch_metrics(bucket_name, 'us-east-1', '5xxErrors', 2)

            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            bucket_data = results[0]
            assert 'performance' in bucket_data
            assert '4xx_errors' in bucket_data['performance']
            assert '5xx_errors' in bucket_data['performance']

    async def test_scan_bucket_without_metrics(self, client_id, create_s3_bucket):
        """Test : Bucket sans métriques CloudWatch"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1')
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            bucket_data = results[0]
            assert 'performance' in bucket_data, "Devrait avoir une section performance même sans métriques"
            # Les valeurs devraient être None
            assert bucket_data['performance']['all_requests'] is None


class TestS3ScannerEdgeCases:
    """Tests de cas limites et situations spéciales"""

    async def test_scan_bucket_with_all_features(self, client_id, create_s3_bucket):
        """Test : Bucket avec toutes les fonctionnalités activées"""
        with mock_aws():
            # ARRANGE
            # Note: logging désactivé car moto ne supporte pas bien le logging sur le même bucket
            bucket_name = create_s3_bucket(
                region='us-east-1',
                encryption=True,
                versioning=True,
                public_access_block=True,
                lifecycle=True,
                cors=True,
                website=True,
                logging=False  # Désactivé pour éviter les erreurs moto
            )
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            bucket_data = results[0]
            assert bucket_data['encryption_enabled'] is True
            assert bucket_data['versioning_enabled'] is True
            assert bucket_data['public_access_blocked'] is True
            assert bucket_data['lifecycle_enabled'] is True
            assert bucket_data['cors_enabled'] is True
            assert bucket_data['website_enabled'] is True

    async def test_scan_bucket_with_no_features(self, client_id, create_s3_bucket):
        """Test : Bucket sans aucune fonctionnalité activée"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1')
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            bucket_data = results[0]
            assert bucket_data['encryption_enabled'] is False
            assert bucket_data['versioning_enabled'] is False
            assert bucket_data['lifecycle_enabled'] is False
            assert bucket_data['cors_enabled'] is False
            assert bucket_data['website_enabled'] is False
            assert bucket_data['logging_enabled'] is False


class TestS3ScannerIntegration:
    """Tests d'intégration avec d'autres composants"""

    async def test_scan_data_format_validation(self, client_id, create_s3_bucket):
        """Test : Validation du format des données retournées"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1')
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            bucket_data = results[0]

            # Vérifier les champs obligatoires
            required_fields = [
                'client_id', 'resource_id', 'bucket_name', 'creation_date',
                'region', 'encryption_enabled', 'versioning_enabled',
                'public_access_blocked', 'performance'
            ]

            for field in required_fields:
                assert field in bucket_data, f"Le champ '{field}' devrait être présent"

            # Vérifier les types
            assert isinstance(bucket_data['client_id'], str)
            assert isinstance(bucket_data['bucket_name'], str)
            assert isinstance(bucket_data['performance'], dict)

    async def test_scan_arn_format(self, client_id, create_s3_bucket):
        """Test : Validation du format ARN"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1')
            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            resource_id = results[0]['resource_id']

            # Vérifier le format ARN : arn:aws:s3:::bucket-name
            arn_pattern = r'^arn:aws:s3:::[a-z0-9\-]+$'
            assert re.match(arn_pattern, resource_id), f"ARN invalide: {resource_id}"

    async def test_scan_with_no_regions_specified(self, client_id, create_s3_bucket):
        """Test : Scanner sans spécifier de régions"""
        with mock_aws():
            # ARRANGE
            bucket_name = create_s3_bucket(region='us-east-1')

            session = boto3.Session()
            scanner = S3Scanner(session, client_id, regions=None)  # Pas de régions spécifiées

            # ACT
            results = await scanner.scan()

            # ASSERT
            # Devrait scanner et trouver le bucket
            assert isinstance(results, list), "Devrait retourner une liste"
            assert len(results) >= 1, "Devrait trouver au moins 1 bucket"

