from api.services.ScanAbstraction.create_cloud_scanne import CloudScanner
from typing import List, Optional
from loguru import logger
import boto3
import asyncio
from datetime import datetime, timedelta

class EC2Scanner(CloudScanner):
    def __init__(self, session: boto3.Session, client_id: str, regions: List[str] = None):
        super().__init__(session, client_id)
        self.requested_regions = regions

    async def scan(self) -> List[dict]:
        """
        Scan des instances EC2 dans les régions demandées ou autorisées
        Retourne une liste de dictionnaires avec toutes les métriques par instance
        """
        logger.info("🔍 Démarrage scan EC2...")

        try:
            # Utiliser les régions demandées OU toutes les autorisées
            if self.requested_regions:
                regions_to_scan = self.requested_regions
                logger.info(f"🎯 Régions demandées: {regions_to_scan}")
            else:
                regions_to_scan = self._get_authorized_regions()
                logger.info(f"🌍 Régions autorisées: {regions_to_scan}")

            # Scanner toutes les régions en parallèle
            logger.info(f"🚀 Lancement scan parallèle de {len(regions_to_scan)} régions")
            tasks = [self._scan_region(region) for region in regions_to_scan]
            region_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Fusionner toutes les instances
            instances = []
            for i, result in enumerate(region_results):
                if isinstance(result, list):
                    instances.extend(result)
                    logger.info(f"✅ Région {regions_to_scan[i]}: {len(result)} instances")
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ Région {regions_to_scan[i]} échouée: {result}")

            logger.success(f"✅ EC2 scan terminé: {len(instances)} instances scannées")
            return instances

        except Exception as e:
            logger.error(f"❌ Erreur scan EC2: {str(e)}")
            raise

    async def _scan_region(self, region: str) -> List[dict]:
        """Scan une région spécifique avec gestion d'erreur robuste"""
        logger.info(f"🔍 Scan région: {region}")
        instances = []

        try:
            ec2_client = self.get_client('ec2', region)
            response = ec2_client.describe_instances()

            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    # Traiter chaque instance de manière isolée
                    instance_data = self._scan_single_instance(instance, region)
                    if instance_data:
                        instances.append(instance_data)

            logger.info(f"----> Région {region}: {len(instances)} instances scannées")
            return instances

        except Exception as e:
            logger.warning(f"⚠️ Région {region} inaccessible: {e}")
            # Supprimer le client défaillant du pool
            self.invalidate_client('ec2', region)
            return []

    def _scan_single_instance(self, instance: dict, region: str) -> Optional[dict]:
        """
        Scan une instance et retourne toutes ses données dans un seul dictionnaire
        """
        try:
            instance_id = instance['InstanceId']
            logger.debug(f"📋 Scan instance {instance_id}")

            # Récupérer toutes les métadonnées
            instance_data = self._extract_instance_data(instance, region)

            # Récupérer les métriques de performance CloudWatch
            performance_data = self._extract_performance_metrics(instance, region)

            # Fusionner les données
            instance_data['performance'] = performance_data

            return instance_data

        except Exception as e:
            logger.error(f"❌ Erreur scan instance {instance.get('InstanceId', 'unknown')}: {e}")
            return None

    def _extract_instance_data(self, instance: dict, region: str) -> dict:
        """
        Extrait TOUTES les métadonnées d'une instance EC2 en un seul dictionnaire
        """
        instance_id = instance['InstanceId']
        account_id = instance.get('OwnerId', 'unknown')

        # Construire l'ARN
        instance_arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"

        # Extraire les volumes EBS
        ebs_volumes = []
        if 'BlockDeviceMappings' in instance:
            for device in instance['BlockDeviceMappings']:
                if 'Ebs' in device:
                    ebs_volumes.append({
                        "device_name": device['DeviceName'],
                        "volume_id": device['Ebs']['VolumeId'],
                        "delete_on_termination": device['Ebs'].get('DeleteOnTermination', False)
                    })

        # Extraire les tags
        tags = {}
        if 'Tags' in instance and instance['Tags']:
            tags = {tag['Key']: tag['Value'] for tag in instance['Tags']}

        return {
            "client_id": self.client_id,
            "resource_id": instance_arn,
            "instance_id": instance_id,
            "instance_type": instance['InstanceType'],
            "state": instance['State']['Name'],
            "ami_id": instance['ImageId'],
            "availability_zone": instance['Placement']['AvailabilityZone'],
            "tenancy": instance['Placement']['Tenancy'],
            "architecture": instance['Architecture'],
            "virtualization_type": instance['VirtualizationType'],
            "launch_time": instance['LaunchTime'],  # Garder en datetime pour la BDD
            "vpc_id": instance.get('VpcId'),
            "subnet_id": instance.get('SubnetId'),
            "private_ip": instance.get('PrivateIpAddress'),
            "public_ip": instance.get('PublicIpAddress'),
            "iam_profile": instance.get('IamInstanceProfile', {}).get('Arn'),
            "root_device_name": instance.get('RootDeviceName'),
            "ebs_volumes": ebs_volumes,
            "tags": tags,
            "region": region,
            "timestamp": datetime.now().isoformat()
        }

    def _extract_performance_metrics(self, instance: dict, region: str) -> dict:
        """
        Extrait TOUTES les métriques de performance CloudWatch en un seul dictionnaire
        """
        instance_id = instance['InstanceId']

        return {
            "cpu_utilization_avg": self._get_cloudwatch_metric(
                instance_id, region, 'CPUUtilization', 'AWS/EC2', 'Average'
            ),
            "memory_utilization_avg": self._get_cloudwatch_metric(
                instance_id, region, 'mem_used_percent', 'CWAgent', 'Average'
            ),
            "network_in_bytes": self._get_cloudwatch_metric(
                instance_id, region, 'NetworkIn', 'AWS/EC2', 'Sum'
            ),
            "network_out_bytes": self._get_cloudwatch_metric(
                instance_id, region, 'NetworkOut', 'AWS/EC2', 'Sum'
            )
        }

    def _get_cloudwatch_metric(
        self,
        instance_id: str,
        region: str,
        metric_name: str,
        namespace: str,
        statistic: str
    ) -> Optional[float]:
        """
        Récupère une métrique CloudWatch générique
        Retourne None si la métrique n'est pas disponible
        """
        try:
            cloudwatch = self.get_client('cloudwatch', region)

            response = cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.now() - timedelta(days=1),
                EndTime=datetime.now(),
                Period=3600,  # 1 heure
                Statistics=[statistic]
            )

            if response['Datapoints']:
                if statistic == 'Average':
                    value = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                elif statistic == 'Sum':
                    value = sum(dp['Sum'] for dp in response['Datapoints'])
                else:
                    value = response['Datapoints'][0].get(statistic, 0)

                return round(value, 2) if statistic == 'Average' else int(value)
            else:
                logger.debug(f"⚠️ Pas de données CloudWatch pour {metric_name} sur {instance_id}")
                return None

        except Exception as e:
            logger.warning(f"⚠️ Erreur CloudWatch {metric_name} pour {instance_id}: {e}")
            return None

    def _get_authorized_regions(self) -> List[str]:
        """Récupère les régions autorisées via l'API AWS"""
        try:
            # Utiliser le pool pour le client initial
            ec2_client = self.get_client('ec2', 'us-east-1')
            response = ec2_client.describe_regions()

            authorized = []
            for region in response['Regions']:
                region_name = region['RegionName']
                try:
                    # Tester l'accès à chaque région avec le pool
                    test_client = self.get_client('ec2', region_name)
                    test_client.describe_instances()
                    authorized.append(region_name)
                    logger.info(f"✅ Région {region_name} accessible")
                except Exception as e:
                    logger.warning(f"⚠️ Région {region_name} inaccessible: {e}")
                    # Supprimer le client défaillant
                    self.invalidate_client('ec2', region_name)
                    continue

            return authorized if authorized else ['us-east-1']

        except Exception as e:
            logger.warning(f"⚠️ Impossible de récupérer les régions: {e}")
            return ['us-east-1']
