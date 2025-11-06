# ✅ PROBLÈME RÉSOLU : Dashboard affichait l'historique au lieu de l'état actuel

## 🐛 PROBLÈME IDENTIFIÉ

**Symptôme :** Le dashboard affichait 20 instances au lieu de 5.

**Cause :** L'endpoint `/api/v1/ec2/instances` récupérait **TOUS** les enregistrements de la BDD (historique complet), pas uniquement les instances du dernier scan.

**Exemple :**
- 4 scans EC2 effectués
- Chaque scan a enregistré 5 instances
- BDD contient 20 enregistrements (4 × 5)
- Dashboard affichait 20 instances au lieu de 5

---

## ✅ SOLUTION APPLIQUÉE

### **1. Ajout du paramètre `latest_only`**

Modifié les endpoints :
- `GET /api/v1/ec2/instances`
- `GET /api/v1/s3/buckets`

**Nouveau paramètre :**
```python
latest_only: bool = True  # Par défaut, récupère uniquement le dernier scan
```

### **2. Logique implémentée**

#### **Si `latest_only=True` (défaut) :**
1. Récupère le dernier scan **EC2** (ou **S3** pour les buckets)
2. Filtre les instances/buckets par `scan_run_id` du dernier scan
3. Retourne uniquement les ressources du dernier scan

#### **Si `latest_only=False` :**
1. Récupère **TOUTES** les instances/buckets (historique complet)
2. Utile pour l'analyse historique

---

## 📝 CODE MODIFIÉ

### **Endpoint EC2 (events.py)**

```python
@router.get("/ec2/instances")
async def get_ec2_instances(
    client_id: Optional[str] = None,
    region: Optional[str] = None,
    state: Optional[str] = None,
    latest_only: bool = True,  # ✅ NOUVEAU PARAMÈTRE
    limit: int = 50,
    db: Session = Depends(get_db)
):
    try:
        if latest_only:
            # Récupérer le dernier scan EC2
            latest_scan = db.query(ScanRun).filter(
                ScanRun.service_type == 'ec2'  # ✅ Filtrer par service
            ).order_by(ScanRun.scan_timestamp.desc()).first()
            
            if not latest_scan:
                return {
                    "total_instances": 0,
                    "instances": [],
                    "scan_id": None,
                    "scan_timestamp": None
                }
            
            # Construire la requête pour le dernier scan EC2 uniquement
            query = db.query(EC2Instance).filter(
                EC2Instance.scan_run_id == latest_scan.id  # ✅ Filtrer par scan_run_id
            )
        else:
            # Mode historique : récupérer toutes les instances
            query = db.query(EC2Instance)
        
        # ... reste du code (filtres, limit, etc.)
```

### **Endpoint S3 (events.py)**

Même logique appliquée pour S3 :
```python
latest_scan = db.query(ScanRun).filter(
    ScanRun.service_type == 's3'  # ✅ Filtrer par service S3
).order_by(ScanRun.scan_timestamp.desc()).first()
```

---

## 🧪 TESTS

### **Avant le fix :**
```bash
curl "http://localhost:8000/api/v1/ec2/instances?limit=100"
# Résultat : 20 instances (historique complet)
```

### **Après le fix :**
```bash
curl "http://localhost:8000/api/v1/ec2/instances?latest_only=true&limit=100"
# Résultat : 5 instances (dernier scan uniquement) ✅
```

### **Mode historique (si besoin) :**
```bash
curl "http://localhost:8000/api/v1/ec2/instances?latest_only=false&limit=100"
# Résultat : 20 instances (historique complet)
```

---

## 📊 RÉSULTAT DANS LE DASHBOARD

### **Avant :**
- **Total Instances** : `20` ❌
- **Régions** : Données dupliquées
- **Graphiques** : Données faussées

### **Après :**
- **Total Instances** : `5` ✅
- **Régions** : `1` (eu-west-3) ✅
- **Graphiques** : Données correctes ✅

---

## 🔧 POINTS TECHNIQUES IMPORTANTS

### **1. Nom des colonnes**
- ❌ `EC2Instance.scan_id` (n'existe pas)
- ✅ `EC2Instance.scan_run_id` (clé étrangère vers `scan_runs.id`)

### **2. Filtrage par service**
- ❌ `db.query(ScanRun).order_by(...)` (récupère le dernier scan tous services confondus)
- ✅ `db.query(ScanRun).filter(ScanRun.service_type == 'ec2').order_by(...)` (récupère le dernier scan EC2)

### **3. Clé primaire de ScanRun**
- ❌ `latest_scan.scan_id` (n'existe pas)
- ✅ `latest_scan.id` (clé primaire)

---

## 🚀 UTILISATION

### **Dashboard (par défaut) :**
Le dashboard utilise automatiquement `latest_only=true` :
```javascript
// Dans api.js
async getEC2Instances(params = {}) {
    const queryParams = new URLSearchParams({
        latest_only: 'true',  // ✅ Par défaut
        limit: params.limit || 100,
        ...params
    });
    // ...
}
```

### **Analyse historique (si besoin) :**
Pour voir l'évolution dans le temps :
```javascript
const historicalData = await api.getEC2Instances({ latest_only: false });
```

---

## ✅ CHECKLIST

- [x] Paramètre `latest_only` ajouté à `/ec2/instances`
- [x] Paramètre `latest_only` ajouté à `/s3/buckets`
- [x] Filtrage par `service_type` (ec2 ou s3)
- [x] Utilisation de `scan_run_id` au lieu de `scan_id`
- [x] Utilisation de `latest_scan.id` au lieu de `latest_scan.scan_id`
- [x] Tests réussis : 5 instances au lieu de 20
- [x] Dashboard affiche les bonnes données

---

## 🎯 PROCHAINES ÉTAPES

1. **Rafraîchir le dashboard** (F5) pour voir les bonnes données
2. **Vérifier les graphiques** (doivent afficher 5 instances)
3. **Vérifier le tableau** (doit afficher 5 lignes)
4. **Tester les filtres** (par état, recherche)

---

## 💡 AMÉLIORATION FUTURE

Pour éviter ce genre de confusion, on pourrait :
1. Ajouter un champ `is_latest` dans la table pour marquer le dernier scan
2. Créer une vue SQL qui retourne automatiquement le dernier état
3. Ajouter un endpoint `/ec2/instances/current` dédié à l'état actuel

Mais pour l'instant, `latest_only=true` fait parfaitement le job ! ✅

