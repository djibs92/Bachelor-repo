# 🔧 ENDPOINT D'ADMINISTRATION

## 📋 DESCRIPTION

Endpoint de suppression complète de la base de données, utile en développement.

---

## 🎯 ENDPOINT CRÉÉ

### **DELETE /api/v1/admin/clear-database**

Supprime **TOUTES** les données de la base de données (scans, instances EC2, buckets S3, performances).

---

## 📝 PARAMÈTRES

| Paramètre | Type | Obligatoire | Description |
|-----------|------|-------------|-------------|
| `confirm` | boolean | ✅ OUI | Doit être `true` pour confirmer la suppression |

---

## 🧪 EXEMPLES D'UTILISATION

### **1. Sans confirmation (ÉCHOUE) :**

```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/clear-database"
```

**Réponse (400 Bad Request) :**
```json
{
    "detail": "⚠️ Vous devez confirmer la suppression avec ?confirm=true"
}
```

---

### **2. Avec confirmation (RÉUSSIT) :**

```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/clear-database?confirm=true"
```

**Réponse (200 OK) :**
```json
{
    "status": "success",
    "message": "✅ Base de données vidée avec succès",
    "deleted": {
        "scan_runs": 4,
        "ec2_instances": 11,
        "ec2_performance": 11,
        "s3_buckets": 1,
        "s3_performance": 1,
        "total": 28
    }
}
```

---

## ⚙️ FONCTIONNEMENT INTERNE

L'endpoint supprime les données dans l'ordre suivant (pour respecter les foreign keys) :

1. **EC2Performance** (table enfant)
2. **S3Performance** (table enfant)
3. **EC2Instance** (table parent)
4. **S3Bucket** (table parent)
5. **ScanRun** (table racine)

Si une erreur survient, un **rollback** est effectué (aucune donnée n'est supprimée).

---

## ⚠️ AVERTISSEMENTS

### **DANGER : Suppression irréversible**
- ⚠️ Cette action est **IRRÉVERSIBLE**
- ⚠️ Toutes les données historiques seront perdues
- ⚠️ Utiliser uniquement en **développement**

### **Protection**
- ✅ Nécessite une confirmation explicite (`?confirm=true`)
- ✅ Rollback automatique en cas d'erreur
- ✅ Retourne le nombre d'éléments supprimés

---

## 📊 CAS D'USAGE

### **Quand utiliser cet endpoint ?**

✅ **OUI :**
- En développement pour repartir de zéro
- Avant une démo pour nettoyer les données de test
- Après un changement de schéma de BDD
- Pour supprimer des scans de test erronés

❌ **NON :**
- En production (perte de données)
- Sans sauvegarde préalable
- Si tu veux garder l'historique

---

## 🔄 WORKFLOW TYPIQUE

```bash
# 1. Vérifier combien de scans on a
curl "http://localhost:8000/api/v1/scans/history?limit=100"

# 2. Vider la BDD
curl -X DELETE "http://localhost:8000/api/v1/admin/clear-database?confirm=true"

# 3. Vérifier que c'est vide
curl "http://localhost:8000/api/v1/scans/history?limit=100"
# Résultat : {"total_scans": 0, "scans": []}

# 4. Relancer un scan
curl -X POST "http://localhost:8000/api/v1/scans" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aws",
    "services": ["ec2"],
    "regions": ["eu-west-3"],
    "client_id": "ASM-Enterprise",
    "auth": {
      "type": "sts",
      "role_arn": "arn:aws:iam::680164043810:role/Cloudignoze-arn-test-1"
    }
  }'
```

---

## 📁 FICHIER MODIFIÉ

- ✅ `CloudiagnozeApp/api/endpoints/events.py` : Ajout de l'endpoint `DELETE /admin/clear-database`

---

## 🧪 TESTS RÉUSSIS

### **Test 1 : Sans confirmation**
```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/clear-database"
```
✅ Retourne une erreur 400 avec message de confirmation

### **Test 2 : Avec confirmation**
```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/clear-database?confirm=true"
```
✅ Supprime 28 entrées (4 scans, 11 instances EC2, 1 bucket S3)

### **Test 3 : Vérification**
```bash
curl "http://localhost:8000/api/v1/scans/history?limit=100"
```
✅ Retourne `{"total_scans": 0, "scans": []}`

---

## 💡 AMÉLIORATIONS FUTURES (optionnel)

Si tu veux améliorer cet endpoint plus tard, tu peux ajouter :

1. **Suppression sélective :**
   ```bash
   DELETE /admin/clear-database?confirm=true&client_id=TEST-CLIENT
   # Supprime uniquement les scans d'un client
   ```

2. **Suppression par date :**
   ```bash
   DELETE /admin/clear-database?confirm=true&older_than_days=30
   # Supprime les scans de plus de 30 jours
   ```

3. **Garder les N derniers scans :**
   ```bash
   DELETE /admin/clear-database?confirm=true&keep_last=100
   # Garde uniquement les 100 derniers scans
   ```

Mais pour l'instant, la suppression complète est suffisante pour ton projet de Bachelor ! 🎓

---

## ✅ CONCLUSION

L'endpoint d'administration est **opérationnel** et **sécurisé** :

- ✅ Suppression complète de la BDD
- ✅ Protection par confirmation obligatoire
- ✅ Rollback automatique en cas d'erreur
- ✅ Statistiques de suppression détaillées
- ✅ Testé et fonctionnel

**Tu peux maintenant nettoyer ta BDD facilement pendant le développement !** 🚀

