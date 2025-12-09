"""
Service de stockage des résultats de scan dans MariaDB.

Ce service gère la sauvegarde des résultats de scan EC2 et S3 dans la base de données.

Workflow :
1. Créer un ScanRun (enregistrement de l'exécution du scan)
2. Pour chaque ressource (instance EC2 ou bucket S3) :
   - Créer l'entrée dans ec2_instances ou s3_buckets
   - Créer l'entrée de performance associée
3. Commit de la transaction

En cas d'erreur, toute la transaction est annulée (rollback).
"""

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from loguru import logger

from api.database.models import (
    ScanRun, EC2Instance, EC2Performance, S3Bucket, S3Performance,
    VPCInstance, VPCPerformance, RDSInstance, RDSPerformance
)
from api.database.connection import SessionLocal


# ========================================
# FONCTION : save_ec2_scan
# ========================================
def save_ec2_scan(client_id: str, instances_data: List[dict], user_id: int = None, session_id: str = None) -> bool:
    """
    Sauvegarde les résultats d'un scan EC2 dans la base de données.

    Args:
        client_id (str): Identifiant du client (ex: "ASM-Enterprise")
        instances_data (List[dict]): Liste des instances EC2 avec leurs métadonnées et performances
        user_id (int): ID de l'utilisateur qui a lancé le scan (pour isolation des comptes)
        session_id (str): ID de session pour grouper les scans multi-services

    Returns:
        bool: True si la sauvegarde a réussi, False sinon

    Exemple d'utilisation :
        ```python
        instances = [
            {
                "instance_id": "i-xxx",
                "instance_type": "t3.micro",
                "state": "running",
                "region": "eu-west-3",
                ...
                "performance": {
                    "cpu_utilization_avg": 45.2,
                    "network_in_bytes": 1024000
                }
            }
        ]
        success = save_ec2_scan("ASM-Enterprise", instances, user_id=1, session_id="scan-abc123")
        ```
    """
    # Créer une session de base de données
    db = SessionLocal()

    try:
        logger.info(f"💾 Sauvegarde de {len(instances_data)} instances EC2 pour {client_id} (session: {session_id})")

        # ========================================
        # ÉTAPE 1 : Créer un ScanRun
        # ========================================
        # Enregistre l'exécution du scan
        scan_run = ScanRun(
            session_id=session_id,
            client_id=client_id,
            service_type='ec2',
            scan_timestamp=datetime.now(),
            total_resources=len(instances_data),
            status='success',
            user_id=user_id
        )
        db.add(scan_run)
        db.flush()  # Envoie à la BDD pour obtenir l'ID, mais ne commit pas encore
        
        logger.debug(f"✅ ScanRun créé avec ID: {scan_run.id}")
        
        # ========================================
        # ÉTAPE 2 : Sauvegarder chaque instance
        # ========================================
        for instance_data in instances_data:
            # Extraire les données de performance (séparées des métadonnées)
            performance_data = instance_data.pop('performance', {})
            
            # Créer l'instance EC2
            ec2_instance = EC2Instance(
                scan_run_id=scan_run.id,
                resource_id=instance_data.get('resource_id'),
                instance_id=instance_data.get('instance_id'),
                client_id=client_id,
                instance_type=instance_data.get('instance_type'),
                state=instance_data.get('state'),
                ami_id=instance_data.get('ami_id'),
                availability_zone=instance_data.get('availability_zone'),
                tenancy=instance_data.get('tenancy'),
                architecture=instance_data.get('architecture'),
                virtualization_type=instance_data.get('virtualization_type'),
                vpc_id=instance_data.get('vpc_id'),
                subnet_id=instance_data.get('subnet_id'),
                private_ip=instance_data.get('private_ip'),
                public_ip=instance_data.get('public_ip'),
                iam_profile=instance_data.get('iam_profile'),
                root_device_name=instance_data.get('root_device_name'),
                launch_time=instance_data.get('launch_time'),
                region=instance_data.get('region'),
                ebs_volumes=instance_data.get('ebs_volumes'),
                tags=instance_data.get('tags'),
                scan_timestamp=instance_data.get('timestamp', datetime.now())
            )
            db.add(ec2_instance)
            db.flush()  # Obtenir l'ID de l'instance
            
            # Créer les performances associées
            ec2_performance = EC2Performance(
                ec2_instance_id=ec2_instance.id,
                cpu_utilization_avg=performance_data.get('cpu_utilization_avg'),
                memory_utilization_avg=performance_data.get('memory_utilization_avg'),
                network_in_bytes=performance_data.get('network_in_bytes'),
                network_out_bytes=performance_data.get('network_out_bytes')
            )
            db.add(ec2_performance)
        
        # ========================================
        # ÉTAPE 3 : Commit de la transaction
        # ========================================
        # Toutes les données sont sauvegardées en une seule transaction
        db.commit()
        logger.success(f"✅ {len(instances_data)} instances EC2 sauvegardées avec succès !")
        return True
        
    except Exception as e:
        # En cas d'erreur, annuler toutes les modifications
        db.rollback()
        logger.error(f"❌ Erreur lors de la sauvegarde EC2 : {e}")
        return False
        
    finally:
        # Toujours fermer la session
        db.close()


