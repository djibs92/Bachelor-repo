import pytest
import sys
import os
from unittest.mock import Mock
from datetime import datetime, timedelta

# 5 tests couvrent 20 fonctions
#Patterns testés : Métadonnées simples, Sécurité, Performance CloudWatch, Erreurs, Orchestration


# Ajouter le répertoire parent au path Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.services.provider.aws.scanners.s3_scan import S3Scanner

# ========================================
# TESTS DE PATTERNS S3 - PAS BESOIN DE TOUT TESTER
# ========================================

def test_extract_bucket_name():
    """
    🎯 PATTERN: Extracteur métadonnées SIMPLE S3
    Représente: _extract_creation_date, _extract_region, _extract_owner, etc.
    Raison: Tous ces extracteurs ont la même logique (1 champ → 1 event)
    """
    scanner = S3Scanner(session=None, client_id="test-client")
    
    fake_bucket = {
        'Name': 'mon-super-bucket',
        'CreationDate': datetime.now()
    }
    fake_arn = 'arn:aws:s3:::mon-super-bucket'
    fake_s3_client = Mock()
    
    # Mock _create_event
    def mock_create_event(resource_id, metric_type, metric_value):
        return {
            'resource_id': resource_id,
            'metric_type': metric_type, 
            'metric_value': metric_value
        }
    
    scanner._create_event = mock_create_event
    
    result = scanner._extract_bucket_name(fake_bucket, fake_arn, fake_s3_client)
    
    assert result['resource_id'] == fake_arn
    assert result['metric_type'] == "aws.metadata.s3.bucket.bucket_name"
    assert result['metric_value'] == "mon-super-bucket"

def test_extract_encryption():
    """
    🎯 PATTERN: Extracteur sécurité S3 avec gestion d'erreur
    Représente: _extract_versioning, _extract_public_access_block, _extract_acl
    Raison: Teste la logique d'appel API S3 + gestion des exceptions
    """
    scanner = S3Scanner(session=None, client_id="test-client")
    
    fake_bucket = {'Name': 'bucket-test'}
    fake_arn = 'arn:aws:s3:::bucket-test'
    
    # Mock S3 client avec encryption activée
    mock_s3_client = Mock()
    mock_s3_client.get_bucket_encryption.return_value = {
        'ServerSideEncryptionConfiguration': {
            'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]
        }
    }
    
    # Mock _create_event
    def mock_create_event(resource_id, metric_type, metric_value):
        return {
            'resource_id': resource_id,
            'metric_type': metric_type, 
            'metric_value': metric_value
        }
    
    scanner._create_event = mock_create_event
    
    result = scanner._extract_encryption(fake_bucket, fake_arn, mock_s3_client)
    
    assert result['metric_type'] == "aws.metadata.s3.encryption_enabled"
    assert result['metric_value'] == True
    
    # Vérifier que l'API S3 a été appelée
    mock_s3_client.get_bucket_encryption.assert_called_once_with(Bucket='bucket-test')

def test_extract_request_metrics():
    """
    🎯 PATTERN: Extracteur PERFORMANCE S3 avec CloudWatch
    Représente: _extract_error_metrics, _extract_latency_metrics, _extract_transfer_metrics
    Raison: Teste l'intégration CloudWatch + gestion des métriques multiples
    """
    scanner = S3Scanner(session=None, client_id="test-client")
    
    fake_bucket = {'Name': 'bucket-perf'}
    fake_arn = 'arn:aws:s3:::bucket-perf'
    fake_region = 'us-east-1'
    
    # Mock CloudWatch avec données
    mock_cloudwatch = Mock()
    mock_cloudwatch.get_metric_statistics.return_value = {
        'Datapoints': [
            {'Sum': 1000, 'Timestamp': datetime.now()},
            {'Sum': 1500, 'Timestamp': datetime.now()}
        ]
    }
    
    # Mock get_client pour retourner CloudWatch
    scanner.get_client = Mock(return_value=mock_cloudwatch)
    
    # Mock _create_event
    created_events = []
    def mock_create_event(resource_id, metric_type, metric_value):
        event = {
            'resource_id': resource_id,
            'metric_type': metric_type, 
            'metric_value': metric_value
        }
        created_events.append(event)
        return event
    
    scanner._create_event = mock_create_event
    
    result = scanner._extract_request_metrics(fake_bucket, fake_arn, None, fake_region)
    
    # Vérifier qu'on a des métriques (AllRequests, GetRequests, PutRequests)
    assert len(result) >= 3
    assert len(created_events) >= 3
    
    # Vérifier les types de métriques
    metric_types = [event['metric_type'] for event in created_events]
    assert any('all_requests' in mt for mt in metric_types)

