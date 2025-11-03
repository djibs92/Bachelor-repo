"""
Configuration OpenAPI séparée du code métier
"""

OPENAPI_CONFIG = {
    "title": "CloudDiagnoze API",
    "version": "1.0.0",
    "description": """
    ## 🌩️ Scanner d'infrastructure cloud multi-dimensionnel
    
    CloudDiagnoze analyse votre infrastructure cloud sous toutes ses dimensions.
    
    ### 🎯 Fonctionnalités
    - **Multi-provider** : AWS (GCP, Azure en développement)
    - **Événements 2CBP** : Format standardisé
    - **Scan asynchrone** : Réponse immédiate + traitement background
    """,
    "contact": {
        "name": "CloudDiagnoze Team",
        "email": "contact@clouddiagnoze.com",
    },
    "license_info": {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
}

# Exemples pour chaque endpoint
EXAMPLES = {
    "scan_request": {
        "provider": "aws",
        "services": ["ec2", "s3"],
        "auth_mode": {
            "type": "sts",
            "role_arn": "arn:aws:iam::123456789012:role/CloudDiagnozeRole"
        },
        "client_id": "mon-client-prod",
        "regions": ["us-east-1", "eu-west-1"]
    },
    "scan_response": {
        "scan_id": "scan-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": "QUEUED",
        "message": "Scan for provider 'aws' and services ['ec2', 's3'] has been queued."
    }
}

# Documentation des endpoints
ENDPOINTS_DOC = {
    "/scans": {
        "post": {
            "summary": "🚀 Lancer un scan d'infrastructure",
            "description": """
            Lance un scan asynchrone de votre infrastructure cloud.
            
            **Flux :** Validation → Réponse immédiate → Traitement background
            """,
            "responses": {
                202: "Scan lancé avec succès",
                400: "Paramètres invalides",
                500: "Erreur serveur"
            }
        }
    }
}