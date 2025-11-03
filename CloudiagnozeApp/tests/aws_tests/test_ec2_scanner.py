import pytest
import sys
import os
from unittest.mock import Mock
from datetime import datetime, timedelta

# 1. ISOLER la fonction à tester
# 2. CRÉER des données fictives 
# 3. MOCKER les dépendances
# 4. EXÉCUTER la fonction
# 5. VÉRIFIER le résultat

# Ajouter le répertoire parent au path Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.services.provider.aws.scanners.ec2_scan import EC2Scanner

# ========================================
# TESTS DE PATTERNS - PAS BESOIN DE TOUT TESTER
# ========================================

def test_extract_instance_type():
    """
     PATTERN: Extracteur métadonnées SIMPLE
    Représente: _extract_ami_id, _extract_architecture, _extract_tenancy, etc.
    Raison: Tous ces extracteurs ont la même logique (1 champ → 1 event)
    """
    scanner = EC2Scanner(session=None, client_id="test-client")
    
    fake_instance = {
        'InstanceType': 't2.micro',
        'InstanceId': 'i-123456789'
    }
    fake_arn = 'arn:aws:ec2:us-east-1:123456789:instance/i-123456789'
    
    # Mock _create_event pour éviter les dépendances
    def mock_create_event(resource_id, metric_type, metric_value):
        return {
            'resource_id': resource_id,
            'metric_type': metric_type, 
            'metric_value': metric_value
        }
    
    scanner._create_event = mock_create_event
    
    result = scanner._extract_instance_type(fake_instance, fake_arn)
    
    assert result['resource_id'] == fake_arn
    assert result['metric_type'] == "aws.metadata.ec2.instance_type"
    assert result['metric_value'] == "t2.micro"

def test_extract_ip_addresses():
    """
     PATTERN: Extracteur métadonnées COMPLEXE (retourne liste)
    Représente: _extract_storage_info, _extract_tags (cas complexes)
    Raison: Teste la logique de création de plusieurs events depuis 1 ressource
    """
    scanner = EC2Scanner(session=None, client_id="test-client")
    
    fake_instance = {
        'PrivateIpAddress': '10.0.1.100',
        'PublicIpAddress': '54.123.45.67',
        'InstanceId': 'i-123456789'
    }
    fake_arn = 'arn:aws:ec2:us-east-1:123456789:instance/i-123456789'
    
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
    
    result = scanner._extract_ip_addresses(fake_instance, fake_arn)
    
    # Vérifier qu'on a 2 events (IP privée + publique)
    assert len(result) == 2
    assert len(created_events) == 2
    
    # Vérifier les types de métriques
    metric_types = [event['metric_type'] for event in created_events]
    assert "aws.metadata.ec2.private_ip" in metric_types
    assert "aws.metadata.ec2.public_ip" in metric_types

def test_extract_cpu_utilization():
    """
     PATTERN: Extracteur PERFORMANCE avec CloudWatch
    Représente: _extract_memory_utilization, _extract_network_in, _extract_network_out
    Raison: Teste l'intégration CloudWatch + gestion d'erreurs (pattern critique)
    """
    scanner = EC2Scanner(session=None, client_id="test-client")
    
    fake_instance = {'InstanceId': 'i-123456789'}
    fake_arn = 'arn:aws:ec2:us-east-1:123456789:instance/i-123456789'
    fake_region = 'us-east-1'
    
    # Mock CloudWatch response avec données
    mock_cloudwatch = Mock()
    mock_cloudwatch.get_metric_statistics.return_value = {
        'Datapoints': [
            {'Average': 25.5, 'Timestamp': datetime.now()},
            {'Average': 30.2, 'Timestamp': datetime.now()}
        ]
    }
    
    # Mock get_client pour retourner notre mock CloudWatch
    scanner.get_client = Mock(return_value=mock_cloudwatch)
    
    # Mock _create_event
    def mock_create_event(resource_id, metric_type, metric_value):
        return {
            'resource_id': resource_id,
            'metric_type': metric_type, 
            'metric_value': metric_value
        }
    
    scanner._create_event = mock_create_event
    
    result = scanner._extract_cpu_utilization(fake_instance, fake_arn, fake_region)
    
    # Vérifications
    assert result['metric_type'] == "aws.performance.ec2.cpu_utilization.average"
    assert result['metric_value'] == 27.85  # Moyenne de 25.5 et 30.2
    
    # Vérifier que CloudWatch a été appelé correctement
    mock_cloudwatch.get_metric_statistics.assert_called_once()

