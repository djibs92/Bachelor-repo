"""
Script de debug pour tester le scan RDS directement
"""
import sys
sys.path.insert(0, 'CloudiagnozeApp')

import boto3
from loguru import logger

# Configuration du logging
logger.remove()
logger.add(sys.stdout, level="DEBUG")

logger.info("🧪 Test de connexion RDS AWS")

try:
    # Créer une session AWS
    session = boto3.Session()
    
    # Assumer le rôle
    logger.info("🔑 Assumption du rôle CloudDiagnoze-ScanRole...")
    sts_client = session.client('sts')
    assumed_role = sts_client.assume_role(
        RoleArn="arn:aws:iam::730335226954:role/CloudDiagnoze-ScanRole",
        RoleSessionName="CloudDiagnoze-Debug-RDS"
    )
    
    # Créer une nouvelle session avec les credentials temporaires
    temp_session = boto3.Session(
        aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
        aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
        aws_session_token=assumed_role['Credentials']['SessionToken']
    )
    logger.success("✅ Rôle assumé avec succès")
    
    # Tester plusieurs régions
    regions = ["eu-west-3", "eu-west-1", "us-east-1"]
    
    total_instances = 0
    
    for region in regions:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 Scan de la région {region}")
        logger.info(f"{'='*60}")
        
        try:
            rds_client = temp_session.client('rds', region_name=region)
            
            # Lister les instances RDS
            logger.info(f"📡 Appel describe_db_instances() pour {region}...")
            response = rds_client.describe_db_instances()
            
            instances = response.get('DBInstances', [])
            logger.info(f"📊 {len(instances)} instances RDS trouvées dans {region}")
            
            if instances:
                for instance in instances:
                    db_id = instance.get('DBInstanceIdentifier', 'N/A')
                    db_class = instance.get('DBInstanceClass', 'N/A')
                    engine = instance.get('Engine', 'N/A')
                    engine_version = instance.get('EngineVersion', 'N/A')
                    status = instance.get('DBInstanceStatus', 'N/A')
                    
                    logger.success(f"  🗄️  Instance: {db_id}")
                    logger.info(f"     Classe: {db_class}")
                    logger.info(f"     Moteur: {engine} {engine_version}")
                    logger.info(f"     Status: {status}")
                    
                    total_instances += 1
            else:
                logger.warning(f"  ⚠️  Aucune instance RDS dans {region}")
                
        except Exception as e:
            logger.error(f"❌ Erreur dans {region}: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info(f"\n{'='*60}")
    logger.success(f"✅ Total: {total_instances} instances RDS trouvées")
    logger.info(f"{'='*60}")
    
except Exception as e:
    logger.error(f"❌ Erreur globale: {e}")
    import traceback
    traceback.print_exc()

