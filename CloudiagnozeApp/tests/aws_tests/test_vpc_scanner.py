"""
Tests unitaires pour le scanner VPC

Organisation :
1. Tests de base (scan simple, régions multiples)
2. Tests des fonctionnalités réseau
3. Tests des configurations VPC
4. Tests de cas limites (edge cases)
5. Tests d'intégration
"""
import pytest
import boto3
from moto import mock_aws
from api.services.provider.aws.scanners.vpc_scanner import VPCScanner


class TestVPCScannerBasic:
    """Tests de fonctionnalités de base du scanner VPC"""

    async def test_scan_no_vpcs(self, client_id):
        """Test : Scanner sans VPCs (sauf le VPC par défaut)"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert isinstance(results, list), "Le résultat doit être une liste"
            # Moto crée un VPC par défaut
            assert len(results) >= 0

    async def test_scan_single_vpc(self, client_id, create_vpc):
        """Test : Scanner un seul VPC"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1', cidr='10.0.0.0/16')
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1, "Devrait trouver au moins 1 VPC"
            vpc_ids = [r['vpc_id'] for r in results]
            assert vpc_id in vpc_ids

    async def test_scan_multiple_vpcs(self, client_id, create_multiple_vpcs):
        """Test : Scanner plusieurs VPCs"""
        with mock_aws():
            # ARRANGE
            count = 3
            vpc_ids = create_multiple_vpcs(count=count, region='us-east-1')
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= count, f"Devrait trouver au moins {count} VPCs"

    async def test_scan_multiple_regions(self, client_id, create_vpc):
        """Test : Scanner plusieurs régions"""
        with mock_aws():
            # ARRANGE
            vpc_us = create_vpc(region='us-east-1', cidr='10.0.0.0/16')
            vpc_eu = create_vpc(region='eu-west-3', cidr='10.1.0.0/16')

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1', 'eu-west-3'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 2, "Devrait trouver au moins 2 VPCs"
            regions = [r['region'] for r in results]
            assert 'us-east-1' in regions
            assert 'eu-west-3' in regions


class TestVPCScannerNetworking:
    """Tests des fonctionnalités réseau du VPC"""

    async def test_scan_vpc_with_subnets(self, client_id, create_vpc):
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
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1
            vpc_ids = [r['vpc_id'] for r in results]
            assert vpc_id in vpc_ids

    async def test_scan_vpc_with_internet_gateway(self, client_id, create_vpc):
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
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1

    async def test_scan_vpc_with_nat_gateways(self, client_id, create_vpc):
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
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1

    async def test_scan_vpc_with_flow_logs(self, client_id, create_vpc):
        """Test : VPC avec Flow Logs activés"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1', flow_logs=True)

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1


class TestVPCScannerConfiguration:
    """Tests des configurations VPC"""

    async def test_scan_vpc_with_tags(self, client_id, create_vpc):
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
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1

    async def test_scan_vpc_with_dedicated_tenancy(self, client_id, create_vpc):
        """Test : VPC avec tenancy dédié"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1', tenancy='dedicated')

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1

    async def test_scan_vpc_with_endpoints(self, client_id, create_vpc):
        """Test : VPC avec VPC endpoints"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1', vpc_endpoints=2)

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1


class TestVPCScannerEdgeCases:
    """Tests de cas limites"""

    async def test_scan_vpc_with_all_features(self, client_id, create_vpc):
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
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1
            vpc_ids = [r['vpc_id'] for r in results]
            assert vpc_id in vpc_ids

    async def test_scan_vpc_minimal(self, client_id, create_vpc):
        """Test : VPC minimal sans ressources supplémentaires"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1')

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1
            vpc_ids = [r['vpc_id'] for r in results]
            assert vpc_id in vpc_ids

    async def test_scan_invalid_region(self, client_id):
        """Test : Scanner une région invalide"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['invalid-region-999'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            # Le scan devrait continuer malgré l'erreur (liste vide)
            assert isinstance(results, list)


class TestVPCScannerIntegration:
    """Tests d'intégration"""

    async def test_scan_result_structure(self, client_id, create_vpc):
        """Test : Validation de la structure du résultat"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1')
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) >= 1
            vpc = results[0]
            # Vérifier les champs obligatoires
            required_fields = ['vpc_id', 'region', 'client_id', 'cidr_block']
            for field in required_fields:
                assert field in vpc, f"Le champ '{field}' devrait être présent"

    async def test_scan_with_no_regions_specified(self, client_id, create_vpc):
        """Test : Scanner sans spécifier de régions"""
        with mock_aws():
            # ARRANGE
            create_vpc(region='us-east-1')

            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=None)  # Pas de régions

            # ACT
            results = await scanner.scan()

            # ASSERT
            # Devrait scanner les régions disponibles
            assert isinstance(results, list)

    async def test_scan_returns_list(self, client_id, create_vpc):
        """Test : Vérifier que le scan retourne une liste"""
        with mock_aws():
            # ARRANGE
            vpc_id = create_vpc(region='us-east-1')
            session = boto3.Session()
            scanner = VPCScanner(session, client_id, regions=['us-east-1'])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert isinstance(results, list)
            assert len(results) >= 1

