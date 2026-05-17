from typing import List, Dict, Any
from loguru import logger
from api.services.factories.connection_factory import ConnectionFactory
from api.services.factories.scanner_factory import ScannerFactory
from api.services.storage_service import save_ec2_scan, save_s3_scan


SAVE_FUNCTIONS = {
    "ec2": save_ec2_scan,
    "s3": save_s3_scan,
}


async def scan_list_service(scan_id: str, provider: str, services: List[str], auth_mode: Dict[str, Any], client_id: str, regions: List[str] = None, user_id: int = None):
    """
    Moteur principal de CloudDiagnoze.
    Orchestre les scans EC2 et S3 pour chaque service demandé.

    Args:
        scan_id: ID unique du scan (sert de session_id pour grouper les services)
        provider: Provider cloud (aws)
        services: Liste des services à scanner (ec2, s3)
        auth_mode: Mode d'authentification
        client_id: ID du client
        regions: Régions à scanner (optionnel, toutes si absent)
        user_id: ID de l'utilisateur qui lance le scan (isolation multi-tenant)
    """
    logger.info(f"🚀 Démarrage scan_list_service pour scan_id: {scan_id}")
    logger.info(f"Provider: {provider}, Services: {services}, User ID: {user_id}")

    # Le scan_id sert de session_id pour grouper tous les services scannés ensemble
    session_id = scan_id
    logger.info(f"📦 Session ID pour ce groupe de scans: {session_id}")

    try:
        # 1. Connexion au provider
        session = ConnectionFactory.create_connection(provider, auth_mode)
        logger.success(f"Connexion {provider} établie")

        # 2. Pour chaque service, lancer le scanner approprié
        results = []
        for service in services:
            logger.info(f"🔍 Scan du service : {service}")

            # Créer le scanner
            scanner = ScannerFactory.create_scanner(provider, service, session, client_id, regions)

            # Tous les scanners utilisent maintenant le même pattern : scan() → List[dict]
            result = await scanner.scan()
            results.append(result)
            logger.success(f"✅ Service {service} scanné : {len(result)} ressources trouvées")

            # 3. Sauvegarder les résultats en base de données via storage_service
            if result:
                save_function = SAVE_FUNCTIONS.get(service)
                if save_function:
                    logger.info(f"💾 Sauvegarde des résultats {service} en BDD...")
                    # Passer le session_id pour grouper les scans
                    if save_function(client_id, result, user_id, session_id):
                        logger.success(f"✅ {len(result)} ressources {service.upper()} sauvegardées en BDD (session: {session_id})")
                    else:
                        logger.warning(f"⚠️ Échec de la sauvegarde {service.upper()} en BDD")
                else:
                    logger.warning(f"⚠️ Pas de fonction de sauvegarde pour le service {service}")

        logger.success(f"🎉 Scan {scan_id} terminé avec succès")

    except Exception as e:
        logger.error(f"❌ Erreur scan {scan_id}: {str(e)}")
        raise
        
