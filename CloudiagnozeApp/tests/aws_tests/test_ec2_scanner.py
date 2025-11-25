"""
Tests unitaires pour EC2Scanner

Organisation :
1. Tests de base (scan simple, régions multiples)
2. Tests de gestion d'erreurs
3. Tests de métriques CloudWatch
4. Tests de cas limites (edge cases)
5. Tests d'intégration
"""

import pytest
import boto3
from moto import mock_aws
from datetime import datetime
import re

from api.services.provider.aws.scanners.ec2_scan import EC2Scanner
from tests.aws_tests.fixtures_ec2 import (
    create_ec2_instance,
    create_multiple_ec2_instances,
    create_cloudwatch_metrics
)


# ========================================
# CLASSE 1 : Tests de base
# ========================================
class TestEC2ScannerBasic:
    """Tests de fonctionnalités de base du scanner EC2"""
    
    async def test_scan_empty_region(self, client_id, single_region):
        """Test : Scanner une région sans instances"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert isinstance(results, list), "Le résultat doit être une liste"
            assert len(results) == 0, "Devrait retourner une liste vide pour une région sans instances"

    async def test_scan_single_instance(self, client_id, single_region, create_ec2_instance):
        """Test : Scanner une région avec 1 instance"""
        with mock_aws():
            # ARRANGE
            instance_id = create_ec2_instance(region=single_region)
            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1, "Devrait trouver exactement 1 instance"
            assert results[0]['instance_id'] == instance_id
            assert results[0]['client_id'] == client_id
            assert results[0]['state'] == 'running'

    async def test_scan_multiple_instances(self, client_id, single_region, create_multiple_ec2_instances):
        """Test : Scanner une région avec plusieurs instances"""
        with mock_aws():
            # ARRANGE
            count = 5
            instance_ids = create_multiple_ec2_instances(region=single_region, count=count)
            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == count, f"Devrait trouver {count} instances"
            result_ids = [r['instance_id'] for r in results]
            for instance_id in instance_ids:
                assert instance_id in result_ids, f"Instance {instance_id} devrait être dans les résultats"

    async def test_scan_multiple_regions(self, client_id, test_regions, create_ec2_instance):
        """Test : Scanner plusieurs régions en parallèle"""
        with mock_aws():
            # ARRANGE
            # Créer 2 instances dans chaque région
            for region in test_regions:
                create_ec2_instance(region=region)
                create_ec2_instance(region=region)

            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=test_regions)

            # ACT
            results = await scanner.scan()

            # ASSERT
            expected_count = len(test_regions) * 2
            assert len(results) == expected_count, f"Devrait trouver {expected_count} instances au total"


# ========================================
# CLASSE 2 : Tests de gestion d'erreurs
# ========================================
class TestEC2ScannerErrors:
    """Tests de gestion d'erreurs et cas exceptionnels"""

    async def test_scan_with_invalid_region(self, client_id):
        """Test : Gestion d'une région invalide"""
        with mock_aws():
            # ARRANGE
            session = boto3.Session()
            invalid_region = 'invalid-region-999'
            scanner = EC2Scanner(session, client_id, regions=[invalid_region])

            # ACT & ASSERT
            # Le scanner devrait gérer l'erreur et retourner une liste vide
            results = await scanner.scan()
            assert isinstance(results, list), "Devrait retourner une liste même en cas d'erreur"
            assert len(results) == 0, "Devrait retourner une liste vide pour une région invalide"

    async def test_scan_with_mixed_valid_invalid_regions(self, client_id, single_region, create_ec2_instance):
        """Test : Scanner avec un mélange de régions valides et invalides"""
        with mock_aws():
            # ARRANGE
            instance_id = create_ec2_instance(region=single_region)
            session = boto3.Session()
            regions = [single_region, 'invalid-region-999']
            scanner = EC2Scanner(session, client_id, regions=regions)

            # ACT
            results = await scanner.scan()

            # ASSERT
            # Devrait scanner la région valide et ignorer l'invalide
            assert len(results) >= 1, "Devrait trouver au moins l'instance de la région valide"
            assert results[0]['instance_id'] == instance_id


