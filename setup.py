#!/usr/bin/env python3
"""
🚀 Script de Configuration Interactive - CloudDiagnoze
======================================================
Ce script guide l'utilisateur dans la configuration complète
du déploiement Docker de CloudDiagnoze.

Usage:
    python setup.py

Ce script va :
  1. Collecter les credentials de base de données
  2. Générer automatiquement une clé JWT sécurisée
  3. Collecter les credentials AWS
  4. Créer le fichier .env
  5. Proposer de lancer Docker Compose
"""

import os
import sys
import secrets
import subprocess
import shutil

# ========================================
# CODES COULEURS ANSI
# ========================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

# ========================================
# FONCTIONS D'AFFICHAGE
# ========================================
def print_header(text):
    """Affiche un header stylisé"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_step(step_num, text):
    """Affiche une étape numérotée"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}📌 ÉTAPE {step_num}: {text}{Colors.END}")
    print(f"{Colors.CYAN}{'─'*50}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def get_input(prompt, default=None, hide=False):
    """Récupère une saisie utilisateur avec valeur par défaut optionnelle"""
    try:
        if default:
            display_prompt = f"{prompt} [{default}]"
        else:
            display_prompt = prompt
        
        if hide:
            import getpass
            value = getpass.getpass(f"{Colors.YELLOW}➤ {display_prompt}: {Colors.END}")
        else:
            value = input(f"{Colors.YELLOW}➤ {display_prompt}: {Colors.END}")
        
        # Si l'utilisateur appuie sur Entrée, retourner la valeur par défaut
        if not value and default:
            return default
        return value
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Annulé par l'utilisateur.{Colors.END}")
        sys.exit(1)

def confirm(prompt):
    """Demande une confirmation oui/non"""
    while True:
        response = get_input(f"{prompt} (oui/non)").lower().strip()
        if response in ['oui', 'o', 'yes', 'y']:
            return True
        if response in ['non', 'n', 'no']:
            return False
        print_warning("Répondez par 'oui' ou 'non'")

def get_password(prompt, min_length=8):
    """Récupère un mot de passe avec validation"""
    while True:
        password = get_input(prompt, hide=True)
        if len(password) >= min_length:
            return password
        print_warning(f"Le mot de passe doit contenir au moins {min_length} caractères")

# ========================================
# VÉRIFICATIONS PRÉALABLES
# ========================================
def check_prerequisites():
    """Vérifie que Docker et Docker Compose sont installés"""
    print_step("0", "Vérification des prérequis")
    
    # Vérifier Docker
    if shutil.which("docker"):
        print_success("Docker est installé")
    else:
        print_error("Docker n'est pas installé !")
        print_info("Installez Docker : https://docs.docker.com/get-docker/")
        return False
    
    # Vérifier Docker Compose
    try:
        result = subprocess.run(["docker", "compose", "version"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Docker Compose est installé")
        else:
            raise Exception()
    except:
        print_error("Docker Compose n'est pas installé !")
        return False
    
    # Vérifier si .env existe déjà
    if os.path.exists(".env"):
        print_warning("Un fichier .env existe déjà !")
        if not confirm("Voulez-vous le remplacer ?"):
            print_info("Configuration annulée.")
            return False

    return True

# ========================================
# COLLECTE DES CREDENTIALS
# ========================================
def collect_database_credentials():
    """Collecte les credentials de base de données"""
    print_step("1", "Configuration de la Base de Données")

    print_info("Choisissez vos mots de passe pour MariaDB.")
    print_info("Ces mots de passe seront utilisés uniquement en local.\n")

    db_root_password = get_password("Mot de passe ROOT MariaDB (min 8 caractères)")
    db_password = get_password("Mot de passe utilisateur applicatif (min 8 caractères)")
    db_name = get_input("Nom de la base de données", default="clouddiagnoze")
    db_user = get_input("Nom d'utilisateur BDD", default="clouddiagnoze_user")

    print_success("Credentials BDD configurés !")

    return {
        "DB_ROOT_PASSWORD": db_root_password,
        "DB_PASSWORD": db_password,
        "DB_NAME": db_name,
        "DB_USER": db_user
    }

def generate_jwt_secret():
    """Génère automatiquement une clé JWT sécurisée"""
    print_step("2", "Génération de la Clé JWT")

    print_info("Génération d'une clé secrète sécurisée...")

    # Génération avec le module secrets (cryptographiquement sûr)
    jwt_secret = secrets.token_urlsafe(32)

    print_success(f"Clé JWT générée : {jwt_secret[:10]}...{jwt_secret[-10:]}")
    print_info("Cette clé sera utilisée pour signer les tokens d'authentification.\n")

    return jwt_secret

def collect_aws_credentials():
    """Collecte les credentials AWS"""
    print_step("3", "Configuration AWS")

    print(f"""
{Colors.BLUE}╔══════════════════════════════════════════════════════════╗
║  📖 OÙ TROUVER VOS CREDENTIALS AWS ?                      ║
╠══════════════════════════════════════════════════════════╣
║  1. Connectez-vous à AWS Console                          ║
║     https://console.aws.amazon.com                        ║
║                                                           ║
║  2. Allez dans IAM → Users → Votre utilisateur            ║
║                                                           ║
║  3. Onglet "Security credentials"                         ║
║                                                           ║
║  4. Cliquez "Create access key"                           ║
║                                                           ║
║  5. Copiez l'Access Key ID et le Secret Access Key        ║
╚══════════════════════════════════════════════════════════╝
{Colors.END}""")

    aws_access_key = get_input("AWS Access Key ID")
    aws_secret_key = get_input("AWS Secret Access Key", hide=True)
    aws_region = get_input("AWS Default Region", default="eu-west-1")

    print_success("Credentials AWS configurés !")

    return {
        "AWS_ACCESS_KEY_ID": aws_access_key,
        "AWS_SECRET_ACCESS_KEY": aws_secret_key,
        "AWS_DEFAULT_REGION": aws_region
    }

# ========================================
# GÉNÉRATION DU FICHIER .ENV
# ========================================
def generate_env_file(db_creds, jwt_secret, aws_creds):
    """Génère le fichier .env avec toutes les configurations"""
    print_step("4", "Création du fichier .env")

    env_content = f"""# ========================================
# CLOUDDIAGNOZE - CONFIGURATION
# ========================================
# Fichier généré automatiquement par setup.py
# Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ========================================

# ========================================
# 🗄️  BASE DE DONNÉES MARIADB
# ========================================
DB_ROOT_PASSWORD={db_creds['DB_ROOT_PASSWORD']}
DB_NAME={db_creds['DB_NAME']}
DB_USER={db_creds['DB_USER']}
DB_PASSWORD={db_creds['DB_PASSWORD']}

# ========================================
# 🔐 SÉCURITÉ JWT
# ========================================
SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# ========================================
# ☁️  AWS CREDENTIALS
# ========================================
AWS_ACCESS_KEY_ID={aws_creds['AWS_ACCESS_KEY_ID']}
AWS_SECRET_ACCESS_KEY={aws_creds['AWS_SECRET_ACCESS_KEY']}
AWS_DEFAULT_REGION={aws_creds['AWS_DEFAULT_REGION']}

# ========================================
# ⚙️  APPLICATION
# ========================================
ENVIRONMENT=production
"""

    with open(".env", "w") as f:
        f.write(env_content)

    print_success("Fichier .env créé avec succès !")
    print_info(f"Emplacement : {os.path.abspath('.env')}")

# ========================================
# LANCEMENT DOCKER COMPOSE
# ========================================
def launch_docker_compose():
    """Propose de lancer Docker Compose"""
    print_step("5", "Lancement de l'Application")

    if not confirm("Voulez-vous démarrer l'application maintenant ?"):
        print_info("Vous pouvez lancer manuellement avec : docker-compose up -d --build")
        return False

    print_info("Démarrage de Docker Compose (cela peut prendre quelques minutes)...\n")

    try:
        # Lancer docker-compose avec affichage en temps réel
        process = subprocess.Popen(
            ["docker", "compose", "up", "-d", "--build"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Afficher la sortie en temps réel
        for line in process.stdout:
            print(f"  {line}", end="")

        process.wait()

        if process.returncode == 0:
            print_success("\n🎉 Application démarrée avec succès !")
            return True
        else:
            print_error("Erreur lors du démarrage")
            return False

    except Exception as e:
        print_error(f"Erreur : {e}")
        return False

def show_final_instructions():
    """Affiche les instructions finales"""
    print(f"""
{Colors.GREEN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════╗
║           🎉 CONFIGURATION TERMINÉE !                    ║
╚══════════════════════════════════════════════════════════╝
{Colors.END}

{Colors.CYAN}📍 Accès à l'application :{Colors.END}

   🌐 Frontend (Interface)    : http://localhost
   📖 Documentation API       : http://localhost/docs
   🔧 API Backend             : http://localhost/api/v1

{Colors.CYAN}📋 Commandes utiles :{Colors.END}

   ▸ Voir les logs        : docker-compose logs -f
   ▸ Arrêter              : docker-compose down
   ▸ Redémarrer           : docker-compose restart
   ▸ Reset complet        : docker-compose down -v

{Colors.YELLOW}⚠️  N'oubliez pas :{Colors.END}
   - Configurez votre Role ARN dans l'interface après inscription
   - Le fichier .env contient vos secrets, ne le partagez pas !

{Colors.GREEN}Bonne utilisation de CloudDiagnoze ! 🚀{Colors.END}
""")

# ========================================
# MAIN
# ========================================
def main():
    """Fonction principale"""
    print_header("🚀 CloudDiagnoze - Assistant de Configuration")

    print(f"""
{Colors.BLUE}Bienvenue dans l'assistant de configuration de CloudDiagnoze !

Ce script va vous guider pour :
  ✓ Configurer la base de données MariaDB
  ✓ Générer une clé JWT sécurisée
  ✓ Configurer vos credentials AWS
  ✓ Créer le fichier .env
  ✓ Lancer l'application avec Docker
{Colors.END}
""")

    if not confirm("Prêt à commencer ?"):
        print_info("À bientôt !")
        sys.exit(0)

    # Vérifications préalables
    if not check_prerequisites():
        sys.exit(1)

    # Étape 1 : Credentials BDD
    db_creds = collect_database_credentials()

    # Étape 2 : Génération JWT
    jwt_secret = generate_jwt_secret()

    # Étape 3 : Credentials AWS
    aws_creds = collect_aws_credentials()

    # Étape 4 : Génération .env
    generate_env_file(db_creds, jwt_secret, aws_creds)

    # Étape 5 : Lancement Docker
    launch_docker_compose()

    # Instructions finales
    show_final_instructions()

if __name__ == "__main__":
    main()

