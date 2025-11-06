# 🐛 GUIDE DE DÉBOGAGE - DASHBOARD GLOBAL

## 🔍 PROBLÈMES IDENTIFIÉS

### **Problème 1 : Les modals ne s'ouvrent pas**
**Symptôme :** On voit "Cliquez pour voir les détails" mais rien ne se passe au clic

**Causes possibles :**
1. Event listeners pas attachés
2. Éléments DOM pas trouvés
3. Erreur JavaScript qui bloque l'exécution

### **Problème 2 : Les graphiques sont vides**
**Symptôme :** Les graphiques EC2 et S3 par région ne montrent rien

**Causes possibles :**
1. Données pas chargées
2. API ne retourne rien
3. Données mal formatées

---

## 🧪 ÉTAPES DE DÉBOGAGE

### **Étape 1 : Vérifier que le backend tourne**

```bash
# Terminal 1 : Lancer le backend
cd CloudiagnozeApp
python3 -m uvicorn main:app --reload --port 8000
```

**Résultat attendu :**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### **Étape 2 : Tester l'API manuellement**

```bash
# Tester EC2
curl http://localhost:8000/api/v1/ec2/instances?latest_only=true

# Tester S3
curl http://localhost:8000/api/v1/s3/buckets?latest_only=true

# Tester Scans
curl http://localhost:8000/api/v1/scans/history
```

**Résultat attendu :**
- EC2 : `{"total_instances": 5, "instances": [...]}`
- S3 : `{"total_buckets": 5, "buckets": [...]}`
- Scans : `{"total_scans": X, "scans": [...]}`

### **Étape 3 : Ouvrir la console du navigateur**

1. Ouvrir `design/dashbord.html` dans le navigateur
2. Appuyer sur `F12` ou `Cmd+Option+I` (Mac)
3. Aller dans l'onglet **Console**

**Ce que tu devrais voir :**
```
🔄 Chargement des données...
📦 EC2 instances: Array(5)
📦 S3 buckets: Array(5)
📦 Scan runs: Array(X)
✅ Données chargées: 5 EC2, 5 S3, X scans
🔧 Configuration des event listeners...
Total Resources Card: div.flex.flex-col...
Active Alerts Card: div.flex.flex-col...
Scans Card: div.flex.flex-col...
Security Card: div.flex.flex-col...
📊 Données EC2 par région: {labels: Array(1), data: Array(1)}
📊 Données S3 par région: {labels: Array(1), data: Array(1)}
```

**Si tu vois des erreurs :**
- `❌ Canvas chart-ec2-regions non trouvé` → Problème HTML
- `❌ Erreur chargement données` → Problème API
- `CORS error` → Problème CORS (backend pas lancé)

### **Étape 4 : Tester les event listeners**

1. Ouvrir la console
2. Taper :
```javascript
document.querySelector('[data-modal="resources"]')
```

**Résultat attendu :**
```html
<div class="flex flex-col gap-2 rounded-xl glass-card p-6..." data-modal="resources">
```

**Si `null` :**
- L'élément n'existe pas dans le HTML
- Vérifier que `dashbord.html` a bien les attributs `data-modal`

### **Étape 5 : Tester manuellement un modal**

Dans la console, taper :
```javascript
dashboardGlobal.showResourcesModal()
```

**Résultat attendu :**
- Le modal s'ouvre
- Le tableau est rempli avec les ressources

**Si erreur :**
- Regarder le message d'erreur dans la console
- Vérifier que `globalStats` a bien des données

### **Étape 6 : Utiliser la page de test**

1. Ouvrir `design/test-dashboard.html`
2. Cliquer sur "Tester l'API"
3. Cliquer sur "Tester GlobalStats"
4. Cliquer sur l'élément de test

**Résultats attendus :**
- API : JSON avec les données EC2, S3, Scans
- GlobalStats : JSON avec les distributions par région
- Event Listener : Message "✅ Event listener fonctionne !"

---

## 🔧 SOLUTIONS AUX PROBLÈMES COURANTS

### **Solution 1 : Backend pas lancé**

**Symptôme :** `CORS error` ou `Failed to fetch`

