# 📊 Résumé de l'Infrastructure CloudDiagnoze

## 🌍 Vue d'ensemble

**3 régions EU-WEST** avec infrastructure identique dans chacune.

---

## 📦 Services provisionnés par région

### **EU-WEST-1 (Irlande)**
- ✅ 1 VPC (10.1.0.0/16)
- ✅ 2 Subnets (eu-west-1a, eu-west-1b)
- ✅ 1 Internet Gateway
- ✅ 1 Route Table
- ✅ 2 Security Groups (EC2 + RDS)
- ✅ 5 instances EC2 :
  - 2x t3.micro
  - 1x t2.micro
  - 1x t2.nano
  - 1x t3.small
- ✅ 1 instance RDS PostgreSQL (db.t3.micro)
- ✅ 5 buckets S3 :
  - clouddiagnoze-ireland-bucket-1-XXXX
  - clouddiagnoze-ireland-bucket-2-XXXX
  - clouddiagnoze-ireland-logs-XXXX
  - clouddiagnoze-ireland-backups-XXXX (avec versioning)
  - clouddiagnoze-ireland-static-XXXX

### **EU-WEST-2 (Londres)**
- ✅ 1 VPC (10.2.0.0/16)
- ✅ 2 Subnets (eu-west-2a, eu-west-2b)
- ✅ 1 Internet Gateway
- ✅ 1 Route Table
- ✅ 2 Security Groups (EC2 + RDS)
- ✅ 5 instances EC2 :
  - 2x t3.micro
  - 1x t2.micro
  - 1x t2.nano
  - 1x t3.small
- ✅ 1 instance RDS PostgreSQL (db.t3.micro)
- ✅ 5 buckets S3 :
  - clouddiagnoze-london-bucket-1-XXXX
  - clouddiagnoze-london-bucket-2-XXXX
  - clouddiagnoze-london-logs-XXXX
  - clouddiagnoze-london-backups-XXXX (avec versioning)
  - clouddiagnoze-london-static-XXXX

### **EU-WEST-3 (Paris)**
- ✅ 1 VPC (10.0.0.0/16)
- ✅ 2 Subnets (eu-west-3a, eu-west-3b)
- ✅ 1 Internet Gateway
- ✅ 1 Route Table
- ✅ 2 Security Groups (EC2 + RDS)
- ✅ 5 instances EC2 :
  - 2x t3.micro
  - 1x t2.micro
  - 1x t2.nano
  - 1x t3.small
- ✅ 1 instance RDS PostgreSQL (db.t3.micro)
- ✅ 5 buckets S3 :
  - clouddiagnoze-paris-bucket-1-XXXX
  - clouddiagnoze-paris-bucket-2-XXXX
  - clouddiagnoze-paris-logs-XXXX
  - clouddiagnoze-paris-backups-XXXX (avec versioning)
  - clouddiagnoze-paris-static-XXXX

---

## 🔢 Totaux globaux

| Ressource | Quantité totale |
|-----------|-----------------|
| **Régions** | 3 |
| **VPCs** | 3 |
| **Subnets** | 6 |
| **Internet Gateways** | 3 |
| **Route Tables** | 3 |
| **Security Groups** | 6 |
| **Instances EC2** | **15** |
| - t3.micro | 6 |
| - t2.micro | 3 |
| - t2.nano | 3 |
| - t3.small | 3 |
| **Instances RDS** | 3 |
| **Buckets S3** | **15** |

---

## 💰 Coûts mensuels estimés

| Service | Quantité | Prix/mois |
|---------|----------|-----------|
| EC2 t3.micro | 6 | ~$45 |
| EC2 t2.micro | 3 | ~$25 |
| EC2 t2.nano | 3 | ~$13 |
| EC2 t3.small | 3 | ~$45 |
| RDS db.t3.micro | 3 | ~$39 |
| S3 (stockage) | 15 | ~$5 |
| **TOTAL** | | **~$172/mois** |

---

## 🎯 Services scannables par CloudDiagnoze

### **Actuellement implémentés :**
- ✅ **EC2** - 15 instances (mix T2/T3)
- ✅ **S3** - 15 buckets

### **À implémenter (Étape 2) :**
- ⏳ **VPC** - 3 VPCs avec subnets, IGW, route tables
- ⏳ **RDS** - 3 instances PostgreSQL

---

## 📋 Commandes utiles

```bash
# Voir tous les outputs
terraform output

# Voir les IPs EC2 par région
terraform output paris_ec2_ips
terraform output ireland_ec2_ips
terraform output london_ec2_ips

# Voir les buckets S3 par région
terraform output paris_s3_buckets
terraform output ireland_s3_buckets
terraform output london_s3_buckets

# Voir le résumé global
terraform output summary
```

