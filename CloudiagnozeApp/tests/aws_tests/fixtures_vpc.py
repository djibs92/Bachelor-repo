"""
Fixtures pytest pour les tests du scanner VPC
"""
import pytest
import boto3
from moto import mock_aws
from faker import Faker


@pytest.fixture
def ec2_client():
    """Client EC2 mocké pour les tests VPC"""
    def _create_client(region='us-east-1'):
        return boto3.client('ec2', region_name=region)
    return _create_client


@pytest.fixture
def create_vpc(faker_instance: Faker):
    """
    Factory fixture pour créer un VPC mocké avec toutes ses ressources.
    
    Usage:
        vpc_id = create_vpc(region='us-east-1', cidr='10.0.0.0/16')
    """
    def _create_vpc(
        region='us-east-1',
        cidr='10.0.0.0/16',
        is_default=False,
        tenancy='default',
        tags=None,
        subnets=None,
        internet_gateway=False,
        nat_gateways=0,
        flow_logs=False,
        vpc_endpoints=0
    ):
        """
        Crée un VPC avec ses ressources associées.
        
        Args:
            region: Région AWS
            cidr: Bloc CIDR du VPC
            is_default: Si c'est le VPC par défaut
            tenancy: Type de tenancy (default, dedicated)
            tags: Dictionnaire de tags
            subnets: Liste de dicts avec config des subnets
                     Ex: [{'cidr': '10.0.1.0/24', 'az': 'us-east-1a', 'public': True}]
            internet_gateway: Attacher un Internet Gateway
            nat_gateways: Nombre de NAT Gateways à créer
            flow_logs: Activer les flow logs
            vpc_endpoints: Nombre de VPC endpoints à créer
        
        Returns:
            vpc_id: ID du VPC créé
        """
        ec2_client = boto3.client('ec2', region_name=region)
        
        # Créer le VPC
        vpc_response = ec2_client.create_vpc(
            CidrBlock=cidr,
            InstanceTenancy=tenancy
        )
        vpc_id = vpc_response['Vpc']['VpcId']
        
        # Ajouter des tags
        if tags:
            tag_list = [{'Key': k, 'Value': v} for k, v in tags.items()]
            ec2_client.create_tags(Resources=[vpc_id], Tags=tag_list)
        
        # Créer des subnets
        if subnets:
            for subnet_config in subnets:
                subnet_response = ec2_client.create_subnet(
                    VpcId=vpc_id,
                    CidrBlock=subnet_config.get('cidr', '10.0.1.0/24'),
                    AvailabilityZone=subnet_config.get('az', f'{region}a')
                )
                subnet_id = subnet_response['Subnet']['SubnetId']
                
                # Configurer comme subnet public si demandé
                if subnet_config.get('public', False):
                    ec2_client.modify_subnet_attribute(
                        SubnetId=subnet_id,
                        MapPublicIpOnLaunch={'Value': True}
                    )
        
        # Attacher un Internet Gateway
        if internet_gateway:
            igw_response = ec2_client.create_internet_gateway()
            igw_id = igw_response['InternetGateway']['InternetGatewayId']
            ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        
        # Créer des NAT Gateways
        if nat_gateways > 0 and subnets:
            # Besoin d'un subnet public pour créer un NAT Gateway
            public_subnets = [s for s in subnets if s.get('public', False)]
            if public_subnets:
                for i in range(min(nat_gateways, len(public_subnets))):
                    subnet_cidr = public_subnets[i].get('cidr', '10.0.1.0/24')
                    subnet_az = public_subnets[i].get('az', f'{region}a')
                    
                    # Récupérer le subnet ID
                    subnets_response = ec2_client.describe_subnets(
                        Filters=[
                            {'Name': 'vpc-id', 'Values': [vpc_id]},
                            {'Name': 'cidr-block', 'Values': [subnet_cidr]}
                        ]
                    )
                    if subnets_response['Subnets']:
                        subnet_id = subnets_response['Subnets'][0]['SubnetId']
                        
                        # Allouer une Elastic IP
                        eip_response = ec2_client.allocate_address(Domain='vpc')
                        allocation_id = eip_response['AllocationId']
                        
                        # Créer le NAT Gateway
                        ec2_client.create_nat_gateway(
                            SubnetId=subnet_id,
                            AllocationId=allocation_id
                        )
        
        # Activer les flow logs
        if flow_logs:
            try:
                ec2_client.create_flow_logs(
                    ResourceIds=[vpc_id],
                    ResourceType='VPC',
                    TrafficType='ALL',
                    LogDestinationType='cloud-watch-logs',
                    LogGroupName=f'/aws/vpc/flowlogs/{vpc_id}'
                )
            except Exception:
                # Moto peut ne pas supporter complètement les flow logs
                pass
        
        # Créer des VPC endpoints
        if vpc_endpoints > 0:
            for i in range(vpc_endpoints):
                try:
                    ec2_client.create_vpc_endpoint(
                        VpcId=vpc_id,
                        ServiceName=f'com.amazonaws.{region}.s3',
                        VpcEndpointType='Gateway'
                    )
                except Exception:
                    # Moto peut ne pas supporter tous les types d'endpoints
                    pass
        
        return vpc_id
    
    return _create_vpc


@pytest.fixture
def create_multiple_vpcs(create_vpc, faker_instance: Faker):
    """
    Factory fixture pour créer plusieurs VPCs.
    
    Usage:
        vpc_ids = create_multiple_vpcs(count=3, region='us-east-1')
    """
    def _create_multiple(count=3, region='us-east-1', **kwargs):
        vpc_ids = []
        for i in range(count):
            # Générer un CIDR unique pour chaque VPC
            cidr = f'10.{i}.0.0/16'
            vpc_id = create_vpc(region=region, cidr=cidr, **kwargs)
            vpc_ids.append(vpc_id)
        return vpc_ids
    
    return _create_multiple

