"""
Vérifie s'il y a des instances RDS dans le compte AWS
"""
import requests
import json

# Token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGNsb3VkZGlhZ25vemUuY29tIiwidXNlcl9pZCI6OCwiZXhwIjoxNzY0MTU4NDY2fQ.xUd9fl3IKkh8ZX-nf9_jfOY3UOEcRkl6CL_8AxiZ6uA"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 60)
print("🧪 VÉRIFICATION DU SCAN RDS")
print("=" * 60)

# 1. Lancer un scan RDS seul
print("\n1️⃣ Lancement d'un scan RDS...")
scan_payload = {
    "provider": "aws",
    "services": ["rds"],
    "auth_mode": {
        "type": "sts",
        "role_arn": "arn:aws:iam::730335226954:role/CloudDiagnoze-ScanRole"
    },
    "client_id": "TEST-RDS",
    "regions": ["eu-west-3", "us-east-1"]
}

response = requests.post("http://localhost:8000/api/v1/scans", json=scan_payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# 2. Attendre 30 secondes
print("\n⏳ Attente de 30 secondes...")
import time
time.sleep(30)

# 3. Vérifier l'historique
print("\n2️⃣ Vérification de l'historique des scans...")
response = requests.get("http://localhost:8000/api/v1/scans/history?limit=5", headers=headers)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Total scans: {data['total_scans']}")

for scan in data['scans']:
    print(f"\n  📋 Scan #{scan['scan_id']}:")
    print(f"     Service: {scan['service_type']}")
    print(f"     Client: {scan['client_id']}")
    print(f"     Ressources: {scan['total_resources']}")
    print(f"     Status: {scan['status']}")
    print(f"     Timestamp: {scan['scan_timestamp']}")

# 4. Vérifier les instances RDS
print("\n3️⃣ Vérification des instances RDS...")
response = requests.get("http://localhost:8000/api/v1/rds/instances?latest_only=false&limit=100", headers=headers)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Total instances RDS: {data['total_instances']}")

if data['instances']:
    for instance in data['instances']:
        print(f"\n  🗄️ Instance: {instance['db_instance_identifier']}")
        print(f"     Classe: {instance['db_instance_class']}")
        print(f"     Moteur: {instance['engine']} {instance['engine_version']}")
        print(f"     Région: {instance['region']}")
        print(f"     Status: {instance['db_instance_status']}")
else:
    print("  ℹ️ Aucune instance RDS trouvée")

print("\n" + "=" * 60)
print("✅ Test terminé")
print("=" * 60)

