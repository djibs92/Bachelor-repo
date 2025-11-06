# ✅ ÉTAPE 2 TERMINÉE : UTILITAIRES DE SÉCURITÉ

## 📋 CE QUI A ÉTÉ FAIT

### **1. Dépendances installées**
**Fichier :** `CloudiagnozeApp/requirements.txt`

**Packages ajoutés :**
- `bcrypt==4.1.2` - Hashing de mots de passe
- `python-jose[cryptography]==3.3.0` - Génération et vérification de tokens JWT
- `passlib[bcrypt]==1.7.4` - Gestion des mots de passe

### **2. Module de sécurité créé**
**Fichier :** `CloudiagnozeApp/api/utils/security.py`

**Fonctions disponibles :**

#### **Hashing de mot de passe**
- `hash_password(password: str) -> str` - Hash un mot de passe avec bcrypt
- `verify_password(plain_password: str, hashed_password: str) -> bool` - Vérifie un mot de passe

#### **JWT (JSON Web Token)**
- `create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str` - Crée un token JWT
- `verify_token(token: str) -> Optional[dict]` - Vérifie et décode un token JWT
- `get_user_from_token(token: str) -> Optional[dict]` - Extrait les infos utilisateur d'un token

#### **Réinitialisation de mot de passe**
- `generate_reset_token() -> str` - Génère un token de réinitialisation sécurisé
- `create_reset_token_expiry(hours: int = 24) -> datetime` - Crée une date d'expiration
- `is_reset_token_valid(expiry: datetime) -> bool` - Vérifie si un token est encore valide

#### **Validation**
- `validate_password_strength(password: str) -> tuple[bool, str]` - Valide la force d'un mot de passe
- `validate_email(email: str) -> bool` - Valide le format d'un email

### **3. Export du module**
**Fichier :** `CloudiagnozeApp/api/utils/__init__.py`

Toutes les fonctions sont exportées et peuvent être importées facilement :
```python
from api.utils import hash_password, verify_password, create_access_token
```

---

## 🧪 TESTS EFFECTUÉS

### **Test 1 : Hashing de mot de passe**
```
Password: MyPassword123
Hashed: $2b$12$O6TvHtPTsv342fYrA9Dm7OTPkk/mEaN1cldeSmmQX1ZezCM5kKdKC
Verify correct: True
Verify wrong: False
```
✅ **Résultat :** Le hashing et la vérification fonctionnent correctement

### **Test 2 : JWT**
```
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Payload: {'sub': 'john@acme.com', 'user_id': 1, 'exp': 1762877781}
User info: {'email': 'john@acme.com', 'user_id': 1}
```
✅ **Résultat :** La génération et la vérification de tokens JWT fonctionnent

### **Test 3 : Token de réinitialisation**
```
Reset token: AqGJ6ryZzkMVJkUSkO3Nnc5i2Q6xmUnt2dNgSfh69Xk
Expiry: 2025-11-05 16:16:21.645337
Is valid: True
```
✅ **Résultat :** La génération de tokens de réinitialisation fonctionne

### **Test 4 : Validation**
```
Password 'weak': (False, 'Le mot de passe doit contenir au moins 8 caractères')
Password 'StrongPass123': (True, '')
Email 'john@acme.com': True
Email 'invalid': False
```
✅ **Résultat :** Les validations fonctionnent correctement

---

## 📚 EXEMPLES D'UTILISATION

### **Exemple 1 : Créer un utilisateur avec mot de passe hashé**
```python
from api.utils import hash_password
from api.database import get_db, User

# Hasher le mot de passe
password_hash = hash_password("MyPassword123")

# Créer l'utilisateur
db = next(get_db())
new_user = User(
    email="john@acme.com",
    password_hash=password_hash,
    full_name="John Doe",
    company_name="ACME Corp"
)
db.add(new_user)
db.commit()
```

### **Exemple 2 : Vérifier un mot de passe lors de la connexion**
```python
from api.utils import verify_password
from api.database import get_db, User

db = next(get_db())
user = db.query(User).filter(User.email == "john@acme.com").first()

if user and verify_password("MyPassword123", user.password_hash):
    print("✅ Mot de passe correct")
else:
    print("❌ Mot de passe incorrect")
```