# ========================================
# FONCTION : save_s3_scan
# ========================================
def save_s3_scan(client_id: str, buckets_data: List[dict], user_id: int = None, session_id: str = None) -> bool:
    """
    Sauvegarde les résultats d'un scan S3 dans la base de données.

    Args:
        client_id (str): Identifiant du client (ex: "ASM-Enterprise")
        buckets_data (List[dict]): Liste des buckets S3 avec leurs métadonnées et performances
        user_id (int): ID de l'utilisateur qui a lancé le scan (pour isolation des comptes)
        session_id (str): ID de session pour grouper les scans multi-services

    Returns:
        bool: True si la sauvegarde a réussi, False sinon

    Exemple d'utilisation :
        ```python
        buckets = [
            {
                "bucket_name": "my-bucket",
                "region": "eu-west-3",
                "encryption_enabled": True,
                ...
                "performance": {
                    "all_requests": 1000,
                    "bytes_downloaded": 5000000
                }
            }
        ]
        success = save_s3_scan("ASM-Enterprise", buckets, user_id=1, session_id="scan-abc123")
        ```
    """
    db = SessionLocal()

    try:
        logger.info(f"💾 Sauvegarde de {len(buckets_data)} buckets S3 pour {client_id} (session: {session_id})")

        # ========================================
        # ÉTAPE 1 : Créer un ScanRun
        # ========================================
        scan_run = ScanRun(
            session_id=session_id,
            client_id=client_id,
            service_type='s3',
            scan_timestamp=datetime.now(),
            total_resources=len(buckets_data),
            user_id=user_id,
            status='success'
        )
        db.add(scan_run)
        db.flush()
        
        logger.debug(f"✅ ScanRun créé avec ID: {scan_run.id}")
        
        # ========================================
        # ÉTAPE 2 : Sauvegarder chaque bucket
        # ========================================
        for bucket_data in buckets_data:
            # Extraire les données de performance
            performance_data = bucket_data.pop('performance', {})
            
            # Créer le bucket S3
            s3_bucket = S3Bucket(
                scan_run_id=scan_run.id,
                resource_id=bucket_data.get('resource_id'),
                bucket_name=bucket_data.get('bucket_name'),
                client_id=client_id,
                creation_date=bucket_data.get('creation_date'),
                region=bucket_data.get('region'),
                encryption_enabled=bucket_data.get('encryption_enabled', False),
                versioning_enabled=bucket_data.get('versioning_enabled', False),
                public_access_blocked=bucket_data.get('public_access_blocked', False),
                public_read_enabled=bucket_data.get('public_read_enabled', False),
                bucket_policy_enabled=bucket_data.get('bucket_policy_enabled', False),
                lifecycle_enabled=bucket_data.get('lifecycle_enabled', False),
                cors_enabled=bucket_data.get('cors_enabled', False),
                website_enabled=bucket_data.get('website_enabled', False),
                logging_enabled=bucket_data.get('logging_enabled', False),
                notifications_enabled=bucket_data.get('notifications_enabled', False),
                replication_enabled=bucket_data.get('replication_enabled', False),
                scan_timestamp=bucket_data.get('timestamp', datetime.now())
            )
            db.add(s3_bucket)
            db.flush()
            
            # Créer les performances associées
            s3_performance = S3Performance(
                s3_bucket_id=s3_bucket.id,
                all_requests=performance_data.get('all_requests'),
                get_requests=performance_data.get('get_requests'),
                put_requests=performance_data.get('put_requests'),
                delete_requests=performance_data.get('delete_requests'),
                errors_4xx=performance_data.get('4xx_errors'),
                errors_5xx=performance_data.get('5xx_errors'),
                first_byte_latency_avg=performance_data.get('first_byte_latency_avg'),
                total_request_latency_avg=performance_data.get('total_request_latency_avg'),
                bytes_downloaded=performance_data.get('bytes_downloaded'),
                bytes_uploaded=performance_data.get('bytes_uploaded')
            )
            db.add(s3_performance)
        
        # ========================================
        # ÉTAPE 3 : Commit de la transaction
        # ========================================
        # ✅ Marquer le scan comme terminé avec succès
        scan_run.status = 'success'
        db.commit()
        logger.success(f"✅ {len(buckets_data)} buckets S3 sauvegardés avec succès !")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur lors de la sauvegarde S3 : {e}")
        # Marquer le scan comme échoué
        try:
            scan_run.status = 'failed'
            db.commit()
        except:
            pass
        return False
        
    finally:
        db.close()


