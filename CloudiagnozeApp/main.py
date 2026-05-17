from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
import os
from api.endpoints.scan import router as scan_router
from api.endpoints.scans import router as scans_router
from api.endpoints.admin import router as admin_router
from api.endpoints.aws.ec2 import router as ec2_router
from api.endpoints.aws.s3 import router as s3_router
from api.endpoints.auth import router as auth_router
import uvicorn
from loguru import logger

# ========================================
# MÉTADONNÉES OPENAPI - TAGS
# ========================================
tags_metadata = [
    {
        "name": "🔐 Authentication",
        "description": "Gestion des comptes utilisateurs, authentification JWT et profil utilisateur.",
        "externalDocs": {
            "description": "En savoir plus sur JWT",
            "url": "https://jwt.io/introduction"
        }
    },
    {
        "name": "🔍 Scans",
        "description": "Lancement et suivi des scans d'infrastructure AWS. Supporte EC2 et S3.",
    },
    {
        "name": "💻 EC2",
        "description": "Récupération des instances EC2, leurs configurations et métriques de performance.",
    },
    {
        "name": "🪣 S3",
        "description": "Récupération des buckets S3, configurations de sécurité et métriques.",
    },
    {
        "name": "⚙️ Admin",
        "description": "Endpoints d'administration pour le nettoyage des données et le debug.",
    },
]

# ========================================
# APPLICATION FASTAPI
# ========================================
app = FastAPI(
    title="CloudDiagnoze API",
    description="""
## 🔍 CloudDiagnoze - Scanner d'Infrastructure Cloud AWS

**CloudDiagnoze** est une plateforme SaaS qui analyse automatiquement votre infrastructure AWS
pour inventorier vos ressources, détecter les problèmes de sécurité et optimiser vos coûts.

---

### 🎯 Fonctionnalités principales

| Fonctionnalité | Description |
|----------------|-------------|
| **Scan multi-services** | EC2, S3 en un seul appel |
| **Multi-régions** | Scannez plusieurs régions AWS simultanément |
| **Authentification sécurisée** | JWT + AWS STS AssumeRole |
| **Isolation des données** | Chaque utilisateur voit uniquement ses propres scans |
| **Historique complet** | Conservez l'historique de tous vos scans |

---

### 🔐 Authentification

Toutes les routes (sauf `/auth/signup` et `/auth/login`) nécessitent un **token JWT** dans le header :

```
Authorization: Bearer <votre_token_jwt>
```

**Obtenir un token :**
1. Créez un compte via `POST /api/v1/auth/signup`
2. Connectez-vous via `POST /api/v1/auth/login`
3. Utilisez le `access_token` retourné

---

### 🚀 Flux de scan typique

1. **Authentification** → `POST /auth/login`
2. **Configuration** → `PATCH /auth/me` (ajouter le Role ARN)
3. **Lancement du scan** → `POST /scans`
4. **Récupération des résultats** → `GET /ec2/instances`, `GET /s3/buckets`, etc.

---

### 📊 Services AWS supportés

- **EC2** : Instances, types, états, IPs, security groups
- **S3** : Buckets, configurations de sécurité, versioning

    """,
    version="1.0.0",
    contact={
        "name": "Gebril Kadid",
        "email": "gebril.kadid@spitzkop.io",
        "url": "https://github.com/djibs92/Bachelor-repo"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ✅ SÉCURITÉ : Configuration CORS depuis les variables d'environnement
# Lecture des origines autorisées depuis .env (séparées par des virgules)
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

logger.info(f"🔒 CORS configuré pour les origines : {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # ✅ Origines spécifiques depuis .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers avec les tags appropriés
app.include_router(auth_router, prefix="/api/v1/auth", tags=["🔐 Authentication"])
app.include_router(scan_router, prefix="/api/v1", tags=["🔍 Scans"])
app.include_router(scans_router, prefix="/api/v1")
app.include_router(ec2_router, prefix="/api/v1")
app.include_router(s3_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "CloudDiagnoze API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Configuration pour servir les fichiers statiques (HTML, CSS, JS)
# ⚠️ IMPORTANT : Monter APRÈS les routes API pour ne pas interférer avec /docs et /redoc
try:
    # On remonte de 'CloudiagnozeApp/main.py' vers la racine du projet pour trouver 'design'
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    design_path = os.path.join(base_path, "design")

    # On monte le dossier design sur /app pour éviter les conflits avec /docs et /redoc
    # Accès: http://localhost:8000/app/login.html ou http://localhost:8000/app/
    app.mount("/app", StaticFiles(directory=design_path, html=True), name="static")

    logger.info(f"📁 Fichiers statiques montés sur /app depuis: {design_path}")
except Exception as e:
    logger.warning(f"⚠️ Erreur lors du montage des fichiers statiques: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
