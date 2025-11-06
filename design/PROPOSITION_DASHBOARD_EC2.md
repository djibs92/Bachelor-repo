# 📊 PROPOSITION DASHBOARD EC2

## 🎯 OBJECTIF
Créer un dashboard qui affiche **vraiment** ce qu'on récupère du scanner EC2, pas des données génériques.

---

## 📋 CE QU'ON RÉCUPÈRE DU SCANNER EC2

### **1. Métadonnées des instances**
- ✅ `instance_id` - ID de l'instance
- ✅ `instance_type` - Type (t3.micro, t2.small, etc.)
- ✅ `state` - État (running, stopped, terminated)
- ✅ `region` - Région AWS
- ✅ `availability_zone` - Zone de disponibilité
- ✅ `vpc_id` - VPC
- ✅ `subnet_id` - Sous-réseau
- ✅ `private_ip` - IP privée
- ✅ `public_ip` - IP publique
- ✅ `ami_id` - Image AMI
- ✅ `launch_time` - Date de lancement
- ✅ `tags` - Tags (Name, Environment, etc.)
- ✅ `ebs_volumes` - Volumes EBS attachés

### **2. Métriques de performance (CloudWatch)**
- ✅ `cpu_utilization_avg` - CPU moyen (%)
- ✅ `memory_utilization_avg` - Mémoire moyenne (%) - **null pour l'instant**
- ✅ `network_in_bytes` - Trafic entrant (bytes)
- ✅ `network_out_bytes` - Trafic sortant (bytes)

---

## 🎨 PROPOSITION DE DASHBOARD EC2

### **SECTION 1 : VUE D'ENSEMBLE (Stats Cards)**

#### **Card 1 : Total Instances EC2**
- **Valeur** : Nombre total d'instances
- **Sous-info** : Répartition par état (running, stopped, terminated)
- **Exemple** : `5 instances` → `3 running, 2 stopped`

#### **Card 2 : Instances par Région**
- **Valeur** : Nombre de régions actives
- **Sous-info** : Région la plus utilisée
- **Exemple** : `2 régions` → `eu-west-3 (3), us-east-1 (2)`

#### **Card 3 : CPU Moyen Global**
- **Valeur** : Moyenne CPU de toutes les instances running
- **Sous-info** : Tendance (↑ ou ↓)
- **Exemple** : `42.5%` → `+5.2% vs hier`

#### **Card 4 : Trafic Réseau Total**
- **Valeur** : Somme du trafic IN + OUT
- **Sous-info** : Répartition IN/OUT
- **Exemple** : `1.2 GB` → `800 MB IN, 400 MB OUT`

---

### **SECTION 2 : GRAPHIQUES**

#### **Graphique 1 : Répartition par Type d'Instance (Donut Chart)**
- **Données** : Compter les instances par type (t3.micro, t2.small, etc.)
- **Exemple** : 
  - t3.micro : 3 instances (60%)
  - t2.small : 2 instances (40%)

#### **Graphique 2 : Répartition par État (Bar Chart)**
- **Données** : Compter les instances par état
- **Exemple** :
  - Running : 3
  - Stopped : 2
  - Terminated : 0

#### **Graphique 3 : CPU par Instance (Bar Chart Horizontal)**
- **Données** : Afficher le CPU de chaque instance
- **Exemple** :
  - i-031d1165961f51bda : 55%
  - i-0bf7f50899bb31629 : 32%
  - i-0f9e4798cf8a7ae50 : 40%

#### **Graphique 4 : Trafic Réseau par Instance (Stacked Bar)**
- **Données** : Trafic IN/OUT par instance
- **Exemple** :
  - i-031d1165961f51bda : 38 MB IN, 42 MB OUT
  - i-0bf7f50899bb31629 : 9 KB IN, 10 KB OUT

---

### **SECTION 3 : TABLEAU DES INSTANCES**

#### **Colonnes du tableau**
| Colonne | Données | Exemple |
|---------|---------|---------|
| **Name** | Tag "Name" | CloudDiagnoze-EC2-0 |
| **Instance ID** | instance_id | i-0bf7f50899bb31629 |
| **Type** | instance_type | t3.micro |
| **État** | state (badge coloré) | 🟢 running |
| **Région** | region | eu-west-3 |
| **IP Publique** | public_ip | 15.236.144.245 |
| **CPU** | cpu_utilization_avg | 32% |
| **Trafic** | network_in + network_out | 19 KB |
| **Lancée le** | launch_time | 03/11/2025 13:31 |