# ========================================
# FONCTION : save_vpc_scan
# ========================================
def save_vpc_scan(client_id: str, vpcs_data: List[dict], user_id: int = None, session_id: str = None) -> bool:
    """
    Sauvegarde les résultats d'un scan VPC dans la base de données.

    Args:
        client_id (str): Identifiant du client
        vpcs_data (List[dict]): Liste des VPCs avec leurs métadonnées et performances
        user_id (int): ID de l'utilisateur qui a lancé le scan
        session_id (str): ID de session pour grouper les scans multi-services

    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    db = SessionLocal()

    try:
        logger.info(f"💾 Sauvegarde de {len(vpcs_data)} VPCs pour {client_id} (session: {session_id})")

        # ÉTAPE 1 : Créer un ScanRun
        scan_run = ScanRun(
            session_id=session_id,
            client_id=client_id,
            service_type='vpc',
            scan_timestamp=datetime.now(),
            total_resources=len(vpcs_data),
            status='success',
            user_id=user_id
        )
        db.add(scan_run)
        db.flush()

        logger.debug(f"✅ ScanRun créé avec ID: {scan_run.id}")

        # ÉTAPE 2 : Sauvegarder chaque VPC
        for vpc_data in vpcs_data:
            performance_data = vpc_data.pop('performance', {})

            vpc_instance = VPCInstance(
                scan_run_id=scan_run.id,
                client_id=client_id,
                vpc_id=vpc_data.get('vpc_id'),
                cidr_block=vpc_data.get('cidr_block'),
                state=vpc_data.get('state'),
                is_default=vpc_data.get('is_default', False),
                tenancy=vpc_data.get('tenancy'),
                subnet_count=vpc_data.get('subnet_count', 0),
                public_subnets_count=vpc_data.get('public_subnets_count', 0),
                private_subnets_count=vpc_data.get('private_subnets_count', 0),
                internet_gateway_attached=vpc_data.get('internet_gateway_attached', False),
                nat_gateways_count=vpc_data.get('nat_gateways_count', 0),
                route_tables_count=vpc_data.get('route_tables_count', 0),
                security_groups_count=vpc_data.get('security_groups_count', 0),
                network_acls_count=vpc_data.get('network_acls_count', 0),
                flow_logs_enabled=vpc_data.get('flow_logs_enabled', False),
                vpc_endpoints_count=vpc_data.get('vpc_endpoints_count', 0),
                region=vpc_data.get('region'),
                tags=vpc_data.get('tags'),
                scan_timestamp=datetime.now()
            )
            db.add(vpc_instance)
            db.flush()

            # Créer les performances associées
            vpc_performance = VPCPerformance(
                vpc_instance_id=vpc_instance.id,
                network_in_bytes=performance_data.get('network_in_bytes'),
                network_out_bytes=performance_data.get('network_out_bytes'),
                network_packets_in=performance_data.get('network_packets_in'),
                network_packets_out=performance_data.get('network_packets_out')
            )
            db.add(vpc_performance)

        # ÉTAPE 3 : Commit de la transaction
        db.commit()
        logger.success(f"✅ {len(vpcs_data)} VPCs sauvegardés avec succès !")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur lors de la sauvegarde VPC : {e}")
        return False

    finally:
        db.close()


# ========================================
# FONCTION : save_rds_scan
# ========================================
def save_rds_scan(client_id: str, instances_data: List[dict], user_id: int = None, session_id: str = None) -> bool:
    """
    Sauvegarde les résultats d'un scan RDS dans la base de données.

    Args:
        client_id (str): Identifiant du client
        instances_data (List[dict]): Liste des instances RDS avec leurs métadonnées et performances
        user_id (int): ID de l'utilisateur qui a lancé le scan
        session_id (str): ID de session pour grouper les scans multi-services

    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    db = SessionLocal()

    try:
        logger.info(f"💾 Sauvegarde de {len(instances_data)} instances RDS pour {client_id} (session: {session_id})")

        # ÉTAPE 1 : Créer un ScanRun
        scan_run = ScanRun(
            session_id=session_id,
            client_id=client_id,
            service_type='rds',
            scan_timestamp=datetime.now(),
            total_resources=len(instances_data),
            status='success',
            user_id=user_id
        )
        db.add(scan_run)
        db.flush()

        logger.debug(f"✅ ScanRun créé avec ID: {scan_run.id}")

        # ÉTAPE 2 : Sauvegarder chaque instance RDS
        for instance_data in instances_data:
            performance_data = instance_data.pop('performance', {})

            rds_instance = RDSInstance(
                scan_run_id=scan_run.id,
                client_id=client_id,
                resource_id=instance_data.get('resource_id'),
                db_instance_identifier=instance_data.get('db_instance_identifier'),
                db_instance_class=instance_data.get('db_instance_class'),
                engine=instance_data.get('engine'),
                engine_version=instance_data.get('engine_version'),
                db_instance_status=instance_data.get('db_instance_status'),
                allocated_storage=instance_data.get('allocated_storage'),
                storage_type=instance_data.get('storage_type'),
                storage_encrypted=instance_data.get('storage_encrypted', False),
                iops=instance_data.get('iops'),
                vpc_id=instance_data.get('vpc_id'),
                db_subnet_group_name=instance_data.get('db_subnet_group_name'),
                availability_zone=instance_data.get('availability_zone'),
                multi_az=instance_data.get('multi_az', False),
                publicly_accessible=instance_data.get('publicly_accessible', False),
                endpoint_address=instance_data.get('endpoint_address'),
                endpoint_port=instance_data.get('endpoint_port'),
                master_username=instance_data.get('master_username'),
                iam_database_authentication_enabled=instance_data.get('iam_database_authentication_enabled', False),
                deletion_protection=instance_data.get('deletion_protection', False),
                backup_retention_period=instance_data.get('backup_retention_period'),
                preferred_backup_window=instance_data.get('preferred_backup_window'),
                preferred_maintenance_window=instance_data.get('preferred_maintenance_window'),
                latest_restorable_time=instance_data.get('latest_restorable_time'),
                auto_minor_version_upgrade=instance_data.get('auto_minor_version_upgrade', False),
                enhanced_monitoring_resource_arn=instance_data.get('enhanced_monitoring_resource_arn'),
                monitoring_interval=instance_data.get('monitoring_interval'),
                performance_insights_enabled=instance_data.get('performance_insights_enabled', False),
                region=instance_data.get('region'),
                tags=instance_data.get('tags'),
                security_groups=instance_data.get('security_groups'),
                parameter_groups=instance_data.get('parameter_groups'),
                option_groups=instance_data.get('option_groups'),
                instance_create_time=instance_data.get('instance_create_time'),
                scan_timestamp=datetime.now()
            )
            db.add(rds_instance)
            db.flush()

            # Créer les performances associées
            rds_performance = RDSPerformance(
                rds_instance_id=rds_instance.id,
                cpu_utilization_avg=performance_data.get('cpu_utilization_avg'),
                freeable_memory_bytes=performance_data.get('freeable_memory_bytes'),
                free_storage_space_bytes=performance_data.get('free_storage_space_bytes'),
                database_connections=performance_data.get('database_connections'),
                read_iops_avg=performance_data.get('read_iops_avg'),
                write_iops_avg=performance_data.get('write_iops_avg'),
                read_latency_avg=performance_data.get('read_latency_avg'),
                write_latency_avg=performance_data.get('write_latency_avg'),
                read_throughput_bytes=performance_data.get('read_throughput_bytes'),
                write_throughput_bytes=performance_data.get('write_throughput_bytes'),
                network_receive_throughput_bytes=performance_data.get('network_receive_throughput_bytes'),
                network_transmit_throughput_bytes=performance_data.get('network_transmit_throughput_bytes')
            )
            db.add(rds_performance)

        # ÉTAPE 3 : Commit de la transaction
        db.commit()
        logger.success(f"✅ {len(instances_data)} instances RDS sauvegardées avec succès !")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur lors de la sauvegarde RDS : {e}")
        return False

    finally:
        db.close()


