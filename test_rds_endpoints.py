"""
Script de test pour les endpoints RDS de CloudDiagnoze.

Ce script teste :
1. Lancement d'un scan RDS
2. Récupération des instances RDS
3. Vérification des données

Usage:
    python3 test_rds_endpoints.py
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

# Token d'authentification (à remplacer par votre token)
# Pour obtenir un token, utilisez l'endpoint /auth/login
TOKEN = "YOUR_TOKEN_HERE"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_scan_rds():
    """Lance un scan RDS"""
    print("\n🧪 TEST 1 : Lancement d'un scan RDS")
    print("=" * 60)
    
    payload = {
        "provider": "aws",
        "services": ["rds"],
        "auth_mode": {
            "type": "assume_role",
            "role_arn": "arn:aws:iam::730335226954:role/CloudDiagnoze-ScanRole"
        },
        "client_id": "ASM-Enterprise",
        "regions": ["eu-west-3"]
    }
    
    response = requests.post(f"{BASE_URL}/scans", json=payload, headers=HEADERS)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 202:
        print("✅ Scan RDS lancé avec succès !")
        print("⏳ Attente de 15 secondes pour que le scan se termine...")
        time.sleep(15)
        return True
    else:
        print("❌ Échec du lancement du scan RDS")
        return False

def test_get_rds_instances():
    """Récupère les instances RDS"""
    print("\n🧪 TEST 2 : Récupération des instances RDS")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/rds/instances", headers=HEADERS)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Instances RDS récupérées avec succès !")
        print(f"📊 Nombre total d'instances: {data.get('total_instances', 0)}")
        
        if data.get('instances'):
            print(f"\n📋 Détails de la première instance:")
            first_instance = data['instances'][0]
            print(f"  - Identifiant: {first_instance.get('db_instance_identifier')}")
            print(f"  - Classe: {first_instance.get('db_instance_class')}")
            print(f"  - Moteur: {first_instance.get('engine')} {first_instance.get('engine_version')}")
            print(f"  - Statut: {first_instance.get('db_instance_status')}")
            print(f"  - Région: {first_instance.get('region')}")
            print(f"  - Multi-AZ: {first_instance.get('multi_az')}")
            print(f"  - Stockage: {first_instance.get('allocated_storage')} GB ({first_instance.get('storage_type')})")
            print(f"  - Chiffré: {first_instance.get('storage_encrypted')}")
            
            if first_instance.get('performance'):
                perf = first_instance['performance']
                print(f"\n  📊 Métriques de performance:")
                print(f"    - CPU: {perf.get('cpu_utilization_avg')}%")
                print(f"    - Connexions: {perf.get('database_connections')}")
                print(f"    - IOPS lecture: {perf.get('read_iops_avg')}")
                print(f"    - IOPS écriture: {perf.get('write_iops_avg')}")
        
        return True
    else:
        print(f"❌ Échec de la récupération des instances RDS")
        print(f"Response: {response.text}")
        return False

def test_get_latest_session():
    """Récupère la dernière session de scan"""
    print("\n🧪 TEST 3 : Récupération de la dernière session de scan")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/scans/latest-session", headers=HEADERS)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session récupérée avec succès !")
        print(f"📅 Timestamp: {data.get('session_timestamp')}")
        print(f"🔧 Services scannés: {data.get('services')}")
        print(f"📊 Nombre de scans: {len(data.get('scans', []))}")
        
        # Vérifier si RDS est dans les services
        if 'rds' in data.get('services', []):
            print("✅ RDS est bien présent dans la session !")
        
        return True
    else:
        print(f"❌ Échec de la récupération de la session")
        return False

def main():
    """Fonction principale"""
    print("\n" + "=" * 60)
    print("🧪 TESTS DES ENDPOINTS RDS - CloudDiagnoze")
    print("=" * 60)
    
    # Vérifier que le token est configuré
    if TOKEN == "YOUR_TOKEN_HERE":
        print("\n⚠️ ATTENTION : Vous devez configurer votre token d'authentification !")
        print("1. Lancez le backend : cd CloudiagnozeApp && uvicorn api.main:app --reload")
        print("2. Connectez-vous via /auth/login pour obtenir un token")
        print("3. Remplacez 'YOUR_TOKEN_HERE' dans ce script par votre token")
        return
    
    # Lancer les tests
    results = []
    
    # Test 1 : Scan RDS
    results.append(("Scan RDS", test_scan_rds()))
    
    # Test 2 : Récupération des instances
    results.append(("Récupération instances RDS", test_get_rds_instances()))
    
    # Test 3 : Session de scan
    results.append(("Session de scan", test_get_latest_session()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_pass = sum(1 for _, result in results if result)
    print(f"\n🎯 Score: {total_pass}/{len(results)} tests réussis")

if __name__ == "__main__":
    main()

