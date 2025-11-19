"""
Test direct du scanner RDS pour déboguer
"""
import sys
sys.path.insert(0, 'CloudiagnozeApp')

import boto3
from api.services.provider.aws.scanners.rds_scanner import RDSScanner
from api.database import SessionLocal

# Créer une session AWS
session = boto3.Session()

# Assumer le rôle
sts_client = session.client('sts')
assumed_role = sts_client.assume_role(
    RoleArn="arn:aws:iam::730335226954:role/CloudDiagnoze-ScanRole",
    RoleSessionName="CloudDiagnoze-Test-RDS"
)

# Créer une nouvelle session avec les credentials temporaires
temp_session = boto3.Session(
    aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
    aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
    aws_session_token=assumed_role['Credentials']['SessionToken']
)

# Créer le scanner
scanner = RDSScanner(
    session=temp_session,
    client_id="ASM-Enterprise",
    regions=["eu-west-3"]
)

# Lancer le scan
db = SessionLocal()
try:
    print("🧪 Test du scanner RDS...")
    result = scanner.scan(db, user_id=8)
    print(f"✅ Résultat: {result}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