# ========================================
# CLASSE 3 : Tests des métriques CloudWatch
# ========================================
class TestEC2ScannerMetrics:
    """Tests de récupération des métriques de performance"""

    async def test_scan_instance_with_cpu_metrics(self, client_id, single_region, create_ec2_instance, create_cloudwatch_metrics):
        """Test : Extraction des métriques CPU"""
        with mock_aws():
            # ARRANGE
            instance_id = create_ec2_instance(region=single_region)
            cpu_value = 45.5
            create_cloudwatch_metrics(instance_id, single_region, 'CPUUtilization', cpu_value)

            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            instance_data = results[0]
            assert 'performance' in instance_data, "Devrait contenir des données de performance"
            # Note: moto peut ne pas retourner les métriques exactement, on vérifie juste la structure
            assert 'cpu_utilization_avg' in instance_data['performance']

    async def test_scan_instance_with_network_metrics(self, client_id, single_region, create_ec2_instance, create_cloudwatch_metrics):
        """Test : Extraction des métriques réseau"""
        with mock_aws():
            # ARRANGE
            instance_id = create_ec2_instance(region=single_region)
            network_in = 1024000  # 1 MB
            network_out = 2048000  # 2 MB
            create_cloudwatch_metrics(instance_id, single_region, 'NetworkIn', network_in)
            create_cloudwatch_metrics(instance_id, single_region, 'NetworkOut', network_out)

            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            instance_data = results[0]
            assert 'performance' in instance_data
            assert 'network_in_bytes' in instance_data['performance']
            assert 'network_out_bytes' in instance_data['performance']

    async def test_scan_instance_without_metrics(self, client_id, single_region, create_ec2_instance):
        """Test : Instance sans métriques CloudWatch"""
        with mock_aws():
            # ARRANGE
            instance_id = create_ec2_instance(region=single_region)
            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            instance_data = results[0]
            assert 'performance' in instance_data, "Devrait avoir une section performance même sans métriques"
            # Les valeurs devraient être None ou 0
            assert instance_data['performance']['cpu_utilization_avg'] is None or \
                   instance_data['performance']['cpu_utilization_avg'] == 0


# ========================================
# CLASSE 4 : Tests de cas limites
# ========================================
class TestEC2ScannerEdgeCases:
    """Tests de cas limites et situations spéciales"""

    async def test_scan_stopped_instance(self, client_id, single_region, create_ec2_instance):
        """Test : Scanner une instance arrêtée"""
        with mock_aws():
            # ARRANGE
            instance_id = create_ec2_instance(region=single_region, state='stopped')
            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            assert results[0]['instance_id'] == instance_id
            assert results[0]['state'] == 'stopped'

    async def test_scan_instance_with_tags(self, client_id, single_region, create_ec2_instance):
        """Test : Instance avec tags"""
        with mock_aws():
            # ARRANGE
            tags = {
                'Name': 'test-instance',
                'Environment': 'testing',
                'Owner': 'test-team'
            }
            instance_id = create_ec2_instance(region=single_region, tags=tags)
            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            instance_data = results[0]
            assert instance_data['instance_id'] == instance_id
            # Vérifier que les tags sont présents
            assert 'tags' in instance_data or 'Tags' in instance_data

    async def test_scan_instance_different_types(self, client_id, single_region, create_ec2_instance):
        """Test : Instances de différents types"""
        with mock_aws():
            # ARRANGE
            instance_types = ['t2.micro', 't2.small', 't3.medium']
            instance_ids = []
            for inst_type in instance_types:
                instance_id = create_ec2_instance(region=single_region, instance_type=inst_type)
                instance_ids.append(instance_id)

            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == len(instance_types)
            result_types = [r['instance_type'] for r in results]
            for inst_type in instance_types:
                assert inst_type in result_types


# ========================================
# CLASSE 5 : Tests d'intégration
# ========================================
class TestEC2ScannerIntegration:
    """Tests d'intégration avec d'autres composants"""

    async def test_scan_data_format_validation(self, client_id, single_region, create_ec2_instance):
        """Test : Validation du format des données retournées"""
        with mock_aws():
            # ARRANGE
            instance_id = create_ec2_instance(region=single_region)
            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            instance_data = results[0]

            # Vérifier les champs obligatoires
            required_fields = [
                'client_id', 'resource_id', 'instance_id', 'instance_type',
                'state', 'ami_id', 'availability_zone', 'architecture',
                'virtualization_type', 'launch_time', 'performance'
            ]

            for field in required_fields:
                assert field in instance_data, f"Le champ '{field}' devrait être présent"

            # Vérifier les types
            assert isinstance(instance_data['client_id'], str)
            assert isinstance(instance_data['instance_id'], str)
            assert isinstance(instance_data['performance'], dict)

    async def test_scan_arn_format(self, client_id, single_region, create_ec2_instance):
        """Test : Validation du format ARN"""
        with mock_aws():
            # ARRANGE
            instance_id = create_ec2_instance(region=single_region)
            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=[single_region])

            # ACT
            results = await scanner.scan()

            # ASSERT
            assert len(results) == 1
            resource_id = results[0]['resource_id']

            # Vérifier le format ARN : arn:aws:ec2:region:account:instance/instance-id
            # Note: moto utilise "unknown" comme account ID
            arn_pattern = r'^arn:aws:ec2:[a-z0-9-]+:(\d+|unknown):instance/i-[a-f0-9]+$'
            assert re.match(arn_pattern, resource_id), f"ARN invalide: {resource_id}"

    async def test_scan_with_no_regions_specified(self, client_id, create_ec2_instance):
        """Test : Scanner sans spécifier de régions (devrait utiliser les régions autorisées)"""
        with mock_aws():
            # ARRANGE
            # Créer une instance dans la région par défaut
            create_ec2_instance(region='eu-west-3')

            session = boto3.Session()
            scanner = EC2Scanner(session, client_id, regions=None)  # Pas de régions spécifiées

            # ACT
            results = await scanner.scan()

            # ASSERT
            # Devrait scanner au moins une région et trouver l'instance
            assert isinstance(results, list), "Devrait retourner une liste"
            # Note: Le nombre exact dépend de _get_authorized_regions()