### **Exemple 3 : Créer un token JWT après connexion**
```python
from api.utils import create_access_token

# Créer un token pour l'utilisateur
token = create_access_token({
    "sub": user.email,
    "user_id": user.id
})

# Retourner le token au frontend
return {"access_token": token, "token_type": "bearer"}
```

### **Exemple 4 : Vérifier un token JWT**
```python
from api.utils import verify_token, get_user_from_token

# Récupérer le token depuis le header Authorization
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Vérifier le token
payload = verify_token(token)
if payload:
    print(f"✅ Token valide pour {payload['sub']}")
else:
    print("❌ Token invalide")

# Ou extraire directement les infos utilisateur
user_info = get_user_from_token(token)
if user_info:
    print(f"User ID: {user_info['user_id']}")
    print(f"Email: {user_info['email']}")
```

### **Exemple 5 : Réinitialisation de mot de passe**
```python
from api.utils import generate_reset_token, create_reset_token_expiry, is_reset_token_valid
from api.database import get_db, User

db = next(get_db())
user = db.query(User).filter(User.email == "john@acme.com").first()

# Générer un token de réinitialisation
reset_token = generate_reset_token()
reset_expiry = create_reset_token_expiry(24)  # Valide 24h

# Stocker dans la base de données
user.reset_token = reset_token
user.reset_token_expiry = reset_expiry
db.commit()

# Envoyer le token par email (à implémenter)
# send_email(user.email, f"Reset link: https://clouddiagnoze.com/reset?token={reset_token}")

# Plus tard, quand l'utilisateur clique sur le lien...
if is_reset_token_valid(user.reset_token_expiry):
    # Permettre la réinitialisation
    new_password_hash = hash_password("NewPassword123")
    user.password_hash = new_password_hash
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()
else:
    print("❌ Token expiré")
```

### **Exemple 6 : Validation avant inscription**
```python
from api.utils import validate_email, validate_password_strength

email = "john@acme.com"
password = "MyPassword123"

# Valider l'email
if not validate_email(email):
    return {"error": "Email invalide"}

# Valider le mot de passe
is_valid, error_message = validate_password_strength(password)
if not is_valid:
    return {"error": error_message}

# Si tout est OK, créer l'utilisateur
# ...
```

---

## ⚙️ CONFIGURATION

### **Secret Key JWT**
**Fichier :** `CloudiagnozeApp/api/utils/security.py` (ligne 24)

```python
SECRET_KEY = "clouddiagnoze-secret-key-change-this-in-production-2024"
```

⚠️ **IMPORTANT :** En production, cette clé doit être :
1. **Forte et aléatoire** (au moins 32 caractères)
2. **Stockée dans les variables d'environnement** (pas dans le code)
3. **Gardée secrète** (ne jamais la commiter dans Git)

**Recommandation :**
```python
import os
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-key-for-dev")
```

### **Durée de validité du token**
**Fichier :** `CloudiagnozeApp/api/utils/security.py` (ligne 26)

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 jours
```

Tu peux ajuster cette valeur selon tes besoins :
- `60 * 24` = 1 jour
- `60 * 24 * 7` = 7 jours
- `60 * 24 * 30` = 30 jours

---

## 🔒 RÈGLES DE VALIDATION DU MOT DE PASSE

La fonction `validate_password_strength()` vérifie que le mot de passe :
- ✅ Contient au moins **8 caractères**
- ✅ Contient au moins **une lettre majuscule**
- ✅ Contient au moins **une lettre minuscule**
- ✅ Contient au moins **un chiffre**

**Exemples :**
- ❌ `"weak"` - Trop court
- ❌ `"weakpassword"` - Pas de majuscule ni de chiffre
- ❌ `"WEAKPASSWORD"` - Pas de minuscule ni de chiffre
- ❌ `"WeakPassword"` - Pas de chiffre
- ✅ `"StrongPass123"` - Valide !

---

## 🎯 PROCHAINE ÉTAPE

**Étape 3 : Créer les endpoints d'authentification**
- `POST /api/v1/auth/signup` - Inscription
- `POST /api/v1/auth/login` - Connexion
- `GET /api/v1/auth/me` - Récupérer les infos de l'utilisateur connecté
- `POST /api/v1/auth/forgot-password` - Mot de passe oublié
- `POST /api/v1/auth/reset-password` - Réinitialiser le mot de passe

**Fichier à créer :** `CloudiagnozeApp/api/endpoints/auth.py`

---

**Étape 2 terminée avec succès !** 🎉

