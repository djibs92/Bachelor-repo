from typing import Any, List
from loguru import logger

class ScannerFactory:
    """Factory pour créer des scanners selon le provider + service"""
    
    @staticmethod
    def create_scanner(provider: str, service: str, session: Any, client_id: str,regions: str):
        """
        Créer un scanner selon le provider et le service
        
        Args:
            Provider: "aws" "gcp" "azure" ...
            service : "ec2" "s3" "rds" ...
            session : Session/Client configuré du provider
            client_id : ID du client pour AWS EC2
        
        Returns : 
            Scanner configuré pour le service
        """
        
        logger.info(f" Création scanner {provider}/{service}")
        
        if provider == "aws":
            return ScannerFactory._create_aws_scanner(service, session, client_id,regions)
        #Futur : elif provider == "gcp":
        #           return ScannerFactory._create_gcp_scanner(service,session)
        
        raise ValueError(f"Provider non supporté: {provider}")
    
    @staticmethod
    def _create_aws_scanner(service: str, session: Any, client_id: str, regions: List[str]):
        """Gère les différents scanne AWS"""
        if service == "ec2":
            from api.services.provider.aws.scanners.ec2_scan import EC2Scanner
            return EC2Scanner(session, client_id, regions)
        elif service == "s3":
            from api.services.provider.aws.scanners.s3_scan import S3Scanner
            return S3Scanner(session,client_id,regions)
        elif service == "vpc":
            from api.services.provider.aws.scanners.vpc_scanner import VPCScanner
            return VPCScanner(session,client_id,regions)
        elif service == "rds":
            from api.services.provider.aws.scanners.rds_scanner import RDSScanner
            return RDSScanner(session,client_id,regions)
        # elif service == "iam":
        #     from api.services.provider.aws.scanners.iam_scan import IAMScanner
        #     return IAMScanner(session,client_id,regions)
        raise ValueError(f"Service AWS non supporté: {service}")

    # def _create_gcp_scanner(service:str,session:Any):
    #     """Gère les différents scanner GCP """
    #     if service == "ComputeEngine" ect ....
