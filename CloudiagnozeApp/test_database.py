"""
Script de test de la connexion à la base de données.

Ce script teste :
1. La connexion à MariaDB
2. L'import des modèles ORM
3. La sauvegarde de données de test
"""

from api.database import test_connection
from api.services.storage_service import save_ec2_scan, save_s3_scan, get_latest_ec2_instances
from loguru import logger

def main():
    logger.info("🧪 Test de la connexion à MariaDB")
    
    # Test 1 : Connexion
    if test_connection():
        logger.success("✅ Connexion réussie !")
    else:
        logger.error("❌ Connexion échouée !")
        return
    
    # Test 2 : Sauvegarde de données EC2 de test
    logger.info("\n🧪 Test de sauvegarde EC2")
    test_ec2_data = [
        {
            "resource_id": "arn:aws:ec2:eu-west-3:123456789:instance/i-test123",
            "instance_id": "i-test123",
            "instance_type": "t3.micro",
            "state": "running",
            "region": "eu-west-3",
            "ami_id": "ami-test",
            "availability_zone": "eu-west-3a",
            "vpc_id": "vpc-test",
            "private_ip": "10.0.1.10",
            "public_ip": "1.2.3.4",
            "tags": {"Name": "Test Instance"},
            "ebs_volumes": [{"device": "/dev/xvda", "size": 8}],
            "performance": {
                "cpu_utilization_avg": 25.5,
                "network_in_bytes": 1000000,
                "network_out_bytes": 500000
            }
        }
    ]
    
    if save_ec2_scan("TEST-CLIENT", test_ec2_data):
        logger.success("✅ Sauvegarde EC2 réussie !")
    else:
        logger.error("❌ Sauvegarde EC2 échouée !")
    
    # Test 3 : Sauvegarde de données S3 de test
    logger.info("\n🧪 Test de sauvegarde S3")
    test_s3_data = [
        {
            "resource_id": "arn:aws:s3:::test-bucket",
            "bucket_name": "test-bucket",
            "region": "eu-west-3",
            "encryption_enabled": True,
            "versioning_enabled": False,
            "public_access_blocked": True,
            "public_read_enabled": False,
            "performance": {
                "all_requests": 1000,
                "get_requests": 800,
                "put_requests": 200,
                "bytes_downloaded": 5000000,
                "bytes_uploaded": 1000000
            }
        }
    ]
    
    if save_s3_scan("TEST-CLIENT", test_s3_data):
        logger.success("✅ Sauvegarde S3 réussie !")
    else:
        logger.error("❌ Sauvegarde S3 échouée !")
    
    # Test 4 : Récupération des données
    logger.info("\n🧪 Test de récupération des données")
    instances = get_latest_ec2_instances("TEST-CLIENT", limit=5)
    logger.info(f"📊 {len(instances)} instances récupérées")
    for instance in instances:
        logger.info(f"  - {instance['instance_id']} ({instance['instance_type']}) - {instance['state']}")
    
    logger.success("\n✅ Tous les tests sont terminés !")

if __name__ == "__main__":
    main()

