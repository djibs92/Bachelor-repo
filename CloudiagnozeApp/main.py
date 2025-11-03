from fastapi import FastAPI
from api.endpoints.scan import router as scan_router
from api.endpoints.events import router as events_router
import uvicorn

app = FastAPI(
    title="CloudDiagnoze API",
    description="Scanner d'infrastructure cloud multi-dimensionnel",
    version="1.0.0"
)

# Inclusion du router scan
app.include_router(scan_router, prefix="/api/v1", tags=["scans"])
#Endpoint permettant le visuel des événements 
app.include_router(events_router,prefix="/api/v1",tags=["events"])
@app.get("/")
async def root():
    return {"message": "CloudDiagnoze API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    