#### **Fonctionnalités du tableau**
- ✅ Tri par colonne (cliquer sur l'en-tête)
- ✅ Filtrage par état (running, stopped, all)
- ✅ Filtrage par région
- ✅ Recherche par nom ou ID
- ✅ Pagination (10, 25, 50 par page)
- ✅ Clic sur une ligne → Détails de l'instance

---

### **SECTION 4 : ALERTES / INSIGHTS**

#### **Alertes à afficher**
- ⚠️ **Instances sans IP publique** (potentiel problème d'accès)
- ⚠️ **CPU > 80%** (surcharge)
- ⚠️ **Instances sans tags "Name"** (mauvaise pratique)
- ⚠️ **Instances stopped depuis > 7 jours** (coût inutile)
- ⚠️ **Trafic réseau anormal** (> 1 GB/jour)

---

## 🎯 ÉLÉMENTS À GARDER DU DASHBOARD ACTUEL

### **À GARDER**
- ✅ **Scans This Month** - Pertinent pour suivre l'activité
- ✅ **By Provider** - Mais préciser "AWS" au lieu de multi-cloud

### **À SUPPRIMER / MODIFIER**
- ❌ **Monthly Cost** - On ne récupère pas cette donnée (pour l'instant)
- ❌ **Active Alerts** - On n'a pas de système d'alertes (pour l'instant)
- ❌ **Security Issues** - On ne fait pas de scan de sécurité (pour l'instant)
- ❌ **Recent Critical Alerts** - Idem

---

## 📐 STRUCTURE PROPOSÉE DU DASHBOARD EC2

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER : CloudDiagnoze - Dashboard EC2                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Total        │ Régions      │ CPU Moyen    │ Trafic       │
│ Instances    │ Actives      │ Global       │ Réseau       │
│              │              │              │              │
│ 5            │ 2            │ 42.5%        │ 1.2 GB       │
│ 3 running    │ eu-west-3    │ +5.2%        │ 800MB IN     │
└──────────────┴──────────────┴──────────────┴──────────────┘

┌─────────────────────────┬─────────────────────────────────────┐
│ Répartition par Type    │ CPU par Instance                    │
│                         │                                     │
│ [Donut Chart]           │ [Bar Chart Horizontal]              │
│                         │                                     │
│ t3.micro : 60%          │ i-031d... : ████████ 55%            │
│ t2.small : 40%          │ i-0bf7... : ██████ 32%              │
└─────────────────────────┴─────────────────────────────────────┘

┌─────────────────────────┬─────────────────────────────────────┐
│ Répartition par État    │ Trafic Réseau par Instance          │
│                         │                                     │
│ [Bar Chart]             │ [Stacked Bar Chart]                 │
│                         │                                     │
│ Running : 3             │ i-031d... : ████ IN ████ OUT        │
│ Stopped : 2             │ i-0bf7... : █ IN █ OUT              │
└─────────────────────────┴─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ TABLEAU DES INSTANCES                                           │
│                                                                 │
│ [Filtres: État | Région | Recherche]                           │
│                                                                 │
│ Name          | ID        | Type    | État    | Région | CPU  │
│ ─────────────────────────────────────────────────────────────  │
│ EC2-0         | i-0bf7... | t3.micro| running | eu-w-3 | 32%  │
│ EC2-1         | i-031d... | t3.micro| running | eu-w-3 | 55%  │
│ ...                                                             │
│                                                                 │
│ [Pagination: 1 2 3 ... 10]                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ALERTES / INSIGHTS                                              │
│                                                                 │
│ ⚠️ 2 instances sans IP publique                                │
│ ⚠️ 1 instance avec CPU > 80%                                   │
│ ⚠️ 3 instances sans tag "Name"                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ❓ QUESTIONS POUR TOI

1. **Cette structure te convient ?**
2. **Quels éléments veux-tu garder/modifier/supprimer ?**
3. **Veux-tu qu'on commence par coder cette version EC2 ?**
4. **Après EC2, on fera la même chose pour S3 ?**

---

## 🚀 PROCHAINES ÉTAPES

1. ✅ Valider la structure du dashboard EC2
2. ⏭️ Créer les nouvelles fonctions JavaScript pour récupérer ces données
3. ⏭️ Modifier le HTML pour afficher ces éléments
4. ⏭️ Tester avec tes vraies données
5. ⏭️ Passer à S3 une fois EC2 terminé

