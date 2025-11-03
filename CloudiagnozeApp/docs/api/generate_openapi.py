#!/usr/bin/env python3
"""
Générateur de documentation OpenAPI/ReDoc autonome
Fonctionne sans modifier le code métier
"""
import json
import sys
import os
from pathlib import Path

# Ajouter le projet au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
print(f"🔍 Project root: {project_root}")

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from openapi_config import OPENAPI_CONFIG, EXAMPLES, ENDPOINTS_DOC

def create_documentation_app():
    """Crée une app FastAPI dédiée à la documentation"""
    
    # Import des routers sans modification
    from api.endpoints.scan import router as scan_router
    from api.endpoints.events import router as events_router
    
    # App dédiée documentation
    doc_app = FastAPI(**OPENAPI_CONFIG)
    
    # Inclusion des routers SANS modification
    doc_app.include_router(scan_router, prefix="/api/v1", tags=["🚀 Scans"])
    doc_app.include_router(events_router, prefix="/api/v1", tags=["📊 Événements"])
    
    return doc_app

def generate_openapi_schema():
    """Génère le schéma OpenAPI enrichi"""
    
    app = create_documentation_app()
    
    # Générer le schéma de base
    openapi_schema = get_openapi(
        title=OPENAPI_CONFIG["title"],
        version=OPENAPI_CONFIG["version"],
        description=OPENAPI_CONFIG["description"],
        routes=app.routes,
    )
    
    # Enrichir avec nos exemples
    if "paths" in openapi_schema:
        for path, methods in openapi_schema["paths"].items():
            if path in ENDPOINTS_DOC:
                for method, config in ENDPOINTS_DOC[path].items():
                    if method in methods:
                        methods[method].update(config)
    
    # Ajouter les exemples
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["examples"] = EXAMPLES
    
    return openapi_schema

def generate_redoc_html(openapi_schema):
    """Génère le HTML ReDoc statique"""
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    </head>
    <body>
        <redoc spec-url="./openapi.json"></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    
    return html_template.format(title=OPENAPI_CONFIG["title"])

def main():
    """Génère toute la documentation"""
    
    # Créer les dossiers
    output_dir = Path(__file__).parent / "generated"
    output_dir.mkdir(exist_ok=True)
    
    # Générer OpenAPI
    print("🔄 Génération du schéma OpenAPI...")
    openapi_schema = generate_openapi_schema()
    
    # Sauvegarder OpenAPI JSON
    with open(output_dir / "openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("✅ openapi.json généré")
    
    # Générer ReDoc HTML
    print("🔄 Génération ReDoc HTML...")
    html_content = generate_redoc_html(openapi_schema)
    
    with open(output_dir / "redoc.html", "w") as f:
        f.write(html_content)
    print("✅ redoc.html généré")
    
    print(f"\n🎉 Documentation générée dans : {output_dir}")
    print(f"📖 Ouvrir : {output_dir}/redoc.html")

if __name__ == "__main__":
    main()