**Solution :**
```bash
cd CloudiagnozeApp
python3 -m uvicorn main:app --reload --port 8000
```

### **Solution 2 : Pas de données dans la BDD**

**Symptôme :** `total_instances: 0`, `total_buckets: 0`

**Solution :**
```bash
# Lancer un scan EC2
curl -X POST http://localhost:8000/api/v1/scan/ec2

# Lancer un scan S3
curl -X POST http://localhost:8000/api/v1/scan/s3
```

### **Solution 3 : Event listeners pas attachés**

**Symptôme :** Rien ne se passe au clic

**Solution :**
Vérifier dans `dashbord.html` que les cards ont bien `data-modal` :
```html
<div ... data-modal="resources">
<div ... data-modal="alerts">
<div ... data-modal="scans">
<div ... data-modal="security">
```

### **Solution 4 : Graphiques vides**

**Symptôme :** Les canvas sont là mais vides

**Causes possibles :**
1. Données pas chargées → Vérifier console
2. Labels vides → Vérifier `getEC2RegionDistribution()`
3. Chart.js pas chargé → Vérifier `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>`

**Solution :**
Dans la console :
```javascript
globalStats.getEC2RegionDistribution()
// Devrait retourner : {labels: ["eu-west-3"], data: [5]}

globalStats.getS3RegionDistribution()
// Devrait retourner : {labels: ["eu-west-3"], data: [5]}
```

---

## 📋 CHECKLIST DE VÉRIFICATION

### **Backend :**
- [ ] Backend lancé (`python3 -m uvicorn main:app --reload --port 8000`)
- [ ] API répond (`curl http://localhost:8000/api/v1/ec2/instances?latest_only=true`)
- [ ] Données présentes dans la BDD (total_instances > 0)

### **Front-end :**
- [ ] `dashbord.html` ouvert dans le navigateur
- [ ] Console ouverte (F12)
- [ ] Pas d'erreurs CORS
- [ ] Données chargées (voir console logs)

### **HTML :**
- [ ] Attributs `data-modal` présents sur les 4 cards
- [ ] Canvas `chart-ec2-regions` existe
- [ ] Canvas `chart-s3-regions` existe
- [ ] Canvas `chart-resource-distribution` existe
- [ ] 4 modals présents (`modal-resources`, `modal-alerts`, `modal-scans`, `modal-security`)

### **JavaScript :**
- [ ] `config.js` chargé
- [ ] `api.js` chargé
- [ ] `global-stats.js` chargé
- [ ] `dashboard-global.js` chargé
- [ ] Chart.js chargé
- [ ] `globalStats` défini (taper `globalStats` dans la console)
- [ ] `dashboardGlobal` défini (taper `dashboardGlobal` dans la console)

---

## 🎯 COMMANDES UTILES DANS LA CONSOLE

```javascript
// Vérifier que globalStats existe
globalStats

// Vérifier les données chargées
globalStats.ec2Instances
globalStats.s3Buckets
globalStats.scanRuns

// Vérifier les distributions
globalStats.getEC2RegionDistribution()
globalStats.getS3RegionDistribution()

// Vérifier les ressources
globalStats.getAllResourcesList()

// Tester un modal manuellement
dashboardGlobal.showResourcesModal()
dashboardGlobal.showAlertsModal()
dashboardGlobal.showScansModal()
dashboardGlobal.showSecurityModal()

// Fermer un modal
dashboardGlobal.closeModal('modal-resources')

// Vérifier les event listeners
document.querySelector('[data-modal="resources"]')
```

---

## 📞 SI RIEN NE FONCTIONNE

1. **Rafraîchir la page** (Cmd+R ou F5)
2. **Vider le cache** (Cmd+Shift+R ou Ctrl+Shift+R)
3. **Relancer le backend**
4. **Vérifier que la BDD a des données** (lancer des scans)
5. **Regarder les erreurs dans la console**
6. **Utiliser `test-dashboard.html` pour isoler le problème**

---

## 🚀 PROCHAINES ÉTAPES

Une fois que tout fonctionne :
1. Tester chaque modal
2. Vérifier les graphiques
3. Vérifier les couleurs dynamiques
4. Passer à la **Configuration Scan** !

