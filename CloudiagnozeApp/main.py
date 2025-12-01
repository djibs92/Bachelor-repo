from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from api.endpoints.scan import router as scan_router
from api.endpoints.events import router as events_router
from api.endpoints.auth import router as auth_router
import uvicorn
from loguru import logger

app = FastAPI(
    title="CloudDiagnoze API",
    description="Scanner d'infrastructure cloud multi-dimensionnel",
    version="1.0.0",
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

# Inclusion des routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(scan_router, prefix="/api/v1", tags=["scans"])
app.include_router(events_router, prefix="/api/v1", tags=["events"])


@app.get("/")
async def root():
    return {"message": "CloudDiagnoze API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Configuration pour servir les fichiers statiques (HTML, CSS, JS)
# Cela permet d'accéder à http://localhost:8000/login.html
try:
    # On remonte de 'CloudiagnozeApp/main.py' vers la racine du projet pour trouver 'design'
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    design_path = os.path.join(base_path, "design")

    # On monte le dossier design à la racine "/"
    # html=True permet de servir index.html si on accède à /
    app.mount("/", StaticFiles(directory=design_path, html=True), name="static")
except Exception as e:
    print(f"Erreur lors du montage des fichiers statiques: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
