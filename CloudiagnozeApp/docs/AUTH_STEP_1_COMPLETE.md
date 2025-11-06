# ✅ ÉTAPE 1 TERMINÉE : TABLE USERS ET MODÈLE ORM

## 📋 CE QUI A ÉTÉ FAIT

### **1. Modèle ORM `User` créé**
**Fichier :** `CloudiagnozeApp/api/database/models.py`

**Colonnes de la table `users` :**
- `id` - ID unique (auto-incrémenté)
- `email` - Email de l'utilisateur (unique, indexé)
- `password_hash` - Mot de passe hashé avec bcrypt
- `full_name` - Nom complet (optionnel)
- `company_name` - Nom de l'entreprise (optionnel)
- `role_arn` - Role ARN AWS (optionnel, peut être ajouté plus tard)
- `created_at` - Date de création du compte
- `last_login` - Date de dernière connexion
- `is_active` - Compte actif ou désactivé
- `reset_token` - Token pour réinitialisation du mot de passe
- `reset_token_expiry` - Date d'expiration du token

### **2. Script SQL de migration créé**
**Fichier :** `CloudiagnozeApp/api/database/migrations/create_users_table.sql`

Ce fichier contient le SQL pour créer la table manuellement si nécessaire.

### **3. Script Python pour créer la table**
**Fichier :** `CloudiagnozeApp/create_users_table.py`

Ce script utilise SQLAlchemy pour créer la table automatiquement.

**Exécution :**
```bash
cd CloudiagnozeApp
python3 create_users_table.py
```

**Résultat :**
```
✅ Table 'users' créée avec succès !
```

### **4. Export du modèle User**
**Fichier :** `CloudiagnozeApp/api/database/__init__.py`

Le modèle `User` est maintenant exporté et peut être importé facilement :
```python
from api.database import User
```

---

## 🗄️ STRUCTURE DE LA TABLE `users`

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    company_name VARCHAR(255),
    role_arn VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    reset_token VARCHAR(255),
    reset_token_expiry DATETIME,
    INDEX idx_email (email),
    INDEX idx_is_active (is_active)
);
```

---

## 📊 EXEMPLE D'UTILISATION DU MODÈLE

### **Créer un utilisateur**
```python
from api.database import get_db, User
from sqlalchemy.orm import Session

db: Session = next(get_db())

new_user = User(
    email="john@acme.com",
    password_hash="$2b$12$...",  # Hash bcrypt
    full_name="John Doe",
    company_name="ACME Corp",
    role_arn="arn:aws:iam::123456:role/MyRole",
    is_active=True
)

db.add(new_user)
db.commit()
db.refresh(new_user)

print(f"Utilisateur créé : {new_user.id}")
```

### **Rechercher un utilisateur par email**
```python
user = db.query(User).filter(User.email == "john@acme.com").first()

if user:
    print(f"Utilisateur trouvé : {user.full_name}")
else:
    print("Utilisateur non trouvé")
```

### **Mettre à jour le Role ARN**
```python
user = db.query(User).filter(User.email == "john@acme.com").first()

if user:
    user.role_arn = "arn:aws:iam::123456:role/NewRole"
    db.commit()
    print("Role ARN mis à jour")
```

### **Désactiver un utilisateur**
```python
user = db.query(User).filter(User.email == "john@acme.com").first()

if user:
    user.is_active = False
    db.commit()
    print("Utilisateur désactivé")
```

---

## ✅ VÉRIFICATION

Pour vérifier que la table a bien été créée, tu peux :

### **Option 1 : Via Python**
```python
from api.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

if 'users' in tables:
    print("✅ Table 'users' existe")
    columns = inspector.get_columns('users')
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
else:
    print("❌ Table 'users' n'existe pas")
```

### **Option 2 : Via Docker**
```bash
docker exec clouddiagnoze-db mariadb -uroot -p[PASSWORD] clouddiagnoze -e "DESCRIBE users;"
```

---

## 🎯 PROCHAINE ÉTAPE

**Étape 2 : Créer les utilitaires de sécurité**
- Fonctions pour hasher les mots de passe (bcrypt)
- Fonctions pour générer et vérifier les tokens JWT
- Fichier : `CloudiagnozeApp/api/utils/security.py`

---

**Étape 1 terminée avec succès !** 🎉

