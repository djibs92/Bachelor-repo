"""
Script de test des nouveaux endpoints de récupération de données.

Ce script teste :
1. Lancement d'un scan EC2
2. Récupération de l'historique des scans
3. Récupération des instances EC2
4. Récupération d'une instance spécifique
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_scan_ec2():
    """Lance un scan EC2"""
    print("\n🧪 TEST 1 : Lancement d'un scan EC2")
    print("=" * 60)
    
    payload = {
        "provider": "aws",
        "services": ["ec2"],
        "auth_mode": {
            "type": "assume_role",
            "role_arn": "arn:aws:iam::730335226954:role/CloudDiagnoze-ScanRole"
        },
        "client_id": "ASM-Enterprise",
        "regions": ["eu-west-3"]
    }
    
    response = requests.post(f"{BASE_URL}/scans", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 202:
        print("✅ Scan lancé avec succès !")
        print("⏳ Attente de 10 secondes pour que le scan se termine...")
        time.sleep(10)
        return True
    else:
        print("❌ Échec du lancement du scan")
        return False


def test_get_scans_history():
    """Récupère l'historique des scans"""
    print("\n🧪 TEST 2 : Récupération de l'historique des scans")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/scans/history?client_id=ASM-Enterprise&limit=5")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['total_scans']} scans trouvés")
        for scan in data['scans']:
            print(f"  - Scan #{scan['scan_id']} ({scan['service_type']}) : {scan['total_resources']} ressources - {scan['scan_timestamp']}")
        return True
    else:
        print(f"❌ Erreur: {response.text}")
        return False


def test_get_ec2_instances():
    """Récupère les instances EC2"""
    print("\n🧪 TEST 3 : Récupération des instances EC2")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/ec2/instances?client_id=ASM-Enterprise&limit=10")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['total_instances']} instances trouvées")
        for instance in data['instances'][:3]:  # Afficher seulement les 3 premières
            print(f"\n  Instance: {instance['instance_id']}")
            print(f"    Type: {instance['instance_type']}")
            print(f"    État: {instance['state']}")
            print(f"    Région: {instance['region']}")
            if 'performance' in instance:
                print(f"    CPU: {instance['performance'].get('cpu_utilization_avg')}%")
        return data['instances'][0]['instance_id'] if data['instances'] else None
    else:
        print(f"❌ Erreur: {response.text}")
        return None


def test_get_ec2_instance_history(instance_id):
    """Récupère l'historique d'une instance spécifique"""
    print(f"\n🧪 TEST 4 : Récupération de l'historique de l'instance {instance_id}")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/ec2/instances/{instance_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['total_scans']} scans trouvés pour {instance_id}")
        for entry in data['history']:
            print(f"  - {entry['scan_timestamp']} : {entry['state']} (CPU: {entry.get('performance', {}).get('cpu_utilization_avg')}%)")
        return True
    else:
        print(f"❌ Erreur: {response.text}")
        return False


def test_get_s3_buckets():
    """Récupère les buckets S3"""
    print("\n🧪 TEST 5 : Récupération des buckets S3")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/s3/buckets?client_id=ASM-Enterprise&limit=10")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['total_buckets']} buckets trouvés")
        for bucket in data['buckets'][:3]:  # Afficher seulement les 3 premiers
            print(f"\n  Bucket: {bucket['bucket_name']}")
            print(f"    Région: {bucket['region']}")
            print(f"    Chiffrement: {bucket['encryption_enabled']}")
            print(f"    Versioning: {bucket['versioning_enabled']}")
        return True
    else:
        print(f"❌ Erreur: {response.text}")
        return False


def main():
    print("🚀 TESTS DES NOUVEAUX ENDPOINTS")
    print("=" * 60)
    
    # Test 1 : Lancer un scan
    if not test_scan_ec2():
        print("\n❌ Échec du test 1, arrêt des tests")
        return
    
    # Test 2 : Historique des scans
    test_get_scans_history()
    
    # Test 3 : Récupérer les instances EC2
    instance_id = test_get_ec2_instances()
    
    # Test 4 : Historique d'une instance spécifique
    if instance_id:
        test_get_ec2_instance_history(instance_id)
    
    # Test 5 : Récupérer les buckets S3
    test_get_s3_buckets()
    
    print("\n" + "=" * 60)
    print("✅ TOUS LES TESTS SONT TERMINÉS !")
    print("=" * 60)


if __name__ == "__main__":
    main()

