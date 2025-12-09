"""
Scanner VPC pour CloudDiagnoze.

Ce scanner récupère les informations des VPCs AWS et retourne les données.
La sauvegarde en BDD est déléguée au storage_service (même pattern que EC2/S3).
"""

import boto3
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime


class VPCScanner:
    """Scanner pour les VPCs AWS"""

    def __init__(self, session: boto3.Session, client_id: str, regions: List[str] = None):
        """
        Initialise le scanner VPC.

        Args:
            session: Session boto3 authentifiée
            client_id: Identifiant du client
            regions: Liste des régions à scanner (optionnel)
        """
        self.session = session
        self.client_id = client_id
        self.requested_regions = regions

    async def scan(self) -> List[dict]:
        """
        Lance le scan des VPCs.

        Returns:
            Liste de dictionnaires contenant les données des VPCs
        """
        logger.info("🌐 Démarrage du scan VPC")

        # Déterminer les régions à scanner
        if self.requested_regions:
            regions_to_scan = self.requested_regions
            logger.info(f"📍 Régions demandées: {regions_to_scan}")
        else:
            regions_to_scan = self._get_available_regions()
            logger.info(f"📍 Régions disponibles: {regions_to_scan}")

        vpcs_data = []

        # Scanner chaque région
        for region in regions_to_scan:
            try:
                logger.info(f"🔍 Scan de la région {region}...")
                region_vpcs = self._scan_region(region)
                vpcs_data.extend(region_vpcs)
                logger.success(f"✅ {len(region_vpcs)} VPCs trouvés dans {region}")
            except Exception as e:
                logger.error(f"❌ Erreur lors du scan de {region}: {e}")
                continue

        logger.success(f"✅ Scan VPC terminé: {len(vpcs_data)} VPCs trouvés")

        return vpcs_data
    
    def _get_available_regions(self) -> List[str]:
        """Récupère la liste des régions AWS disponibles"""
        try:
            ec2_client = self.session.client('ec2', region_name='us-east-1')
            response = ec2_client.describe_regions()
            return [region['RegionName'] for region in response['Regions']]
        except Exception as e:
            logger.warning(f"⚠️ Impossible de récupérer les régions: {e}")
            return ['eu-west-1', 'eu-west-2', 'eu-west-3']

    def _scan_region(self, region: str) -> List[dict]:
        """
        Scanne une région spécifique.

        Returns:
            Liste des VPCs trouvés dans la région
        """
        ec2_client = self.session.client('ec2', region_name=region)

        # Récupérer tous les VPCs
        response = ec2_client.describe_vpcs()
        vpcs = response.get('Vpcs', [])

        logger.info(f"📊 {len(vpcs)} VPCs trouvés dans {region}")

        # Scanner chaque VPC et collecter les données
        vpcs_data = []
        for vpc in vpcs:
            vpc_data = self._scan_single_vpc(vpc, region, ec2_client)
            if vpc_data:
                vpcs_data.append(vpc_data)

        return vpcs_data

    def _scan_single_vpc(self, vpc: dict, region: str, ec2_client) -> Optional[dict]:
        """Scanne un VPC individuel et retourne ses données"""
        vpc_id = vpc['VpcId']

        try:
            # Récupérer les informations du VPC
            vpc_data = self._extract_vpc_data(vpc, region, ec2_client)

            # Récupérer les métriques de performance
            performance_data = self._extract_vpc_performance(vpc_id, region, ec2_client)

            # Fusionner les données
            vpc_data['performance'] = performance_data
            vpc_data['client_id'] = self.client_id

            logger.debug(f"✅ VPC {vpc_id} scanné")
            return vpc_data

        except Exception as e:
            logger.error(f"❌ Erreur scan VPC {vpc_id}: {e}")
            return None

    def _extract_vpc_data(self, vpc: dict, region: str, ec2_client) -> dict:
        """Extrait les données d'un VPC"""
        vpc_id = vpc['VpcId']

        # Données de base
        data = {
            'vpc_id': vpc_id,
            'cidr_block': vpc.get('CidrBlock'),
            'state': vpc.get('State', 'unknown'),
            'is_default': vpc.get('IsDefault', False),
            'tenancy': vpc.get('InstanceTenancy', 'default'),
            'region': region
        }

        # Compter les subnets
        try:
            subnets_response = ec2_client.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            subnets = subnets_response.get('Subnets', [])
            data['subnet_count'] = len(subnets)

            # Compter subnets publics vs privés
            public_count = 0
            private_count = 0
            azs = set()

            for subnet in subnets:
                azs.add(subnet.get('AvailabilityZone'))
                if subnet.get('MapPublicIpOnLaunch', False):
                    public_count += 1
                else:
                    private_count += 1

            data['public_subnets_count'] = public_count
            data['private_subnets_count'] = private_count
            data['availability_zones'] = list(azs)  # Stocker la liste des AZs

        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération subnets pour {vpc_id}: {e}")
            data['subnet_count'] = 0
            data['public_subnets_count'] = 0
            data['private_subnets_count'] = 0
            data['availability_zones'] = []

        # Internet Gateway
        try:
            igw_response = ec2_client.describe_internet_gateways(
                Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
            )
            data['internet_gateway_attached'] = len(igw_response.get('InternetGateways', [])) > 0
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération IGW pour {vpc_id}: {e}")
            data['internet_gateway_attached'] = False

        # NAT Gateways
        try:
            nat_response = ec2_client.describe_nat_gateways(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            data['nat_gateways_count'] = len(nat_response.get('NatGateways', []))
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération NAT pour {vpc_id}: {e}")
            data['nat_gateways_count'] = 0

        # Route Tables
        try:
            rt_response = ec2_client.describe_route_tables(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            data['route_tables_count'] = len(rt_response.get('RouteTables', []))
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération route tables pour {vpc_id}: {e}")
            data['route_tables_count'] = 0

        # Security Groups
        try:
            sg_response = ec2_client.describe_security_groups(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            data['security_groups_count'] = len(sg_response.get('SecurityGroups', []))
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération security groups pour {vpc_id}: {e}")
            data['security_groups_count'] = 0

        # Network ACLs
        try:
            acl_response = ec2_client.describe_network_acls(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            data['network_acls_count'] = len(acl_response.get('NetworkAcls', []))
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération ACLs pour {vpc_id}: {e}")
            data['network_acls_count'] = 0

        # VPC Endpoints
        try:
            endpoint_response = ec2_client.describe_vpc_endpoints(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            data['vpc_endpoints_count'] = len(endpoint_response.get('VpcEndpoints', []))
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération endpoints pour {vpc_id}: {e}")
            data['vpc_endpoints_count'] = 0

        # Flow Logs
        try:
            flow_logs_response = ec2_client.describe_flow_logs(
                Filters=[{'Name': 'resource-id', 'Values': [vpc_id]}]
            )
            data['flow_logs_enabled'] = len(flow_logs_response.get('FlowLogs', [])) > 0
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération flow logs pour {vpc_id}: {e}")
            data['flow_logs_enabled'] = False

        # Tags
        tags = vpc.get('Tags', [])
        data['tags'] = ','.join([f"{tag['Key']}={tag['Value']}" for tag in tags]) if tags else None

        return data

    def _extract_vpc_performance(self, vpc_id: str, region: str, ec2_client) -> dict:
        """Extrait les métriques de performance d'un VPC et retourne un dictionnaire"""
        performance_data = {
            "network_in_bytes": 0,
            "network_out_bytes": 0,
            "network_packets_in": 0,
            "network_packets_out": 0
        }

        # Pour les VPCs, les métriques sont principalement au niveau des NAT Gateways
        try:
            nat_response = ec2_client.describe_nat_gateways(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            nat_gateways = nat_response.get('NatGateways', [])

            if nat_gateways:
                logger.debug(f"📊 {len(nat_gateways)} NAT Gateways trouvés pour {vpc_id}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération métriques pour {vpc_id}: {e}")

        return performance_data