def test_extract_cpu_utilization_no_data():
    """
     PATTERN: Gestion d'erreur CloudWatch (pas de données)
    Raison: Teste le fallback vers _create_unavailable_event
    """
    scanner = EC2Scanner(session=None, client_id="test-client")
    
    fake_instance = {'InstanceId': 'i-123456789'}
    fake_arn = 'arn:aws:ec2:us-east-1:123456789:instance/i-123456789'
    
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
    
    result = scanner._extract_cpu_utilization(fake_instance, fake_arn, 'us-east-1')
    
    assert result['unavailable'] == True
    assert "Aucune donnée CloudWatch disponible" in result['reason']

def test_scan_single_instance():
    """
     PATTERN: Logique principale d'orchestration
    Raison: Teste que tous les extracteurs sont appelés + gestion d'erreurs
    """
    scanner = EC2Scanner(session=None, client_id="test-client")
    
    fake_instance = {
        'InstanceType': 't2.micro',
        'InstanceId': 'i-123456789',
        'State': {'Name': 'running'},
        'ImageId': 'ami-12345'
    }
    fake_region = 'us-east-1'
    
    # Mock _build_ec2_arn
    scanner._build_ec2_arn = Mock(return_value='arn:aws:ec2:us-east-1:123:instance/i-123456789')
    
    # Mock tous les extracteurs pour retourner des events fictifs
    def mock_extractor(*args):
        return {'mock': 'event'}
    
    # Remplacer quelques extracteurs par des mocks
    scanner._extract_instance_type = Mock(return_value=mock_extractor())
    scanner._extract_instance_state = Mock(return_value=mock_extractor())
    scanner._extract_cpu_utilization = Mock(return_value=mock_extractor())
    
    # Mock add_event_to_store pour éviter les dépendances
    import api.services.provider.aws.scanners.ec2_scan
    api.services.provider.aws.scanners.ec2_scan.add_event_to_store = Mock()
    
    result = scanner._scan_single_instance(fake_instance, fake_region)
    
    # Vérifier qu'on a des events
    assert len(result) > 0
    
    # Vérifier que les extracteurs ont été appelés
    scanner._extract_instance_type.assert_called_once()
    scanner._extract_instance_state.assert_called_once()
    scanner._extract_cpu_utilization.assert_called_once()

# ========================================
# POURQUOI ON NE TESTE PAS TOUT ?
# ========================================
# ❌ _extract_ami_id        → Identique à _extract_instance_type
# ❌ _extract_architecture  → Identique à _extract_instance_type  
# ❌ _extract_tenancy       → Identique à _extract_instance_type
# ❌ _extract_memory_util   → Identique à _extract_cpu_utilization
# ❌ _extract_network_in    → Identique à _extract_cpu_utilization
# 
#  RÉSULTAT: 5 tests couvrent 18 fonctions !
# ========================================

def test_extract_instance_type_missing_field():
    """Test avec instance sans InstanceType"""
    scanner = EC2Scanner(session=None, client_id="test-client")
    
    fake_instance = {'InstanceId': 'i-123456789'}  # Pas d'InstanceType
    fake_arn = 'arn:aws:ec2:us-east-1:123456789:instance/i-123456789'
    
    # Test que ça lève une erreur
    with pytest.raises(KeyError):
        scanner._extract_instance_type(fake_instance, fake_arn)

def test_extract_instance_type_different_types():
    """Test avec différents types d'instance"""
    scanner = EC2Scanner(session=None, client_id="test-client")
    
    # Mock _create_event correctement
    def mock_create_event(resource_id, metric_type, metric_value):
        return {'metric_value': metric_value}
    
    scanner._create_event = mock_create_event
    
    test_cases = ['t3.large', 'm5.xlarge', 'c5.2xlarge']
    
    for instance_type in test_cases:
        fake_instance = {'InstanceType': instance_type, 'InstanceId': 'i-123'}
        result = scanner._extract_instance_type(fake_instance, 'arn:test')
        assert result['metric_value'] == instance_type
