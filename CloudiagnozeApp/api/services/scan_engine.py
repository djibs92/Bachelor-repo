from typing import List, Dict, Any
from loguru import logger
from api.services.factories.connection_factory import ConnectionFactory
from api.services.factories.scanner_factory import ScannerFactory
from api.services.storage_service import save_ec2_scan, save_s3_scan
from api.database.connection import SessionLocal

async def scan_list_service(scan_id: str, provider: str, services: List[str], auth_mode: Dict[str, Any], client_id: str, regions: List[str] = None, user_id: int = None):
    """
    Moteur principal de CloudDiagnoze
    Orchestrateur qui lance les scans pour chaque service demandé

    Args:
        scan_id: ID unique du scan
        provider: Provider cloud (aws, azure, gcp)
        services: Liste des services à scanner (ec2, s3, vpc)
        auth_mode: Mode d'authentification
        client_id: ID du client
        regions: Régions à scanner (optionnel)
        user_id: ID de l'utilisateur qui lance le scan (pour isolation des comptes)
    """
    logger.info(f"🚀 Démarrage scan_list_service pour scan_id: {scan_id}")
    logger.info(f"Provider: {provider}, Services: {services}, User ID: {user_id}")

    try:
        # 1. Connexion au provider (Connexion via le mode de connexion propre au provider Key/AWS STS ect ....)
        session = ConnectionFactory.create_connection(provider,auth_mode)
        logger.success(f"Connexion {provider} établie")

        # 2. Pour chaque service, lancer le scanner approprié
        results = []
        for service in services:
            logger.info(f"🔍 Scan du service : {service}")

            scanner = ScannerFactory.create_scanner(provider, service, session, client_id, regions)

            # VPC scanner écrit directement en BDD (pas Event2CBP)
            if service == "vpc":
                db = SessionLocal()
                try:
                    result = scanner.scan(db, user_id)
                    results.append(result)
                    logger.success(f"✅ VPC scanné : {result.get('total_vpcs', 0)} VPCs trouvés et sauvegardés")
                except Exception as e:
                    logger.error(f"❌ Erreur scan VPC : {e}")
                    db.rollback()
                    raise
                finally:
                    db.close()

            # EC2 et S3 utilisent Event2CBP
            else:
                result = await scanner.scan()
                results.append(result)
                logger.success(f"✅ Service {service} scanné : {len(result)} événements trouvés")

                # 3. Sauvegarder les résultats en base de données
                logger.info(f"💾 Sauvegarde des résultats {service} en BDD...")
                if service == "ec2" and result:
                    if save_ec2_scan(client_id, result, user_id):
                        logger.success(f"✅ {len(result)} instances EC2 sauvegardées en BDD")
                    else:
                        logger.warning(f"⚠️ Échec de la sauvegarde EC2 en BDD")

                elif service == "s3" and result:
                    if save_s3_scan(client_id, result, user_id):
                        logger.success(f"✅ {len(result)} buckets S3 sauvegardés en BDD")
                    else:
                        logger.warning(f"⚠️ Échec de la sauvegarde S3 en BDD")

        logger.success(f"🎉 Scan {scan_id} terminé avec succès")

    except Exception as e :
        logger.error(f"❌ Erreur scan {scan_id}: {str(e)}")
        raise
        
