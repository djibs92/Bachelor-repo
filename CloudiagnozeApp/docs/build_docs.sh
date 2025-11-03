#!/bin/bash
echo "🚀 Génération documentation CloudDiagnoze..."

cd api
python generate_openapi.py

if [ "$1" = "--deploy" ]; then
    echo "📤 Déploiement GitHub Pages..."
    cp generated/openapi.json ../
    cp generated/redoc.html ../index.html  # ← Renommer en index.html !
fi

echo "✅ Documentation prête !"
