from typing import List, Dict, Any
from loguru import logger
import boto3
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from api.database import ScanRun, RDSInstance, RDSPerformance


class RDSScanner:
    """
    Scanner pour les instances RDS (Relational Database Service).
    
    Scanne toutes les instances RDS dans les régions spécifiées et stocke
    les données directement en base de données.
    """
    
    def __init__(self, session: boto3.Session, client_id: str, regions: List[str] = None):
        """
        Initialise le scanner RDS.
        
        Args:
            session: Session boto3 authentifiée
            client_id: Identifiant du client
            regions: Liste des régions à scanner (optionnel)
        """
        self.session = session
        self.client_id = client_id
        self.requested_regions = regions
    
    def _get_available_regions(self) -> List[str]:
        """Récupère la liste des régions AWS disponibles pour RDS"""
        try:
            ec2_client = self.session.client('ec2', region_name='us-east-1')
            response = ec2_client.describe_regions()
            regions = [region['RegionName'] for region in response['Regions']]
            logger.info(f"📍 {len(regions)} régions disponibles pour RDS")
            return regions
        except Exception as e:
            logger.error(f"❌ Erreur récupération des régions: {e}")
            return ['eu-west-3']  # Région par défaut
    
    def scan(self, db: Session, user_id: int = None) -> Dict[str, Any]:
        """
        Lance le scan des instances RDS.
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur qui lance le scan
            
        Returns:
            Dictionnaire avec les résultats du scan
        """
        logger.info("🗄️ Démarrage du scan RDS")
        
        # Créer un ScanRun
        scan_run = ScanRun(
            client_id=self.client_id,
            service_type='rds',
            scan_timestamp=datetime.now(),
            total_resources=0,
            status='success',
            user_id=user_id
        )
        db.add(scan_run)
        db.commit()
        
        # Déterminer les régions à scanner
        if self.requested_regions:
            regions_to_scan = self.requested_regions
            logger.info(f"📍 Régions demandées: {regions_to_scan}")
        else:
            regions_to_scan = self._get_available_regions()
            logger.info(f"📍 Régions disponibles: {regions_to_scan}")
        
        total_instances = 0
        instances_by_region = {}
        
        # Scanner chaque région
        for region in regions_to_scan:
            try:
                logger.info(f"🔍 Scan de la région {region}...")
                instances_count = self._scan_region(region, db, scan_run)
                instances_by_region[region] = instances_count
                total_instances += instances_count
                logger.success(f"✅ {instances_count} instances RDS trouvées dans {region}")
            except Exception as e:
                logger.error(f"❌ Erreur lors du scan de {region}: {e}")
                continue
        
        # Mettre à jour le scan_run
        scan_run.total_resources = total_instances
        scan_run.status = 'success' if total_instances > 0 else 'partial'
        db.commit()
        
        logger.success(f"✅ Scan RDS terminé: {total_instances} instances trouvées")
        
        return {
            "total_instances": total_instances,
            "instances_by_region": instances_by_region,
            "scan_run_id": scan_run.id
        }
    
    def _scan_region(self, region: str, db: Session, scan_run: ScanRun) -> int:
        """
        Scanne une région spécifique.

        Returns:
            Nombre d'instances RDS trouvées
        """
        logger.info(f"🌍 Connexion à la région {region}...")
        rds_client = self.session.client('rds', region_name=region)

        # Récupérer toutes les instances RDS
        try:
            logger.info(f"📡 Appel describe_db_instances() pour {region}...")
            response = rds_client.describe_db_instances()
            instances = response.get('DBInstances', [])

            logger.info(f"📊 {len(instances)} instances RDS trouvées dans {region}")

            if not instances:
                logger.warning(f"⚠️  Aucune instance RDS dans {region}")
                return 0

            # Scanner chaque instance
            for idx, instance in enumerate(instances, 1):
                db_id = instance.get('DBInstanceIdentifier', 'unknown')
                logger.info(f"📦 [{idx}/{len(instances)}] Traitement de {db_id}...")
                self._scan_single_instance(instance, region, rds_client, db, scan_run)

            return len(instances)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des instances RDS dans {region}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0

    def _scan_single_instance(self, instance: dict, region: str, rds_client, db: Session, scan_run: ScanRun):
        """Scanne une instance RDS individuelle et stocke les données"""
        db_identifier = instance['DBInstanceIdentifier']
        logger.info(f"🔍 Scan de l'instance RDS: {db_identifier}")

        try:
            # Récupérer les informations de l'instance
            logger.debug(f"  📋 Extraction des métadonnées...")
            instance_data = self._extract_instance_data(instance, region)
            logger.debug(f"  ✅ Métadonnées extraites: {len(instance_data)} champs")

            # Créer l'instance RDS
            logger.debug(f"  💾 Création de l'enregistrement RDSInstance...")
            rds_instance = RDSInstance(
                scan_run_id=scan_run.id,
                client_id=self.client_id,
                **instance_data
            )
            db.add(rds_instance)
            db.flush()
            logger.debug(f"  ✅ RDSInstance créée avec ID: {rds_instance.id}")

            # Créer les métriques de performance
            logger.debug(f"  📊 Récupération des métriques CloudWatch...")
            rds_performance = self._extract_performance_metrics(db_identifier, region, rds_client)
            rds_performance.rds_instance_id = rds_instance.id
            db.add(rds_performance)
            logger.debug(f"  ✅ Métriques CloudWatch ajoutées")

            db.commit()
            logger.success(f"✅ Instance RDS {db_identifier} sauvegardée avec succès")

        except Exception as e:
            logger.error(f"❌ Erreur scan instance RDS {db_identifier}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            db.rollback()
            raise  # Re-raise pour voir l'erreur dans les logs

    def _extract_instance_data(self, instance: dict, region: str) -> dict:
        """
        Extrait toutes les métadonnées d'une instance RDS.

        Returns:
            Dictionnaire avec toutes les données de l'instance
        """
        db_identifier = instance['DBInstanceIdentifier']

        # Construire l'ARN
        instance_arn = instance.get('DBInstanceArn', f"arn:aws:rds:{region}::db:{db_identifier}")

        # Extraire les tags
        tags = {}
        if 'TagList' in instance:
            tags = {tag['Key']: tag['Value'] for tag in instance['TagList']}

        # Extraire les security groups
        security_groups = []
        if 'VpcSecurityGroups' in instance:
            security_groups = [
                {
                    "id": sg['VpcSecurityGroupId'],
                    "status": sg['Status']
                }
                for sg in instance['VpcSecurityGroups']
            ]

        # Extraire les parameter groups
        parameter_groups = []
        if 'DBParameterGroups' in instance:
            parameter_groups = [
                {
                    "name": pg['DBParameterGroupName'],
                    "status": pg['ParameterApplyStatus']
                }
                for pg in instance['DBParameterGroups']
            ]

        # Extraire les option groups
        option_groups = []
        if 'OptionGroupMemberships' in instance:
            option_groups = [
                {
                    "name": og['OptionGroupName'],
                    "status": og['Status']
                }
                for og in instance['OptionGroupMemberships']
            ]

        # Extraire l'endpoint
        endpoint_address = None
        endpoint_port = None
        if 'Endpoint' in instance:
            endpoint_address = instance['Endpoint'].get('Address')
            endpoint_port = instance['Endpoint'].get('Port')

        return {
            "resource_id": instance_arn,
            "db_instance_identifier": db_identifier,
            "db_instance_class": instance.get('DBInstanceClass'),
            "engine": instance.get('Engine'),
            "engine_version": instance.get('EngineVersion'),
            "db_instance_status": instance.get('DBInstanceStatus'),
            "allocated_storage": instance.get('AllocatedStorage'),
            "storage_type": instance.get('StorageType'),
            "storage_encrypted": instance.get('StorageEncrypted', False),
            "iops": instance.get('Iops'),
            "vpc_id": instance.get('DBSubnetGroup', {}).get('VpcId') if instance.get('DBSubnetGroup') else None,
            "db_subnet_group_name": instance.get('DBSubnetGroup', {}).get('DBSubnetGroupName') if instance.get('DBSubnetGroup') else None,
            "availability_zone": instance.get('AvailabilityZone'),
            "multi_az": instance.get('MultiAZ', False),
            "publicly_accessible": instance.get('PubliclyAccessible', False),
            "endpoint_address": endpoint_address,
            "endpoint_port": endpoint_port,
            "master_username": instance.get('MasterUsername'),
            "iam_database_authentication_enabled": instance.get('IAMDatabaseAuthenticationEnabled', False),
            "deletion_protection": instance.get('DeletionProtection', False),
            "backup_retention_period": instance.get('BackupRetentionPeriod'),
            "preferred_backup_window": instance.get('PreferredBackupWindow'),
            "preferred_maintenance_window": instance.get('PreferredMaintenanceWindow'),
            "latest_restorable_time": instance.get('LatestRestorableTime'),
            "auto_minor_version_upgrade": instance.get('AutoMinorVersionUpgrade', False),
            "enhanced_monitoring_resource_arn": instance.get('EnhancedMonitoringResourceArn'),
            "monitoring_interval": instance.get('MonitoringInterval'),
            "performance_insights_enabled": instance.get('PerformanceInsightsEnabled', False),
            "region": region,
            "tags": tags,
            "security_groups": security_groups,
            "parameter_groups": parameter_groups,
            "option_groups": option_groups,
            "instance_create_time": instance.get('InstanceCreateTime'),
            "scan_timestamp": datetime.now()
        }

    def _extract_performance_metrics(self, db_identifier: str, region: str, rds_client) -> RDSPerformance:
        """
        Extrait les métriques de performance CloudWatch pour une instance RDS.

        Returns:
            Objet RDSPerformance avec les métriques
        """
        rds_performance = RDSPerformance()

        try:
            cloudwatch_client = self.session.client('cloudwatch', region_name=region)

            # Période de temps pour les métriques (dernières 24 heures)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)

            # Métriques CPU
            rds_performance.cpu_utilization_avg = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'CPUUtilization', start_time, end_time, 'Average'
            )

            # Métriques mémoire
            rds_performance.freeable_memory_bytes = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'FreeableMemory', start_time, end_time, 'Average'
            )

            # Métriques stockage
            rds_performance.free_storage_space_bytes = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'FreeStorageSpace', start_time, end_time, 'Average'
            )

            # Métriques connexions
            rds_performance.database_connections = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'DatabaseConnections', start_time, end_time, 'Average'
            )

            # Métriques IOPS
            rds_performance.read_iops_avg = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'ReadIOPS', start_time, end_time, 'Average'
            )
            rds_performance.write_iops_avg = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'WriteIOPS', start_time, end_time, 'Average'
            )

            # Métriques latence
            rds_performance.read_latency_avg = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'ReadLatency', start_time, end_time, 'Average'
            )
            rds_performance.write_latency_avg = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'WriteLatency', start_time, end_time, 'Average'
            )

            # Métriques throughput
            rds_performance.read_throughput_bytes = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'ReadThroughput', start_time, end_time, 'Sum'
            )
            rds_performance.write_throughput_bytes = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'WriteThroughput', start_time, end_time, 'Sum'
            )

            # Métriques réseau
            rds_performance.network_receive_throughput_bytes = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'NetworkReceiveThroughput', start_time, end_time, 'Sum'
            )
            rds_performance.network_transmit_throughput_bytes = self._get_cloudwatch_metric(
                cloudwatch_client, db_identifier, 'NetworkTransmitThroughput', start_time, end_time, 'Sum'
            )

            logger.debug(f"📊 Métriques récupérées pour {db_identifier}")

        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération métriques pour {db_identifier}: {e}")

        return rds_performance

    def _get_cloudwatch_metric(self, cloudwatch_client, db_identifier: str, metric_name: str,
                                start_time: datetime, end_time: datetime, stat: str) -> float:
        """
        Récupère une métrique CloudWatch spécifique.

        Returns:
            Valeur de la métrique ou None si non disponible
        """
        try:
            response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_identifier
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 heure
                Statistics=[stat]
            )

            datapoints = response.get('Datapoints', [])
            if datapoints:
                # Retourner la dernière valeur
                latest = max(datapoints, key=lambda x: x['Timestamp'])
                return latest.get(stat)

            return None

        except Exception as e:
            logger.debug(f"⚠️ Métrique {metric_name} non disponible pour {db_identifier}: {e}")
            return None



