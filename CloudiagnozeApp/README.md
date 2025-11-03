# 🚀 CloudDiagnoze TUI

Une interface utilisateur en terminal (TUI) élégante pour CloudDiagnoze, construite avec [Bubble Tea](https://github.com/charmbracelet/bubbletea).

## 📋 Description

CloudDiagnoze TUI offre une interface interactive et intuitive pour scanner votre infrastructure cloud AWS. Plus besoin de Postman ou de requêtes curl complexes - tout se fait directement dans votre terminal avec une interface moderne et responsive.

## ✨ Fonctionnalités

- 🔐 **Configuration AWS** : Saisie sécurisée des paramètres de connexion
- 🎯 **Sélection des services** : Multi-select interactif (EC2, S3, RDS, VPC, IAM)
- 🌍 **Sélection des régions** : Choix multiple des régions AWS à scanner
- 📊 **Progression en temps réel** : Suivi visuel du scan avec barres de progression
- 📋 **Résultats structurés** : Affichage élégant des événements 2CBP générés
- ⚡ **Interface responsive** : S'adapte à la taille de votre terminal

## 🛠️ Installation

### Prérequis

- Go 1.21 ou plus récent
- Accès à l'API CloudDiagnoze (doit être en cours d'exécution)

### Build depuis les sources

```bash
# Cloner le projet
git clone <repository-url>
cd clouddiagnoze-tui

# Installer les dépendances
make deps

# Construire l'application
make build

# Ou directement exécuter
make run
```

### Installation globale

```bash
# Construire et installer
make install

# Utiliser depuis n'importe où
clouddiagnoze
```

## 🚀 Utilisation

### Démarrage rapide

```bash
# Lancer l'application
./build/clouddiagnoze

# Ou si installé globalement
clouddiagnoze
```

### Flux d'utilisation

1. **Configuration AWS** 🔐
   - Saisissez votre `client_id`
   - Configurez le `role_arn` pour l'authentification
   - Validez la connexion

2. **Sélection des services** 🎯
   - Choisissez les services AWS à scanner (EC2, S3, RDS, etc.)
   - Navigation avec les flèches ↑↓ et sélection avec Espace

3. **Sélection des régions** 🌍
   - Sélectionnez les régions AWS à inclure dans le scan
   - Support multi-sélection

4. **Lancement du scan** 📊
   - Visualisation en temps réel de la progression
   - Logs détaillés du processus

5. **Consultation des résultats** 📋
   - Affichage structuré des événements 2CBP
   - Navigation dans les résultats
   - Export possible (à venir)

## ⌨️ Raccourcis clavier

- `↑/↓` : Navigation dans les listes
- `Espace` : Sélection/Désélection
- `Enter` : Valider et passer à l'étape suivante
- `Esc` : Retour à l'étape précédente
- `q` : Quitter l'application
- `?` : Afficher l'aide

## 🔧 Configuration

### Variables d'environnement

```bash
# URL de l'API CloudDiagnoze (par défaut: http://localhost:8000)
export CLOUDDIAGNOZE_API_URL="http://your-api-url:8000"

# Timeout pour les requêtes API (par défaut: 30s)
export CLOUDDIAGNOZE_TIMEOUT="30s"
```

### Fichier de configuration

Créez un fichier `configs/config.yaml` :

```yaml
api:
  url: "http://localhost:8000"
  timeout: "30s"

ui:
  theme: "default"
  animations: true
```

## 🧪 Développement

### Commandes disponibles

```bash
make help          # Afficher l'aide
make build         # Construire l'application
make run           # Exécuter l'application
make test          # Lancer les tests
make dev           # Mode développement avec auto-reload
make fmt           # Formater le code
make lint          # Linter le code
make clean         # Nettoyer les artifacts
```

### Structure du projet

```
clouddiagnoze-tui/
├── cmd/clouddiagnoze/    # Point d'entrée
├── internal/
│   ├── api/              # Client HTTP vers CloudDiagnoze API
│   ├── config/           # Configuration
│   ├── models/           # Modèles de données
│   ├── ui/               # Interface utilisateur
│   │   ├── components/   # Composants réutilisables
│   │   ├── screens/      # Écrans de l'application
│   │   └── styles/       # Styles et thèmes
│   └── utils/            # Utilitaires
└── configs/              # Fichiers de configuration
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🔗 Liens utiles

- [CloudDiagnoze API](../Reflection-sur-Project/) - L'API backend
- [Bubble Tea](https://github.com/charmbracelet/bubbletea) - Framework TUI
- [Lip Gloss](https://github.com/charmbracelet/lipgloss) - Styles pour terminal

---

*Développé avec ❤️ pour simplifier la gestion d'infrastructure cloud*
