from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

class CloudScanner(ABC):
    def __init__(self,session,client_id:str):
        self.session = session
        self.client_id = client_id
        self._clients_pool: Dict[str,Any] = {}


    @abstractmethod
    async def scan(self) -> List[dict]:
        """
        Scan et retourne une liste de dictionnaires contenant les métriques
        Chaque scanner implémente sa logique spécifique
        """
        pass

    # Recupère le client pour eviter des multi appels
    def get_client(self,service: str,region: str):
        """Récupère un client depuis le pool avec les gestions d'erreurs"""
        key = f"{service}_{region}"

        if key not in self._clients_pool:
            self._clients_pool[key] = self.session.client(service,region_name=region)
            logger.debug(f"Nouveau client {service} pour {region}")
        else:
            logger.debug(f"Réutilisation client {service} pour {region}")
        return self._clients_pool[key]

    # Retire un client qui echouerai potentiellement
    def invalidate_client(self,service:str,region:str):
        """Supprime un client défaillant du pool"""
        key = f"{service}_{region}"
        if key in self._clients_pool:
            del self._clients_pool[key]
            logger.warning(f"Client {service}_{region} supprimé du pool")


    def _create_event(self,resource_id:str,metric_name:str,metric_value) -> dict:
        """Helper permettant de créer des événements standardisés sous forme de dictionnaire"""
        return {
            "client_id": self.client_id,
            "resource_id": resource_id,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "timestamp": datetime.now().isoformat()
        }

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