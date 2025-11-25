"""
Fixtures spécifiques pour les tests S3
"""
import pytest
import boto3
from moto import mock_aws
from datetime import datetime, timedelta


@pytest.fixture
def s3_client():
    """Crée un client S3 mocké"""
    with mock_aws():
        yield boto3.client('s3', region_name='us-east-1')


@pytest.fixture
def cloudwatch_client():
    """Crée un client CloudWatch mocké"""
    with mock_aws():
        yield boto3.client('cloudwatch', region_name='us-east-1')


@pytest.fixture
def create_s3_bucket():
    """
    Factory pour créer des buckets S3 de test.
    
    Usage:
        bucket_name = create_s3_bucket(name='test-bucket', region='eu-west-3')
    """
    def _create(
        name=None,
        region='us-east-1',
        encryption=False,
        versioning=False,
        public_access_block=False,
        public_read=False,
        bucket_policy=False,
        lifecycle=False,
        cors=False,
        website=False,
        logging=False,
        replication=False
    ):
        s3 = boto3.client('s3', region_name='us-east-1')
        
        # Générer un nom unique si non fourni
        if name is None:
            import uuid
            name = f'test-bucket-{uuid.uuid4().hex[:8]}'
        
        # Créer le bucket
        if region == 'us-east-1':
            s3.create_bucket(Bucket=name)
        else:
            s3.create_bucket(
                Bucket=name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        # Configurer encryption
        if encryption:
            s3.put_bucket_encryption(
                Bucket=name,
                ServerSideEncryptionConfiguration={
                    'Rules': [{
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    }]
                }
            )
        
        # Configurer versioning
        if versioning:
            s3.put_bucket_versioning(
                Bucket=name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
        
        # Configurer public access block
        if public_access_block:
            s3.put_public_access_block(
                Bucket=name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
        
        # Configurer public read ACL
        if public_read:
            s3.put_bucket_acl(Bucket=name, ACL='public-read')
        
        # Configurer bucket policy
        if bucket_policy:
            policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{name}/*"
                }]
            }
            import json
            s3.put_bucket_policy(Bucket=name, Policy=json.dumps(policy))
        
        # Configurer lifecycle
        if lifecycle:
            s3.put_bucket_lifecycle_configuration(
                Bucket=name,
                LifecycleConfiguration={
                    'Rules': [{
                        'ID': 'test-rule',
                        'Status': 'Enabled',
                        'Prefix': 'logs/',
                        'Expiration': {'Days': 30}
                    }]
                }
            )
        
        # Configurer CORS
        if cors:
            s3.put_bucket_cors(
                Bucket=name,
                CORSConfiguration={
                    'CORSRules': [{
                        'AllowedMethods': ['GET', 'POST'],
                        'AllowedOrigins': ['*'],
                        'AllowedHeaders': ['*']
                    }]
                }
            )
        
        # Configurer website
        if website:
            s3.put_bucket_website(
                Bucket=name,
                WebsiteConfiguration={
                    'IndexDocument': {'Suffix': 'index.html'},
                    'ErrorDocument': {'Key': 'error.html'}
                }
            )
        
        # Configurer logging
        if logging:
            s3.put_bucket_logging(
                Bucket=name,
                BucketLoggingStatus={
                    'LoggingEnabled': {
                        'TargetBucket': name,
                        'TargetPrefix': 'logs/'
                    }
                }
            )
        
        return name

    return _create


@pytest.fixture
def create_multiple_s3_buckets():
    """
    Factory pour créer plusieurs buckets S3.

    Usage:
        bucket_names = create_multiple_s3_buckets(count=5, region='eu-west-3')
    """
    def _create(count=3, region='us-east-1', **kwargs):
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_names = []

        for i in range(count):
            import uuid
            bucket_name = f'test-bucket-{uuid.uuid4().hex[:8]}'

            # Créer le bucket
            if region == 'us-east-1':
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )

            bucket_names.append(bucket_name)

        return bucket_names

    return _create


@pytest.fixture
def create_s3_cloudwatch_metrics():
    """
    Factory pour créer des métriques CloudWatch S3 de test.

    Usage:
        create_s3_cloudwatch_metrics(bucket_name, region, 'AllRequests', 1000)
    """
    def _create(bucket_name, region, metric_name, value):
        cw = boto3.client('cloudwatch', region_name=region)

        # Déterminer l'unité selon la métrique
        if 'Latency' in metric_name:
            unit = 'Milliseconds'
        elif 'Bytes' in metric_name:
            unit = 'Bytes'
        elif 'Requests' in metric_name or 'Errors' in metric_name:
            unit = 'Count'
        else:
            unit = 'None'

        cw.put_metric_data(
            Namespace='AWS/S3',
            MetricData=[{
                'MetricName': metric_name,
                'Dimensions': [
                    {'Name': 'BucketName', 'Value': bucket_name},
                    {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                ],
                'Value': value,
                'Timestamp': datetime.now(),
                'Unit': unit
            }]
        )

    return _create

