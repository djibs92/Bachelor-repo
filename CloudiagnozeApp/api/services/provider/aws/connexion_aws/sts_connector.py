"""
Coder les différents mode de connexion accéptés.
"""

from loguru import logger
import boto3, os

def get_assumed_session(role_arn: str):
    """Pour facilité le client ont créer l'assume role a sa place"""
    """Chose a déterminer en fonction de la technicité du client"""
    logger.info("🔐 Démarrage AssumeRole avec ARN : {}", role_arn)
    try:
        sts = boto3.client(
            "sts",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "eu-west-1")
        )

        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName="CloudDiagnozeSession"
        )

        logger.success("✅ AssumeRole réussi. Expire à : {}", response['Credentials']['Expiration'])

        credentials = response['Credentials']
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=os.getenv("AWS_DEFAULT_REGION", "eu-west-1")
        )
        return session

    except Exception as e:
        logger.error("❌ Erreur AssumeRole : {}", str(e))
        raise ValueError(f"Impossible de se connecter au compte AWS : {str(e)}")
        