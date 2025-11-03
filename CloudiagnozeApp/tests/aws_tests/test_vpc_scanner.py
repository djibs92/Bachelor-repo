import pytest
import sys
import os
from unittest.mock import Mock
from datetime import datetime, timedelta

# 5 tests couvrent 15+ fonctions VPC
# Patterns testés : Métadonnées VPC, Réseau, Sécurité, Comptage ressources, Orchestration

# Ajouter le répertoire parent au path Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.services.provider.aws.scanners.vpc_scan import VPCScanner

# ========================================
# TESTS DE PATTERNS VPC - PAS BESOIN DE TOUT TESTER
# ========================================

def test_extract_vpc_info():
    """
    🎯 PATTERN: Extracteur métadonnées SIMPLE VPC
    Représente: _extract_vpc_state, _extract_vpc_tenancy, _extract_is_default
    Raison: Tous ces extracteurs ont la même logique (1-2 champs → events)
    """
    scanner = VPCScanner(session=None, client_id="test-client")
    
    fake_vpc = {
        'VpcId': 'vpc-123456789',
        'CidrBlock': '10.0.0.0/16',
        'State': 'available'
    }
    fake_arn = 'arn:aws:ec2:us-east-1:123456789:vpc/vpc-123456789'
    fake_ec2_client = Mock()
    fake_region = 'us-east-1'
    
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
    
    result = scanner._extract_vpc_info(fake_vpc, fake_arn, fake_ec2_client, fake_region)
    
    # Vérifier qu'on a 2 events (vpc_id, cidr_block)
    assert len(result) == 2
    assert len(created_events) == 2
    
    # Vérifier les types de métriques
    metric_types = [event['metric_type'] for event in created_events]
    assert "aws.metadata.vpc.vpc_id" in metric_types
    assert "aws.metadata.vpc.cidr_block" in metric_types
    
    # Vérifier les valeurs
    vpc_id_event = next(e for e in created_events if e['metric_type'] == "aws.metadata.vpc.vpc_id")
    assert vpc_id_event['metric_value'] == "vpc-123456789"
    
    cidr_event = next(e for e in created_events if e['metric_type'] == "aws.metadata.vpc.cidr_block")
    assert cidr_event['metric_value'] == "10.0.0.0/16"

def test_extract_subnet_count():
    """
    🎯 PATTERN: Extracteur COMPTAGE avec API calls
    Représente: _extract_route_tables_count, _extract_nat_gateways
    Raison: Teste la logique d'appel API + comptage + classification
    """
    scanner = VPCScanner(session=None, client_id="test-client")
    
    fake_vpc = {'VpcId': 'vpc-123456789'}
    fake_arn = 'arn:aws:ec2:us-east-1:123456789:vpc/vpc-123456789'
    fake_region = 'us-east-1'
    
    # Mock EC2 client avec réponse subnets
    fake_ec2_client = Mock()
    fake_ec2_client.describe_subnets.return_value = {
        'Subnets': [
            {'SubnetId': 'subnet-1', 'MapPublicIpOnLaunch': True},   # Public
            {'SubnetId': 'subnet-2', 'MapPublicIpOnLaunch': False},  # Private
            {'SubnetId': 'subnet-3', 'MapPublicIpOnLaunch': True},   # Public
            {'SubnetId': 'subnet-4', 'MapPublicIpOnLaunch': False}   # Private
        ]
    }
    
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
    
    result = scanner._extract_subnet_count(fake_vpc, fake_arn, fake_ec2_client, fake_region)
    
    # Vérifier qu'on a 3 events (total, public, private)
    assert len(result) == 3
    assert len(created_events) == 3
    
    # Vérifier les comptages
    total_event = next(e for e in created_events if e['metric_type'] == "aws.metadata.vpc.subnet_count")
    assert total_event['metric_value'] == 4
    
    public_event = next(e for e in created_events if e['metric_type'] == "aws.metadata.vpc.public_subnets_count")
    assert public_event['metric_value'] == 2
    
    private_event = next(e for e in created_events if e['metric_type'] == "aws.metadata.vpc.private_subnets_count")
    assert private_event['metric_value'] == 2
    
    # Vérifier l'appel API
    fake_ec2_client.describe_subnets.assert_called_once_with(
        Filters=[{'Name': 'vpc-id', 'Values': ['vpc-123456789']}]
    )

def test_extract_security_groups():
    """
    🎯 PATTERN: Extracteur SÉCURITÉ avec analyse de règles
    Représente: _extract_network_acls, _extract_flow_logs
    Raison: Teste la logique d'analyse sécurité + comptage de vulnérabilités
    """
    scanner = VPCScanner(session=None, client_id="test-client")
    
    fake_vpc = {'VpcId': 'vpc-123456789'}
    fake_arn = 'arn:aws:ec2:us-east-1:123456789:vpc/vpc-123456789'
    fake_region = 'us-east-1'
    
    # Mock EC2 client avec Security Groups
    fake_ec2_client = Mock()
    fake_ec2_client.describe_security_groups.return_value = {
        'SecurityGroups': [
            {
                'GroupId': 'sg-1',
                'IpPermissions': [
                    {
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Règle ouverte
                    }
                ]
            },
            {
                'GroupId': 'sg-2',
                'IpPermissions': [
                    {
                        'IpRanges': [{'CidrIp': '10.0.0.0/16'}]  # Règle fermée
                    },
                    {
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Règle ouverte
                    }
                ]
            }
        ]
    }
    
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
    
    result = scanner._extract_security_groups(fake_vpc, fake_arn, fake_ec2_client, fake_region)
    
    # Vérifier qu'on a 2 events (count, open_rules)
    assert len(result) == 2
    assert len(created_events) == 2
    
    # Vérifier les comptages
    count_event = next(e for e in created_events if e['metric_type'] == "aws.security.vpc.security_groups_count")
    assert count_event['metric_value'] == 2
    
    open_rules_event = next(e for e in created_events if e['metric_type'] == "aws.security.vpc.open_security_rules_count")
    assert open_rules_event['metric_value'] == 2  # 2 règles ouvertes détectées

