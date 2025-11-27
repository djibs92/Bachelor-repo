from typing import Dict, Any
from loguru import logger


class ConnectionFactory:
    """Factory pour créer les connexions selon provider + auth_mode"""

    @staticmethod
    def create_connection(provider: str, auth_mode: Dict[str, Any]):
        """
        Crée une connexion selon le provider et le mode d'authentification

        Args:
            provider: "aws", "gcp", "azure"...
            auth_mode: {"type": "sts", "role_arn": "..."}

        Returns:
            Session/Client configuré pour le provider
        """
        logger.info(f"🔗 Création connexion {provider} avec mode {auth_mode['type']}")

        if provider == "aws":
            return ConnectionFactory._create_aws_connection(auth_mode)

        # Futur: elif provider == "gcp":
        #     return ConnectionFactory._create_gcp_connection(auth_mode)
        # elif provider == "azure" :
        #    return ConnectionFactory._create_gcp_connection(auth_mode)

        raise ValueError(f"Provider non supporté: {provider}")

    @staticmethod
    def _create_aws_connection(auth_mode: Dict[str, Any]):
        """Gère les différents modes de connexion AWS"""

        if auth_mode["type"] == "sts":
            from api.services.provider.aws.connexion_aws.sts_connector import (
                get_assumed_session,
            )

            return get_assumed_session(auth_mode["role_arn"])

        # Futur: elif auth_mode["type"] == "access_key":
        #     from api.services.provider.aws.connection.access_key_connector import create_session
        #     return create_session(auth_mode["access_key"], auth_mode["secret_key"])

        raise ValueError(
            f"Mode d'authentification AWS non supporté: {auth_mode['type']}"
        )
