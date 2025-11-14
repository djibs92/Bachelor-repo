#!/bin/bash

echo "🧹 Nettoyage de l'ancien état Terraform..."

# Sauvegarder l'ancien état
if [ -f "terraform.tfstate" ]; then
    mv terraform.tfstate terraform.tfstate.old.$(date +%Y%m%d_%H%M%S)
    echo "✅ Ancien tfstate sauvegardé"
fi

if [ -f "terraform.tfstate.backup" ]; then
    mv terraform.tfstate.backup terraform.tfstate.backup.old.$(date +%Y%m%d_%H%M%S)
    echo "✅ Ancien tfstate.backup sauvegardé"
fi

# Supprimer le dossier .terraform
if [ -d ".terraform" ]; then
    rm -rf .terraform
    echo "✅ Dossier .terraform supprimé"
fi

# Supprimer le lock file
if [ -f ".terraform.lock.hcl" ]; then
    rm .terraform.lock.hcl
    echo "✅ Lock file supprimé"
fi

echo ""
echo "🚀 Réinitialisation de Terraform..."
export AWS_PROFILE=terraform-provisionner
terraform init

echo ""
echo "✅ Terraform réinitialisé et prêt !"
echo ""
echo "📋 Prochaines étapes :"
echo "   1. terraform plan    # Vérifier le plan"
echo "   2. ./deploy.sh       # Déployer l'infrastructure"

