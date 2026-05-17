from api.services.ScanAbstraction.create_cloud_scanne import CloudScanner
from typing import List, Optional
from loguru import logger
import boto3
import asyncio
from datetime import datetime, timedelta

class S3Scanner(CloudScanner):
    def __init__(self,session:boto3.session,client_id:str,regions:List[str] = None):
        super().__init__(session,client_id)
        self.requested_regions = regions

    async def scan(self) -> List[dict]:
        """Scan des buckets S3"""
        logger.info("Start scan S3")
        
        try: 
            s3_client = self.get_client('s3', 'us-east-1')
            response = s3_client.list_buckets()
            buckets = response.get('Buckets', [])
            
            logger.info(f"{len(buckets)} buckets trouvés")
            
            # Déterminer les régions à scanner
            if self.requested_regions:
                regions_to_scan = self.requested_regions
                logger.info(f" Régions demandées: {regions_to_scan}")
            else:
                regions_to_scan = self._get_authorized_regions()
                logger.info(f" Régions autorisées: {regions_to_scan}")
            
            # Filtrer les buckets par régions autorisées
            filtered_buckets = []
            for bucket in buckets:
                bucket_region = self._get_bucket_region(bucket, s3_client)
                if bucket_region in regions_to_scan:
                    filtered_buckets.append(bucket)
                    logger.info(f"Bucket {bucket['Name']} en région {bucket_region} - autorisé")
                else:
                    logger.warning(f" Bucket {bucket['Name']} en région {bucket_region} - non autorisé")
            
            logger.info(f"{len(filtered_buckets)} buckets à scanner (sur {len(buckets)} total)")
            
            #  PARALLÉLISATION DES BUCKETS
            logger.info(f" Lancement scan parallèle de {len(filtered_buckets)} buckets")
            tasks = [self._scan_single_bucket(bucket, s3_client) for bucket in filtered_buckets]
            bucket_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Fusionner tous les buckets
            buckets_data = []
            for i, result in enumerate(bucket_results):
                if isinstance(result, dict):
                    buckets_data.append(result)
                    logger.success(f"✅ Bucket {filtered_buckets[i]['Name']} scanné")
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ Bucket {filtered_buckets[i]['Name']} échoué: {result}")

            logger.success(f"✅ Scan S3 terminé : {len(buckets_data)} buckets scannés")
            return buckets_data
        
        except Exception as e:
            logger.error(f"Error scan s3: {e}")
            return []

    def _get_bucket_region(self, bucket: dict, s3_client) -> str:
        """Récupère la région d'un bucket"""
        try:
            response = s3_client.get_bucket_location(Bucket=bucket['Name'])
            region = response.get('LocationConstraint') or 'us-east-1'
            return region
        except Exception as e:
            logger.warning(f"Impossible de récupérer la région pour {bucket['Name']}: {e}")
            return 'us-east-1'
    
    async def _scan_single_bucket(self, bucket: dict, s3_client) -> Optional[dict]:
        """
        Scan un bucket S3 et retourne toutes ses données dans un seul dictionnaire
        """
        try:
            bucket_name = bucket['Name']
            bucket_region = self._get_bucket_region(bucket, s3_client)
            logger.info(f"📦 Scan bucket: {bucket_name} (région: {bucket_region})")

            # Récupérer toutes les métadonnées
            bucket_data = self._extract_bucket_data(bucket, s3_client, bucket_region)

            # Récupérer les métriques de performance CloudWatch
            performance_data = self._extract_performance_metrics(bucket, s3_client, bucket_region)

            # Fusionner les données
            bucket_data['performance'] = performance_data

            return bucket_data

        except Exception as e:
            logger.error(f"❌ Erreur scan bucket {bucket.get('Name', 'unknown')}: {e}")
            return None
    
    def _extract_bucket_data(self, bucket: dict, s3_client, bucket_region: str) -> dict:
        """
        Extrait TOUTES les métadonnées d'un bucket S3 en un seul dictionnaire
        """
        bucket_name = bucket['Name']
        bucket_arn = f"arn:aws:s3:::{bucket_name}"

        # Helper pour récupérer les configs S3 de manière sécurisée
        def safe_get_config(func, default=None, error_code=None, **kwargs):
            try:
                return func(**kwargs)
            except s3_client.exceptions.ClientError as e:
                if error_code and e.response['Error']['Code'] == error_code:
                    return default
                logger.debug(f"Config non disponible pour {bucket_name}: {e}")
                return default
            except Exception as e:
                logger.debug(f"Erreur config {bucket_name}: {e}")
                return default

        # Récupérer encryption
        encryption_response = safe_get_config(
            s3_client.get_bucket_encryption,
            Bucket=bucket_name,
            error_code='ServerSideEncryptionConfigurationNotFoundError'
        )
        encryption_enabled = bool(encryption_response and encryption_response.get('ServerSideEncryptionConfiguration'))

        # Récupérer versioning
        versioning_response = safe_get_config(s3_client.get_bucket_versioning, Bucket=bucket_name)
        versioning_enabled = versioning_response and versioning_response.get('Status') == 'Enabled'

        # Récupérer public access block
        public_access_response = safe_get_config(
            s3_client.get_public_access_block,
            Bucket=bucket_name,
            error_code='NoSuchPublicAccessBlockConfiguration'
        )
        public_access_blocked = bool(
            public_access_response and
            public_access_response.get('PublicAccessBlockConfiguration', {}).get('BlockPublicAcls', False)
        )

        # Récupérer ACL
        acl_response = safe_get_config(s3_client.get_bucket_acl, Bucket=bucket_name)
        public_read = False
        if acl_response:
            grants = acl_response.get('Grants', [])
            public_read = any(
                grant.get('Grantee', {}).get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers'
                for grant in grants
            )

        # Récupérer bucket policy
        policy_response = safe_get_config(
            s3_client.get_bucket_policy,
            Bucket=bucket_name,
            error_code='NoSuchBucketPolicy'
        )
        bucket_policy_enabled = bool(policy_response)

        # Récupérer lifecycle
        lifecycle_response = safe_get_config(
            s3_client.get_bucket_lifecycle_configuration,
            Bucket=bucket_name,
            error_code='NoSuchLifecycleConfiguration'
        )
        lifecycle_enabled = bool(lifecycle_response and lifecycle_response.get('Rules'))

        # Récupérer CORS
        cors_response = safe_get_config(
            s3_client.get_bucket_cors,
            Bucket=bucket_name,
            error_code='NoSuchCORSConfiguration'
        )
        cors_enabled = bool(cors_response and cors_response.get('CORSRules'))

        # Récupérer website
        website_response = safe_get_config(
            s3_client.get_bucket_website,
            Bucket=bucket_name,
            error_code='NoSuchWebsiteConfiguration'
        )
        website_enabled = bool(website_response and website_response.get('IndexDocument'))

        # Récupérer logging
        logging_response = safe_get_config(s3_client.get_bucket_logging, Bucket=bucket_name)
        logging_enabled = bool(logging_response and 'LoggingEnabled' in logging_response)

        # Récupérer notifications
        notifications_response = safe_get_config(
            s3_client.get_bucket_notification_configuration,
            Bucket=bucket_name
        )
        notifications_enabled = False
        if notifications_response:
            notifications_enabled = any([
                notifications_response.get('TopicConfigurations', []),
                notifications_response.get('QueueConfigurations', []),
                notifications_response.get('LambdaFunctionConfigurations', []),
                notifications_response.get('EventBridgeConfiguration')
            ])

        # Récupérer replication
        replication_response = safe_get_config(
            s3_client.get_bucket_replication,
            Bucket=bucket_name,
            error_code='ReplicationConfigurationNotFoundError'
        )
        replication_enabled = bool(
            replication_response and
            replication_response.get('ReplicationConfiguration', {}).get('Rules')
        )

        return {
            "client_id": self.client_id,
            "resource_id": bucket_arn,
            "bucket_name": bucket_name,
            "creation_date": bucket['CreationDate'],  # Garder en datetime pour la BDD
            "region": bucket_region,
            "encryption_enabled": encryption_enabled,
            "versioning_enabled": versioning_enabled,
            "public_access_blocked": public_access_blocked,
            "public_read_enabled": public_read,
            "bucket_policy_enabled": bucket_policy_enabled,
            "lifecycle_enabled": lifecycle_enabled,
            "cors_enabled": cors_enabled,
            "website_enabled": website_enabled,
            "logging_enabled": logging_enabled,
            "notifications_enabled": notifications_enabled,
            "replication_enabled": replication_enabled,
            "timestamp": datetime.now().isoformat()
        }

    def _extract_performance_metrics(self, bucket: dict, s3_client, bucket_region: str) -> dict:
        """
        Extrait TOUTES les métriques de performance CloudWatch en un seul dictionnaire
        """
        bucket_name = bucket['Name']

        return {
            # Métriques de requêtes
            "all_requests": self._get_s3_cloudwatch_metric(bucket_name, bucket_region, 'AllRequests', 'Sum'),
            "get_requests": self._get_s3_cloudwatch_metric(bucket_name, bucket_region, 'GetRequests', 'Sum'),
            "put_requests": self._get_s3_cloudwatch_metric(bucket_name, bucket_region, 'PutRequests', 'Sum'),
            "delete_requests": self._get_s3_cloudwatch_metric(bucket_name, bucket_region, 'DeleteRequests', 'Sum'),

            # Métriques d'erreurs
            "4xx_errors": self._get_s3_cloudwatch_metric(bucket_name, bucket_region, '4xxErrors', 'Sum'),
            "5xx_errors": self._get_s3_cloudwatch_metric(bucket_name, bucket_region, '5xxErrors', 'Sum'),

            # Métriques de latence
            "first_byte_latency_avg": self._get_s3_cloudwatch_metric(bucket_name, bucket_region, 'FirstByteLatency', 'Average'),
            "total_request_latency_avg": self._get_s3_cloudwatch_metric(bucket_name, bucket_region, 'TotalRequestLatency', 'Average'),

            # Métriques de transfert
            "bytes_downloaded": self._get_s3_cloudwatch_metric(bucket_name, bucket_region, 'BytesDownloaded', 'Sum'),
            "bytes_uploaded": self._get_s3_cloudwatch_metric(bucket_name, bucket_region, 'BytesUploaded', 'Sum')
        }

    def _get_s3_cloudwatch_metric(
        self,
        bucket_name: str,
        bucket_region: str,
        metric_name: str,
        statistic: str
    ) -> Optional[float]:
        """
        Récupère une métrique CloudWatch S3 générique
        Retourne None si la métrique n'est pas disponible
        """
        try:
            cloudwatch = self.get_client('cloudwatch', bucket_region)

            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'BucketName', 'Value': bucket_name},
                    {'Name': 'StorageType', 'Value': 'AllStorageTypes'}
                ],
                StartTime=datetime.now() - timedelta(days=1),
                EndTime=datetime.now(),
                Period=3600,  # 1 heure
                Statistics=[statistic]
            )

            if response['Datapoints']:
                if statistic == 'Average':
                    value = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                    return round(value, 2)
                elif statistic == 'Sum':
                    value = sum(dp['Sum'] for dp in response['Datapoints'])
                    return int(value)
                else:
                    return response['Datapoints'][0].get(statistic, 0)
            else:
                logger.debug(f"⚠️ Pas de données CloudWatch pour {metric_name} sur bucket {bucket_name}")
                return None

        except Exception as e:
            logger.warning(f"⚠️ Erreur CloudWatch {metric_name} pour bucket {bucket_name}: {e}")
            return None