"""
Fixtures spécifiques pour les tests EC2
"""
import pytest
import boto3
from moto import mock_aws
from datetime import datetime, timedelta


@pytest.fixture
def ec2_client(single_region):
    """Crée un client EC2 mocké"""
    with mock_aws():
        yield boto3.client('ec2', region_name=single_region)


@pytest.fixture
def cloudwatch_client(single_region):
    """Crée un client CloudWatch mocké"""
    with mock_aws():
        yield boto3.client('cloudwatch', region_name=single_region)


@pytest.fixture
def create_ec2_instance():
    """
    Factory pour créer des instances EC2 de test.

    Usage:
        instance_id = create_ec2_instance(region='eu-west-3', instance_type='t2.micro')
    """
    def _create(
        region='eu-west-3',
        instance_type='t2.micro',
        state='running',
        ami_id='ami-12345678',
        tags=None,
        vpc_id=None,
        subnet_id=None,
        public_ip=True
    ):
        ec2 = boto3.client('ec2', region_name=region)
        
        # Créer un VPC si nécessaire
        if vpc_id is None:
            vpc_response = ec2.create_vpc(CidrBlock='10.0.0.0/16')
            vpc_id = vpc_response['Vpc']['VpcId']
        
        # Créer un subnet si nécessaire
        if subnet_id is None:
            subnet_response = ec2.create_subnet(
                VpcId=vpc_id,
                CidrBlock='10.0.1.0/24',
                AvailabilityZone=f'{region}a'
            )
            subnet_id = subnet_response['Subnet']['SubnetId']
        
        # Paramètres de l'instance
        run_params = {
            'ImageId': ami_id,
            'InstanceType': instance_type,
            'MinCount': 1,
            'MaxCount': 1,
            'SubnetId': subnet_id
        }
        
        # Ajouter des tags si fournis
        if tags:
            run_params['TagSpecifications'] = [{
                'ResourceType': 'instance',
                'Tags': [{'Key': k, 'Value': v} for k, v in tags.items()]
            }]
        
        # Créer l'instance
        response = ec2.run_instances(**run_params)
        instance_id = response['Instances'][0]['InstanceId']
        
        # Changer l'état si nécessaire
        if state == 'stopped':
            ec2.stop_instances(InstanceIds=[instance_id])
        elif state == 'terminated':
            ec2.terminate_instances(InstanceIds=[instance_id])
        
        return instance_id
    
    return _create


@pytest.fixture
def create_multiple_ec2_instances():
    """
    Factory pour créer plusieurs instances EC2.

    Usage:
        instance_ids = create_multiple_ec2_instances(region='eu-west-3', count=5)
    """
    def _create(region='eu-west-3', count=3, **kwargs):
        ec2 = boto3.client('ec2', region_name=region)
        
        # Créer VPC et subnet
        vpc_response = ec2.create_vpc(CidrBlock='10.0.0.0/16')
        vpc_id = vpc_response['Vpc']['VpcId']
        
        subnet_response = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock='10.0.1.0/24',
            AvailabilityZone=f'{region}a'
        )
        subnet_id = subnet_response['Subnet']['SubnetId']
        
        # Créer les instances
        response = ec2.run_instances(
            ImageId=kwargs.get('ami_id', 'ami-12345678'),
            InstanceType=kwargs.get('instance_type', 't2.micro'),
            MinCount=count,
            MaxCount=count,
            SubnetId=subnet_id
        )
        
        instance_ids = [inst['InstanceId'] for inst in response['Instances']]
        return instance_ids
    
    return _create


@pytest.fixture
def create_cloudwatch_metrics():
    """
    Factory pour créer des métriques CloudWatch de test.

    Usage:
        create_cloudwatch_metrics(instance_id, region, 'CPUUtilization', 45.5)
    """
    def _create(instance_id, region, metric_name, value, namespace='AWS/EC2'):
        cw = boto3.client('cloudwatch', region_name=region)
        
        # Déterminer l'unité selon la métrique
        if 'Utilization' in metric_name or 'Percent' in metric_name:
            unit = 'Percent'
        elif 'Network' in metric_name or 'Bytes' in metric_name:
            unit = 'Bytes'
        else:
            unit = 'None'
        
        cw.put_metric_data(
            Namespace=namespace,
            MetricData=[{
                'MetricName': metric_name,
                'Dimensions': [{'Name': 'InstanceId', 'Value': instance_id}],
                'Value': value,
                'Timestamp': datetime.now(),
                'Unit': unit
            }]
        )
    
    return _create