def test_extract_availability_zones():
    """
    🎯 PATTERN: Extracteur RÉSEAU avec déduplication
    Représente: _extract_internet_gateway, _extract_vpc_endpoints
    Raison: Teste la logique de déduplication + extraction de listes uniques
    """
    scanner = VPCScanner(session=None, client_id="test-client")
    
    fake_vpc = {'VpcId': 'vpc-123456789'}
    fake_arn = 'arn:aws:ec2:us-east-1:123456789:vpc/vpc-123456789'
    fake_region = 'us-east-1'
    
    # Mock EC2 client avec subnets dans différentes AZ
    fake_ec2_client = Mock()
    fake_ec2_client.describe_subnets.return_value = {
        'Subnets': [
            {'AvailabilityZone': 'us-east-1a'},
            {'AvailabilityZone': 'us-east-1b'},
            {'AvailabilityZone': 'us-east-1a'},  # Duplicate
            {'AvailabilityZone': 'us-east-1c'},
            {'AvailabilityZone': 'us-east-1b'}   # Duplicate
        ]
    }
    
    # Mock _create_event
    def mock_create_event(resource_id, metric_type, metric_value):
        return {
            'resource_id': resource_id,
            'metric_type': metric_type, 
            'metric_value': metric_value
        }
    
    scanner._create_event = mock_create_event
    
    result = scanner._extract_availability_zones(fake_vpc, fake_arn, fake_ec2_client, fake_region)
    
    # Vérifier qu'on a un event avec AZ uniques
    assert result['metric_type'] == "aws.metadata.vpc.availability_zones"
    assert len(result['metric_value']) == 3  # 3 AZ uniques
    assert set(result['metric_value']) == {'us-east-1a', 'us-east-1b', 'us-east-1c'}

@pytest.mark.asyncio
async def test_scan_single_vpc():
    """
    🎯 PATTERN: Logique principale d'orchestration VPC
    Raison: Teste que tous les extracteurs sont appelés + gestion d'erreurs
    """
    scanner = VPCScanner(session=None, client_id="test-client")
    
    fake_vpc = {
        'VpcId': 'vpc-123456789',
        'CidrBlock': '10.0.0.0/16',
        'State': 'available'
    }
    fake_region = 'us-east-1'
    fake_ec2_client = Mock()
    
    # Mock _build_vpc_arn
    scanner._build_vpc_arn = Mock(return_value='arn:aws:ec2:us-east-1:123:vpc/vpc-123456789')
    
    # Mock quelques extracteurs pour retourner des events fictifs
    def mock_list_extractor(*args):
        return [{'mock': 'event'}]
    
    def mock_single_extractor(*args):
        return {'mock': 'single_event'}
    
    # Remplacer quelques extracteurs par des mocks
    scanner._extract_vpc_info = Mock(return_value=mock_list_extractor())
    scanner._extract_vpc_state = Mock(return_value=mock_single_extractor())
    scanner._extract_subnet_count = Mock(return_value=mock_list_extractor())
    scanner._extract_security_groups = Mock(return_value=mock_list_extractor())
    
    # Mock add_event_to_store pour éviter les dépendances
    import api.services.provider.aws.scanners.vpc_scan
    api.services.provider.aws.scanners.vpc_scan.add_event_to_store = Mock()
    
    result = await scanner._scan_single_vpc(fake_vpc, fake_region, fake_ec2_client)
    
    # Vérifier qu'on a des events
    assert len(result) > 0
    
    # Vérifier que les extracteurs ont été appelés
    scanner._extract_vpc_info.assert_called_once()
    scanner._extract_vpc_state.assert_called_once()
    scanner._extract_subnet_count.assert_called_once()
    scanner._extract_security_groups.assert_called_once()

def test_extract_internet_gateway():
    """Test avec et sans Internet Gateway"""
    scanner = VPCScanner(session=None, client_id="test-client")
    
    fake_vpc = {'VpcId': 'vpc-123456789'}
    fake_arn = 'arn:aws:ec2:us-east-1:123456789:vpc/vpc-123456789'
    fake_region = 'us-east-1'
    
    # Test AVEC Internet Gateway
    fake_ec2_client = Mock()
    fake_ec2_client.describe_internet_gateways.return_value = {
        'InternetGateways': [{'InternetGatewayId': 'igw-123'}]
    }
    
    def mock_create_event(resource_id, metric_type, metric_value):
        return {'metric_type': metric_type, 'metric_value': metric_value}
    
    scanner._create_event = mock_create_event
    
    result = scanner._extract_internet_gateway(fake_vpc, fake_arn, fake_ec2_client, fake_region)
    
    assert result['metric_type'] == "aws.metadata.vpc.internet_gateway_attached"
    assert result['metric_value'] == True
    
    # Test SANS Internet Gateway
    fake_ec2_client.describe_internet_gateways.return_value = {'InternetGateways': []}
    
    result = scanner._extract_internet_gateway(fake_vpc, fake_arn, fake_ec2_client, fake_region)
    assert result['metric_value'] == False
