from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints.scan import router as scan_router
from api.endpoints.events import router as events_router
from api.endpoints.auth import router as auth_router
import uvicorn

app = FastAPI(
    title="CloudDiagnoze API",
    description="Scanner d'infrastructure cloud multi-dimensionnel",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes depuis le front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, remplacer par les domaines autorisés
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    