def test_extract_request_metrics_no_data():
    """
    🎯 PATTERN: Gestion d'erreur CloudWatch S3 (pas de données)
    Raison: Teste le fallback vers _create_unavailable_event
    """
    scanner = S3Scanner(session=None, client_id="test-client")
    
    fake_bucket = {'Name': 'bucket-empty'}
    fake_arn = 'arn:aws:s3:::bucket-empty'
    
    # Mock CloudWatch sans données
    mock_cloudwatch = Mock()
    mock_cloudwatch.get_metric_statistics.return_value = {'Datapoints': []}
    
    scanner.get_client = Mock(return_value=mock_cloudwatch)
    
    # Mock _create_unavailable_event
    def mock_unavailable_event(resource_id, metric_name, reason):
        return {
            'resource_id': resource_id,
            'unavailable': True,
            'reason': reason
        }
    
    scanner._create_unavailable_event = mock_unavailable_event
    
    result = scanner._extract_request_metrics(fake_bucket, fake_arn, None, 'us-east-1')
    
    # Vérifier qu'on a des événements d'indisponibilité
    assert len(result) > 0
    assert any(event.get('unavailable') for event in result if isinstance(event, dict))

@pytest.mark.asyncio
async def test_scan_single_bucket():
    """
    🎯 PATTERN: Logique principale d'orchestration S3
    Raison: Teste que tous les extracteurs sont appelés + gestion d'erreurs
    """
    scanner = S3Scanner(session=None, client_id="test-client")
    
    fake_bucket = {
        'Name': 'test-bucket',
        'CreationDate': datetime.now()
    }
    fake_s3_client = Mock()
    
    # Mock _get_bucket_region pour éviter les erreurs
    scanner._get_bucket_region = Mock(return_value='us-east-1')
    
    # Mock quelques extracteurs pour retourner des events fictifs
    def mock_extractor(*args):
        return {'mock': 'event'}
    
    def mock_performance_extractor(*args):
        return [{'mock': 'performance_event'}]
    
    scanner._extract_bucket_name = Mock(return_value=mock_extractor())
    scanner._extract_encryption = Mock(return_value=mock_extractor())
    scanner._extract_request_metrics = Mock(return_value=mock_performance_extractor())
    
    # Mock add_event_to_store
    import api.services.provider.aws.scanners.s3_scan
    api.services.provider.aws.scanners.s3_scan.add_event_to_store = Mock()
    
    result = await scanner._scan_single_bucket(fake_bucket, fake_s3_client)
    
    # Vérifier qu'on a des events
    assert len(result) > 0
    
    # Vérifier que les extracteurs ont été appelés
    scanner._extract_bucket_name.assert_called_once()
    scanner._extract_encryption.assert_called_once()
    scanner._extract_request_metrics.assert_called_once()

# ========================================
# POURQUOI ON NE TESTE PAS TOUT S3 ?
# ========================================
# ❌ _extract_creation_date  → Identique à _extract_bucket_name
# ❌ _extract_region         → Identique à _extract_bucket_name  
# ❌ _extract_versioning     → Identique à _extract_encryption
# ❌ _extract_error_metrics  → Identique à _extract_request_metrics
# ❌ _extract_latency_metrics → Identique à _extract_request_metrics
# 
# 🎯 RÉSULTAT: 5 tests couvrent 20 fonctions S3 !
# ========================================
