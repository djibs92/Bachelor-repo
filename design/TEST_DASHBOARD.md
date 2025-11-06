# 🧪 TEST DU DASHBOARD

## ✅ ÉTAPES POUR TESTER

### 1. **Ouvrir le Dashboard**
- Ouvre `design/dashbord.html` dans ton navigateur
- Le fichier devrait déjà être ouvert automatiquement

### 2. **Ouvrir la Console du Navigateur**
- **Chrome/Edge** : `Cmd + Option + J` (Mac) ou `F12` (Windows)
- **Firefox** : `Cmd + Option + K` (Mac) ou `F12` (Windows)
- **Safari** : `Cmd + Option + C` (Mac)

### 3. **Vérifier les Logs**
Tu devrais voir dans la console :
```
🚀 Initialisation du dashboard...
📊 Statistiques récupérées: {totalResources: 5, scansThisMonth: 1, ...}
✅ Cartes de stats mises à jour
✅ Graphique CPU mis à jour
✅ Distribution des ressources mise à jour
✅ Dashboard chargé avec succès
```

### 4. **Vérifier les Données Affichées**
Le dashboard devrait afficher :
- **Total Resources** : `5` (tes 5 instances EC2)
- **Scans This Month** : `1` ou plus (selon tes scans)
- **Active Alerts** : `0` (pas encore implémenté)
- **Monthly Cost** : `$0` (pas encore implémenté)
- **CPU Utilization** : La moyenne de tes instances (ex: `0.55%`)
- **Resource Distribution** : AWS 100%, GCP 0%, Azure 0%

---

## ❌ SI TU AS DES ERREURS

### **Erreur CORS**
Si tu vois :
```
Access to fetch at 'http://localhost:8000/api/v1/scans/history' from origin 'null' has been blocked by CORS policy
```

**Solution :**
1. Arrête le serveur uvicorn
2. Installe `fastapi-cors` :
   ```bash
   cd CloudiagnozeApp
   pip3 install fastapi-cors
   ```
3. Modifie `main.py` pour ajouter CORS
4. Relance le serveur

---

### **Erreur 404 sur les scripts JS**
Si tu vois :
```
GET file:///Users/.../design/js/config.js net::ERR_FILE_NOT_FOUND
```

**Solution :**
Les fichiers JS sont bien créés. Vérifie que tu ouvres le fichier HTML depuis le bon chemin.

---

### **Pas de données affichées**
Si les stats restent à `0` :

1. **Vérifie que le serveur tourne** :
   ```bash
   curl http://localhost:8000/api/v1/ec2/instances
   ```

2. **Vérifie la console du navigateur** pour voir les erreurs

3. **Vérifie que tu as des données en BDD** :
   ```bash
   curl http://localhost:8000/api/v1/scans/history
   ```

---

## 🎯 TESTS MANUELS DANS LA CONSOLE

Tu peux tester manuellement dans la console du navigateur :

```javascript
// Test 1 : Vérifier que l'API est accessible
api.getScansHistory().then(data => console.log('Scans:', data));

// Test 2 : Vérifier les instances EC2
api.getEC2Instances().then(data => console.log('EC2:', data));

// Test 3 : Vérifier les stats
api.getDashboardStats().then(stats => console.log('Stats:', stats));

// Test 4 : Rafraîchir le dashboard
dashboard.refresh();
```

---

## 📊 RÉSULTAT ATTENDU

Après le chargement, tu devrais voir :
- ✅ Un loader qui apparaît puis disparaît
- ✅ Les stats mises à jour avec tes vraies données
- ✅ Le CPU moyen calculé
- ✅ La distribution AWS à 100%
- ✅ Pas d'erreurs dans la console

---

## 🔄 AUTO-REFRESH

Le dashboard se rafraîchit automatiquement toutes les **30 secondes**.
Tu peux voir les logs dans la console :
```
🔄 Rafraîchissement du dashboard...
```

---

## 🚀 PROCHAINES ÉTAPES

Si tout fonctionne :
1. ✅ Dashboard connecté au backend
2. ⏭️ Passer à la page "Config Scan"
3. ⏭️ Puis "Rapport de Scan"
4. ⏭️ Enfin "Login/Inscription"

