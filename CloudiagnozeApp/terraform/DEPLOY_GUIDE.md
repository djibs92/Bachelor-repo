# 🚀 Guide de Déploiement Rapide

## ⚡ Déploiement en 3 étapes

### 1️⃣ Réinitialiser Terraform (si ancien état existe)

```bash
cd CloudiagnozeApp/terraform
./reset.sh
```

### 2️⃣ Déployer l'infrastructure

```bash
./deploy.sh
```

**Durée estimée : 10-15 minutes**

### 3️⃣ Scanner avec CloudDiagnoze

Une fois déployé, lancer un scan :

```bash
# Depuis le front-end
# Aller sur : http://localhost:5500/design/config-scan-new.html
# Sélectionner : EC2 + S3
# Régions : eu-west-1, eu-west-2, eu-west-3
# Cliquer sur "Lancer le scan"
```

---

## 📊 Ce qui sera créé

### **3 Régions identiques :**

| Région | VPC CIDR | EC2 | S3 | RDS |
|--------|----------|-----|----|----|
| eu-west-1 (Irlande) | 10.1.0.0/16 | 5 | 5 | 1 |
| eu-west-2 (Londres) | 10.2.0.0/16 | 5 | 5 | 1 |
| eu-west-3 (Paris) | 10.0.0.0/16 | 5 | 5 | 1 |

**Total : 15 EC2 + 15 S3 + 3 RDS + 3 VPCs**

---

## 🧪 Vérifier le déploiement

```bash
# Voir les outputs
terraform output

# Vérifier les EC2
terraform output paris_ec2_ips
terraform output ireland_ec2_ips
terraform output london_ec2_ips

# Vérifier les S3
terraform output paris_s3_buckets
terraform output ireland_s3_buckets
terraform output london_s3_buckets

# Vérifier les RDS
terraform output paris_rds_endpoint
terraform output ireland_rds_endpoint
terraform output london_rds_endpoint
```

---

## 🗑️ Détruire l'infrastructure

```bash
./destroy.sh
```

**⚠️ IMPORTANT : Détruire après les tests pour éviter les coûts !**

---

## 🐛 Troubleshooting

### Erreur : "AMI not found"
Les AMI IDs peuvent changer. Vérifier les AMI Amazon Linux 2023 pour chaque région :
- eu-west-1 : https://console.aws.amazon.com/ec2/home?region=eu-west-1#AMICatalog
- eu-west-2 : https://console.aws.amazon.com/ec2/home?region=eu-west-2#AMICatalog
- eu-west-3 : https://console.aws.amazon.com/ec2/home?region=eu-west-3#AMICatalog

### Erreur : "RDS engine version not available"
Changer `engine_version` dans `modules/region/main.tf` :
```hcl
engine_version = "16.3"  # ou "15.5", "14.10"
```

### Erreur : "Bucket already exists"
Les noms de buckets S3 sont globalement uniques. Le `random_id` devrait éviter ça, mais si ça arrive :
```bash
./reset.sh  # Réinitialiser avec un nouveau random_id
```