# ========================================
# FONCTION : get_latest_ec2_instances
# ========================================
def get_latest_ec2_instances(client_id: str, limit: int = 10) -> List[dict]:
    """
    Récupère les dernières instances EC2 scannées pour un client.
    
    Args:
        client_id (str): Identifiant du client
        limit (int): Nombre maximum d'instances à retourner
        
    Returns:
        List[dict]: Liste des instances avec leurs performances
    """
    db = SessionLocal()
    
    try:
        # Requête pour récupérer les dernières instances
        instances = db.query(EC2Instance).filter(
            EC2Instance.client_id == client_id
        ).order_by(
            EC2Instance.scan_timestamp.desc()
        ).limit(limit).all()
        
        # Convertir en dictionnaires
        result = []
        for instance in instances:
            instance_dict = {
                "instance_id": instance.instance_id,
                "instance_type": instance.instance_type,
                "state": instance.state,
                "region": instance.region,
                "scan_timestamp": instance.scan_timestamp.isoformat() if instance.scan_timestamp else None,
            }
            
            # Ajouter les performances si disponibles
            if instance.performance:
                instance_dict["performance"] = {
                    "cpu_utilization_avg": instance.performance.cpu_utilization_avg,
                    "network_in_bytes": instance.performance.network_in_bytes,
                    "network_out_bytes": instance.performance.network_out_bytes,
                }
            
            result.append(instance_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des instances : {e}")
        return []

    finally:
        db.close()
