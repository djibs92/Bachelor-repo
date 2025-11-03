#!/bin/bash

echo "🚀 TEST D'UN SCAN RÉEL EC2"
echo "=========================================="

# 1. Lancer le scan
echo ""
echo "📡 Lancement du scan EC2..."
SCAN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/scans" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aws",
    "services": ["ec2"],
    "auth_mode": {
      "type": "sts",
      "role_arn": "arn:aws:iam::730335226954:role/CloudDiagnoze-ScanRole"
    },
    "client_id": "ASM-Enterprise",
    "regions": ["eu-west-3"]
  }')

echo "$SCAN_RESPONSE"
SCAN_ID=$(echo "$SCAN_RESPONSE" | grep -o '"scan_id":"[^"]*"' | cut -d'"' -f4)
echo "✅ Scan lancé : $SCAN_ID"

# 2. Attendre que le scan se termine
echo ""
echo "⏳ Attente de 15 secondes pour que le scan se termine..."
sleep 15

# 3. Récupérer l'historique des scans
echo ""
echo "📊 Récupération de l'historique des scans..."
curl -s -X GET "http://localhost:8000/api/v1/scans/history?client_id=ASM-Enterprise&limit=3" | python3 -m json.tool

# 4. Récupérer les instances EC2
echo ""
echo "📊 Récupération des instances EC2..."
curl -s -X GET "http://localhost:8000/api/v1/ec2/instances?client_id=ASM-Enterprise&limit=5" | python3 -m json.tool

echo ""
echo "=========================================="
echo "✅ TEST TERMINÉ !"

