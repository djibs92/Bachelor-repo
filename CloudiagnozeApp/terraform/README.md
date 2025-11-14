# 🚀 Terraform Multi-Régions CloudDiagnoze

## 📋 Vue d'ensemble

Ce Terraform provisionne une infrastructure complète dans **3 régions EU-WEST** :

| Région | Code | Ressources |
|--------|------|------------|
| **eu-west-1** | ireland | 5 EC2 + 5 S3 + 1 RDS + 1 VPC |
| **eu-west-2** | london | 5 EC2 + 5 S3 + 1 RDS + 1 VPC |
| **eu-west-3** | paris | 5 EC2 + 5 S3 + 1 RDS + 1 VPC |

**Total : 15 EC2 + 15 S3 + 3 RDS + 3 VPCs**

---

## 🏗️ Architecture

Chaque région contient :

```
VPC (10.X.0.0/16)
├── Subnet 1 (AZ-a)
├── Subnet 2 (AZ-b)
├── Internet Gateway
├── Route Table
├── Security Groups (EC2 + RDS)
├── 5 instances EC2 (mix T2/T3)
│   ├── 2x t3.micro
│   ├── 1x t2.micro
│   ├── 1x t2.nano
│   └── 1x t3.small
├── 1 instance RDS PostgreSQL (db.t3.micro)
└── 5 buckets S3
    ├── bucket-1
    ├── bucket-2
    ├── logs
    ├── backups (avec versioning)
    └── static
```

---

## 🚀 Déploiement

### 1. Initialiser Terraform

```bash
cd CloudiagnozeApp/terraform
terraform init
```

### 2. Vérifier le plan

```bash
terraform plan
```

### 3. Déployer l'infrastructure

```bash
# Avec le script automatique
./deploy.sh

# Ou manuellement
export AWS_PROFILE=terraform-provisionner
terraform apply -auto-approve
```

---

## 🧪 Scanner l'infrastructure

Une fois déployé, scanner avec CloudDiagnoze :

```bash
# Scanner les 3 régions
curl -X POST "http://localhost:8000/api/v1/scans" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "provider": "aws",
    "services": ["ec2", "s3"],
    "auth_mode": {
      "type": "sts",
      "role_arn": "arn:aws:iam::ACCOUNT_ID:role/CloudDiagnoze-ScanRole"
    },
    "regions": ["eu-west-1", "eu-west-2", "eu-west-3"]
  }'
```

---

## 🗑️ Détruire l'infrastructure

```bash
# Avec le script automatique
./destroy.sh

# Ou manuellement
export AWS_PROFILE=terraform-provisionner
terraform destroy -auto-approve
```

---

## 💰 Estimation des coûts

**Coûts mensuels approximatifs (si toujours actif) :**

| Service | Quantité | Prix unitaire | Total/mois |
|---------|----------|---------------|------------|
| EC2 t3.micro | 6 (2 par région) | $0.0104/h | ~$45 |
| EC2 t2.micro | 3 (1 par région) | $0.0116/h | ~$25 |
| EC2 t2.nano | 3 (1 par région) | $0.0058/h | ~$13 |
| EC2 t3.small | 3 (1 par région) | $0.0208/h | ~$45 |
| RDS db.t3.micro | 3 | $0.018/h | ~$39 |
| S3 (stockage) | 15 buckets | ~$0.023/GB | ~$5 |
| **TOTAL** | | | **~$172/mois** |

⚠️ **Pense à détruire l'infrastructure après les tests !**

---

## 📊 Outputs

Après déploiement, Terraform affiche :

- IPs publiques des 15 instances EC2
- Endpoints des 3 instances RDS
- Noms des 15 buckets S3
- IDs des 3 VPCs

```bash
terraform output
```

