"""
Tests unitaires pour le scanner VPC
"""
import pytest
import boto3
from moto import mock_aws
from unittest.mock import MagicMock
from api.services.provider.aws.scanners.vpc_scanner import VPCScanner


class TestVPCScannerBasic:
    """Tests de fonctionnalités de base du scanner VPC"""
    
    def test_scan_no_vpcs(self, client_id, mock_db_session):
        """Test : Scanner sans VPCs (sauf le VPC par défaut)"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert isinstance(result, dict), "Le résultat doit être un dictionnaire"
            assert 'total_vpcs' in result
            assert 'vpcs_by_region' in result
            assert 'scan_run_id' in result
            # Moto crée un VPC par défaut
            assert result['total_vpcs'] >= 0
    
    def test_scan_single_vpc(self, client_id, mock_db_session, create_vpc):
        """Test : Scanner un seul VPC"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1', cidr='10.0.0.0/16')
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_vpcs'] >= 1, "Devrait trouver au moins 1 VPC"
            assert 'us-east-1' in result['vpcs_by_region']
    
    def test_scan_multiple_vpcs(self, client_id, mock_db_session, create_multiple_vpcs):
        """Test : Scanner plusieurs VPCs"""
        with mock_aws():
            # ARRANGE
            count = 3
            vpc_ids = create_multiple_vpcs(count=count, region='us-east-1')
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_vpcs'] >= count, f"Devrait trouver au moins {count} VPCs"
    
    def test_scan_multiple_regions(self, client_id, mock_db_session, create_vpc):
        """Test : Scanner plusieurs régions"""
        with mock_aws():
            # ARRANGE
            vpc_us = create_vpc(region='us-east-1', cidr='10.0.0.0/16')
            vpc_eu = create_vpc(region='eu-west-3', cidr='10.1.0.0/16')
            
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1', 'eu-west-3'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_vpcs'] >= 2, "Devrait trouver au moins 2 VPCs"
            assert 'us-east-1' in result['vpcs_by_region']
            assert 'eu-west-3' in result['vpcs_by_region']


