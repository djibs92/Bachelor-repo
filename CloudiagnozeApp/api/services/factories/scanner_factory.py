from typing import Any, List
from loguru import logger

class ScannerFactory:
    """Factory pour créer des scanners selon le provider + service"""

    @staticmethod
    def create_scanner(provider: str, service: str, session: Any, client_id: str, regions: str):
        logger.info(f" Création scanner {provider}/{service}")

        if provider == "aws":
            return ScannerFactory._create_aws_scanner(service, session, client_id, regions)

        raise ValueError(f"Provider non supporté: {provider}")

    @staticmethod
    def _create_aws_scanner(service: str, session: Any, client_id: str, regions: List[str]):
        if service == "ec2":
            from api.services.provider.aws.scanners.ec2_scan import EC2Scanner
            return EC2Scanner(session, client_id, regions)
        elif service == "s3":
            from api.services.provider.aws.scanners.s3_scan import S3Scanner
            return S3Scanner(session, client_id, regions)

        raise ValueError(f"Service AWS non supporté: {service}")
