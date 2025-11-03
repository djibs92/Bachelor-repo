
from api.services.ScanAbstraction.create_cloud_scanne import CloudScanner
from api.models.event_2cbp import Event2CBP
from typing import List
from loguru import logger
import boto3
import asyncio

class VPCScanner(CloudScanner):
    def __init__(self, session: boto3.session, client_id: str, regions: List[str] = None):
        super().__init__(session, client_id)
        self.requested_regions = regions
        
    async def scan(self) -> List[Event2CBP]:
        """Scan des VPCs"""
        logger.info("🌐 Start scan VPC")
        
        try:
            # Déterminer les régions à scanner
            if self.requested_regions:
                regions_to_scan = self.requested_regions
                logger.info(f"📍 Régions demandées: {regions_to_scan}")
            else:
                regions_to_scan = self._get_authorized_regions()
                logger.info(f"📍 Régions autorisées: {regions_to_scan}")
            
            # 🚀 PARALLÉLISATION DES RÉGIONS
            logger.info(f"🚀 Lancement scan parallèle de {len(regions_to_scan)} régions")
            tasks = [self._scan_region(region) for region in regions_to_scan]
            region_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Fusionner tous les événements
            all_events = []
            for i, result in enumerate(region_results):
                if isinstance(result, list):
                    all_events.extend(result)
                    logger.success(f"✅ Région {regions_to_scan[i]}: {len(result)} événements VPC")
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ Région {regions_to_scan[i]} échouée: {result}")
            
            logger.success(f"🌐 Scan VPC terminé: {len(all_events)} événements total")
            return all_events
            
        except Exception as e:
            logger.error(f"❌ Erreur scan VPC: {e}")
            raise

    async def _scan_region(self, region: str) -> List[Event2CBP]:
        """Scan une région spécifique"""
        events = []
        
        try:
            ec2_client = self.get_client('ec2', region)
            
            # Récupérer tous les VPCs
            response = ec2_client.describe_vpcs()
            vpcs = response.get('Vpcs', [])
            
            logger.info(f"📊 {len(vpcs)} VPCs trouvés dans {region}")
            
            # Scanner chaque VPC
            for vpc in vpcs:
                vpc_events = await self._scan_single_vpc(vpc, region, ec2_client)
                events.extend(vpc_events)
                
        except Exception as e:
            logger.error(f"❌ Erreur scan région {region}: {e}")
            raise
            
        return events

    async def _scan_single_vpc(self, vpc: dict, region: str, ec2_client) -> List[Event2CBP]:
        """Scan un VPC avec tous ses extracteurs"""
        events = []
        vpc_arn = self._build_vpc_arn(vpc, region)
        
        # Extracteurs MÉTADONNÉES "coup sûr"
        basic_extractors = [
            self._extract_vpc_info,
            self._extract_vpc_state,
            self._extract_vpc_tenancy,
            self._extract_is_default,
            self._extract_subnet_count,
            self._extract_availability_zones,
            self._extract_internet_gateway,
            self._extract_nat_gateways,
            self._extract_route_tables_count,
        ]

        # Extracteurs SÉCURITÉ (permissions requises)
        security_extractors = [
            self._extract_security_groups,
            self._extract_network_acls,
            self._extract_flow_logs,
            self._extract_vpc_endpoints,
        ]

        # Exécuter extracteurs basiques
        for extractor in basic_extractors:
            try:
                extracted_events = extractor(vpc, vpc_arn, ec2_client, region)
                if extracted_events:
                    if isinstance(extracted_events, list):
                        events.extend(extracted_events)
                    else:
                        events.append(extracted_events)
            except Exception as e:
                logger.warning(f"⚠️ Erreur {extractor.__name__} pour {vpc_arn}: {e}")

        # Exécuter extracteurs sécurité
        for extractor in security_extractors:
            try:
                extracted_events = extractor(vpc, vpc_arn, ec2_client, region)
                if extracted_events:
                    if isinstance(extracted_events, list):
                        events.extend(extracted_events)
                    else:
                        events.append(extracted_events)
            except Exception as e:
                logger.warning(f"⚠️ Erreur sécurité {extractor.__name__} pour {vpc_arn}: {e}")

        return events

    def _build_vpc_arn(self, vpc: dict, region: str) -> str:
        """Construit l'ARN du VPC"""
        # VPC n'a pas d'OwnerId dans la réponse, contrairement à EC2
        try:
            sts_client = self.get_client('sts', region)
            response = sts_client.get_caller_identity()
            account_id = response['Account']
        except Exception:
            account_id = "unknown"
        
        vpc_id = vpc['VpcId']
        return f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"

    # ========================================
    # EXTRACTEURS MÉTADONNÉES "COUP SÛR"
    # ========================================

    def _extract_vpc_info(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> List[Event2CBP]:
        """Extrait les infos basiques du VPC"""
        events = []
        
        # VPC ID
        events.append(self._create_event(
            resource_id=vpc_arn,
            metric_type="aws.metadata.vpc.vpc_id",
            metric_value=vpc['VpcId']
        ))
        
        # CIDR Block
        events.append(self._create_event(
            resource_id=vpc_arn,
            metric_type="aws.metadata.vpc.cidr_block",
            metric_value=vpc['CidrBlock']
        ))
        
        return events

    def _extract_vpc_state(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> Event2CBP:
        """Extrait l'état du VPC"""
        return self._create_event(
            resource_id=vpc_arn,
            metric_type="aws.metadata.vpc.state",
            metric_value=vpc['State']
        )

    def _extract_vpc_tenancy(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> Event2CBP:
        """Extrait le type de tenancy"""
        return self._create_event(
            resource_id=vpc_arn,
            metric_type="aws.metadata.vpc.instance_tenancy",
            metric_value=vpc.get('InstanceTenancy', 'default')
        )

    def _extract_is_default(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> Event2CBP:
        """Indique si c'est le VPC par défaut"""
        return self._create_event(
            resource_id=vpc_arn,
            metric_type="aws.metadata.vpc.is_default",
            metric_value=vpc.get('IsDefault', False)
        )

    def _extract_subnet_count(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> List[Event2CBP]:
        """Compte les subnets du VPC"""
        events = []
        
        try:
            response = ec2_client.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}]
            )
            subnets = response.get('Subnets', [])
            
            # Compter total
            events.append(self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.metadata.vpc.subnet_count",
                metric_value=len(subnets)
            ))
            
            # Compter publics vs privés
            public_count = sum(1 for subnet in subnets if subnet.get('MapPublicIpOnLaunch', False))
            private_count = len(subnets) - public_count
            
            events.append(self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.metadata.vpc.public_subnets_count",
                metric_value=public_count
            ))
            
            events.append(self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.metadata.vpc.private_subnets_count",
                metric_value=private_count
            ))
            
        except Exception as e:
            logger.warning(f"Erreur comptage subnets pour {vpc['VpcId']}: {e}")
            return []
            
        return events

    def _extract_availability_zones(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> Event2CBP:
        """Extrait les zones de disponibilité utilisées"""
        try:
            response = ec2_client.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}]
            )
            subnets = response.get('Subnets', [])
            
            # Récupérer les AZ uniques
            availability_zones = list(set(subnet['AvailabilityZone'] for subnet in subnets))
            
            return self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.metadata.vpc.availability_zones",
                metric_value=availability_zones
            )
            
        except Exception as e:
            logger.warning(f"Erreur AZ pour {vpc['VpcId']}: {e}")
            return None

    def _extract_internet_gateway(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> Event2CBP:
        """Vérifie si un Internet Gateway est attaché"""
        try:
            response = ec2_client.describe_internet_gateways(
                Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc['VpcId']]}]
            )
            igws = response.get('InternetGateways', [])
            
            return self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.metadata.vpc.internet_gateway_attached",
                metric_value=len(igws) > 0
            )
            
        except Exception as e:
            logger.warning(f"Erreur IGW pour {vpc['VpcId']}: {e}")
            return None

    def _extract_nat_gateways(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> Event2CBP:
        """Compte les NAT Gateways"""
        try:
            response = ec2_client.describe_nat_gateways(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}]
            )
            nat_gateways = response.get('NatGateways', [])
            
            return self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.metadata.vpc.nat_gateways_count",
                metric_value=len(nat_gateways)
            )
            
        except Exception as e:
            logger.warning(f"Erreur NAT Gateway pour {vpc['VpcId']}: {e}")
            return None

    def _extract_route_tables_count(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> Event2CBP:
        """Compte les tables de routage"""
        try:
            response = ec2_client.describe_route_tables(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}]
            )
            route_tables = response.get('RouteTables', [])
            
            return self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.metadata.vpc.route_tables_count",
                metric_value=len(route_tables)
            )
            
        except Exception as e:
            logger.warning(f"Erreur route tables pour {vpc['VpcId']}: {e}")
            return None

    def _get_authorized_regions(self) -> List[str]:
        """Récupère les régions autorisées"""
        try:
            ec2_client = self.get_client('ec2', 'us-east-1')
            response = ec2_client.describe_regions()
            
            authorized = []
            for region in response['Regions']:
                region_name = region['RegionName']
                try:
                    test_client = self.get_client('ec2', region_name)
                    test_client.describe_vpcs()
                    authorized.append(region_name)
                    logger.info(f"✅ Région {region_name} accessible")
                except Exception as e:
                    logger.warning(f"⚠️ Région {region_name} inaccessible: {e}")
                    self.invalidate_client('ec2', region_name)
                    continue
            
            return authorized if authorized else ['us-east-1']
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération régions: {e}")
            return ['us-east-1']

    def _extract_security_groups(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> List[Event2CBP]:
        """Extrait les Security Groups du VPC"""
        events = []
        
        try:
            response = ec2_client.describe_security_groups(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}]
            )
            security_groups = response.get('SecurityGroups', [])
            
            # Compter total
            events.append(self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.security.vpc.security_groups_count",
                metric_value=len(security_groups)
            ))
            
            # Analyser règles ouvertes (0.0.0.0/0)
            open_rules_count = 0
            for sg in security_groups:
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            open_rules_count += 1
        
            events.append(self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.security.vpc.open_security_rules_count",
                metric_value=open_rules_count
            ))
        
        except Exception as e:
            logger.warning(f"Erreur Security Groups pour {vpc['VpcId']}: {e}")
            return []
        
        return events
        # Permissions requises: ec2:DescribeSecurityGroups

    def _extract_network_acls(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> Event2CBP:
        """Extrait les Network ACLs du VPC"""
        try:
            response = ec2_client.describe_network_acls(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}]
            )
            network_acls = response.get('NetworkAcls', [])
            
            return self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.security.vpc.network_acls_count",
                metric_value=len(network_acls)
            )
        
        except Exception as e:
            logger.warning(f"Erreur Network ACLs pour {vpc['VpcId']}: {e}")
            return None
        # Permissions requises: ec2:DescribeNetworkAcls

    def _extract_flow_logs(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> Event2CBP:
        """Vérifie si Flow Logs sont activés"""
        try:
            response = ec2_client.describe_flow_logs(
                Filters=[
                    {'Name': 'resource-id', 'Values': [vpc['VpcId']]},
                    {'Name': 'resource-type', 'Values': ['VPC']}
                ]
            )
            flow_logs = response.get('FlowLogs', [])
            
            # Vérifier si au moins un Flow Log est actif
            active_flow_logs = [fl for fl in flow_logs if fl.get('FlowLogStatus') == 'ACTIVE']
            
            return self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.security.vpc.flow_logs_enabled",
                metric_value=len(active_flow_logs) > 0
            )
        
        except Exception as e:
            logger.warning(f"Erreur Flow Logs pour {vpc['VpcId']}: {e}")
            return None
        # Permissions requises: ec2:DescribeFlowLogs

    def _extract_vpc_endpoints(self, vpc: dict, vpc_arn: str, ec2_client, region: str) -> Event2CBP:
        """Compte les VPC Endpoints"""
        try:
            response = ec2_client.describe_vpc_endpoints(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}]
            )
            vpc_endpoints = response.get('VpcEndpoints', [])
            
            return self._create_event(
                resource_id=vpc_arn,
                metric_type="aws.security.vpc.vpc_endpoints_count",
                metric_value=len(vpc_endpoints)
            )
        
        except Exception as e:
            logger.warning(f"Erreur VPC Endpoints pour {vpc['VpcId']}: {e}")
            return None
        # Permissions requises: ec2:DescribeVpcEndpoints