class TestVPCScannerNetworking:
    """Tests des fonctionnalités réseau du VPC"""
    
    def test_scan_vpc_with_subnets(self, client_id, mock_db_session, create_vpc):
        """Test : VPC avec subnets publics et privés"""
        with mock_aws():
            # ARRANGE
            subnets = [
                {'cidr': '10.0.1.0/24', 'az': 'us-east-1a', 'public': True},
                {'cidr': '10.0.2.0/24', 'az': 'us-east-1b', 'public': False},
                {'cidr': '10.0.3.0/24', 'az': 'us-east-1c', 'public': True}
            ]
            vpc_id = create_vpc(region='us-east-1', subnets=subnets)
            
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_vpcs'] >= 1
            # Vérifier que add a été appelé (VPCInstance créé)
            assert mock_db_session.add.called
    
    def test_scan_vpc_with_internet_gateway(self, client_id, mock_db_session, create_vpc):
        """Test : VPC avec Internet Gateway"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(
                region='us-east-1',
                internet_gateway=True,
                subnets=[{'cidr': '10.0.1.0/24', 'az': 'us-east-1a', 'public': True}]
            )
            
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_vpcs'] >= 1
            assert mock_db_session.add.called
    
    def test_scan_vpc_with_nat_gateways(self, client_id, mock_db_session, create_vpc):
        """Test : VPC avec NAT Gateways"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(
                region='us-east-1',
                subnets=[
                    {'cidr': '10.0.1.0/24', 'az': 'us-east-1a', 'public': True},
                    {'cidr': '10.0.2.0/24', 'az': 'us-east-1b', 'public': True}
                ],
                internet_gateway=True,
                nat_gateways=2
            )
            
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_vpcs'] >= 1
            assert mock_db_session.add.called
    
    def test_scan_vpc_with_flow_logs(self, client_id, mock_db_session, create_vpc):
        """Test : VPC avec Flow Logs activés"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1', flow_logs=True)
            
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])
            
            # ACT
            result = scanner.scan(mock_db_session)
            
            # ASSERT
            assert result['total_vpcs'] >= 1
            assert mock_db_session.add.called


class TestVPCScannerConfiguration:
    """Tests des configurations VPC"""

    def test_scan_vpc_with_tags(self, client_id, mock_db_session, create_vpc):
        """Test : VPC avec tags"""
        with mock_aws():
            # ARRANGE
            tags = {
                'Name': 'test-vpc',
                'Environment': 'production',
                'Owner': 'team-infra'
            }
            vpc_id = create_vpc(region='us-east-1', tags=tags)

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_vpcs'] >= 1
            assert mock_db_session.add.called

    def test_scan_vpc_with_dedicated_tenancy(self, client_id, mock_db_session, create_vpc):
        """Test : VPC avec tenancy dédié"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1', tenancy='dedicated')

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_vpcs'] >= 1
            assert mock_db_session.add.called

    def test_scan_vpc_with_endpoints(self, client_id, mock_db_session, create_vpc):
        """Test : VPC avec VPC endpoints"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1', vpc_endpoints=2)

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_vpcs'] >= 1
            assert mock_db_session.add.called


class TestVPCScannerEdgeCases:
    """Tests de cas limites"""

    def test_scan_vpc_with_all_features(self, client_id, mock_db_session, create_vpc):
        """Test : VPC avec toutes les fonctionnalités"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(
                region='us-east-1',
                cidr='10.0.0.0/16',
                tags={'Name': 'full-vpc', 'Environment': 'test'},
                subnets=[
                    {'cidr': '10.0.1.0/24', 'az': 'us-east-1a', 'public': True},
                    {'cidr': '10.0.2.0/24', 'az': 'us-east-1b', 'public': False},
                    {'cidr': '10.0.3.0/24', 'az': 'us-east-1c', 'public': True}
                ],
                internet_gateway=True,
                nat_gateways=2,
                flow_logs=True,
                vpc_endpoints=1
            )

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_vpcs'] >= 1
            assert mock_db_session.add.called
            # Vérifier que commit a été appelé
            assert mock_db_session.commit.called

    def test_scan_vpc_minimal(self, client_id, mock_db_session, create_vpc):
        """Test : VPC minimal sans ressources supplémentaires"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1')

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            assert result['total_vpcs'] >= 1
            assert mock_db_session.add.called

    def test_scan_invalid_region(self, client_id, mock_db_session):
        """Test : Scanner une région invalide"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['invalid-region-999'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            # Le scan devrait continuer malgré l'erreur
            assert isinstance(result, dict)
            assert 'total_vpcs' in result


class TestVPCScannerIntegration:
    """Tests d'intégration"""

    def test_scan_result_structure(self, client_id, mock_db_session, create_vpc):
        """Test : Validation de la structure du résultat"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1')
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            # Vérifier les champs obligatoires
            required_fields = ['total_vpcs', 'vpcs_by_region', 'scan_run_id']
            for field in required_fields:
                assert field in result, f"Le champ '{field}' devrait être présent"

            # Vérifier les types
            assert isinstance(result['total_vpcs'], int)
            assert isinstance(result['vpcs_by_region'], dict)

    def test_scan_with_no_regions_specified(self, client_id, mock_db_session, create_vpc):
        """Test : Scanner sans spécifier de régions"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1')

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=None)  # Pas de régions

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            # Devrait scanner les régions disponibles
            assert isinstance(result, dict)
            assert result['total_vpcs'] >= 0

    def test_scan_db_operations(self, client_id, mock_db_session, create_vpc):
        """Test : Vérifier les opérations de base de données"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1')
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            result = scanner.scan(mock_db_session)

            # ASSERT
            # Vérifier que les méthodes DB ont été appelées
            assert mock_db_session.add.called, "add() devrait être appelé"
            assert mock_db_session.commit.called, "commit() devrait être appelé"
            assert mock_db_session.flush.called, "flush() devrait être appelé"

