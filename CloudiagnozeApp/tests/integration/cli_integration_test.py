#!/usr/bin/env python3
"""
🧪 Test d'intégration interactif CLI - CloudDiagnoze
====================================================
Ce script teste le flux complet :
  1. Signup (Inscription)
  2. Login (Connexion)
  3. Configuration du Role ARN
  4. Vérification en BDD

Usage:
    python cli_integration_test.py

Prérequis:
    - Le backend doit être lancé (uvicorn)
    - pip install requests
"""

import requests
import json
import sys
import time

# ========================================
# CONFIGURATION
# ========================================
API_BASE_URL = "http://localhost:8000/api/v1"

# Codes couleurs ANSI pour le terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

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
    """Affiche un message de succès"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    """Affiche un message d'erreur"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    """Affiche une information"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def print_warning(text):
    """Affiche un avertissement"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_json(data, title="Réponse API"):
    """Affiche du JSON formaté"""
    print(f"\n{Colors.BOLD}📋 {title}:{Colors.END}")
    print(f"{Colors.CYAN}{json.dumps(data, indent=2, ensure_ascii=False)}{Colors.END}")

def get_input(prompt, hide=False):
    """Récupère une saisie utilisateur"""
    try:
        if hide:
            import getpass
            return getpass.getpass(f"{Colors.YELLOW}➤ {prompt}: {Colors.END}")
        return input(f"{Colors.YELLOW}➤ {prompt}: {Colors.END}")
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}🛑 Test annulé par l'utilisateur{Colors.END}")
        sys.exit(0)

# ========================================
# FONCTIONS DE TEST
# ========================================

def check_server():
    """Vérifie que le serveur est accessible"""
    print_info(f"Vérification de la connexion à {API_BASE_URL}...")
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/", timeout=5)
        print_success("Serveur accessible !")
        return True
    except requests.exceptions.ConnectionError:
        print_error(f"Le serveur n'est pas accessible à {API_BASE_URL}")
        print_warning("Assurez-vous que le backend est lancé avec : uvicorn api.main:app --reload")
        return False

def step1_signup(email, password):
    """Étape 1 : Inscription"""
    print_step(1, "INSCRIPTION (Signup)")

    print_info(f"Envoi POST /auth/signup avec email: {email}")

    payload = {
        "email": email,
        "password": password
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/signup",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        data = response.json()
        print_json(data, "Réponse Signup")

        if response.status_code == 201:
            print_success("Inscription réussie !")
            return True
        else:
            print_error(f"Échec inscription: {data.get('detail', 'Erreur inconnue')}")
            return False

    except Exception as e:
        print_error(f"Erreur lors de l'inscription: {str(e)}")
        return False

def step2_login(email, password):
    """Étape 2 : Connexion et récupération du token"""
    print_step(2, "CONNEXION (Login)")

    print_info(f"Envoi POST /auth/login avec email: {email}")

    payload = {
        "email": email,
        "password": password
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        data = response.json()

        if response.status_code == 200:
            token = data.get("access_token")
            print_json(data, "Réponse Login")
            print_success(f"Connexion réussie ! Token JWT obtenu")
            print_info(f"Token (premiers 50 chars): {token[:50]}...")
            return token
        else:
            print_json(data, "Erreur Login")
            print_error(f"Échec connexion: {data.get('detail', 'Erreur inconnue')}")
            return None

    except Exception as e:
        print_error(f"Erreur lors de la connexion: {str(e)}")
        return None

def step3_configure_role_arn(token, role_arn):
    """Étape 3 : Configuration du Role ARN"""
    print_step(3, "CONFIGURATION DU ROLE ARN")

    print_info(f"Envoi PATCH /auth/me avec role_arn: {role_arn}")

    payload = {
        "role_arn": role_arn
    }

    try:
        response = requests.patch(
            f"{API_BASE_URL}/auth/me",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )

        data = response.json()
        print_json(data, "Réponse Mise à jour")

        if response.status_code == 200:
            print_success("Role ARN configuré avec succès !")
            return True
        else:
            print_error(f"Échec configuration: {data.get('detail', 'Erreur inconnue')}")
            return False

    except Exception as e:
        print_error(f"Erreur lors de la configuration: {str(e)}")
        return False

def step4_verify_database(token, expected_email, expected_role_arn):
    """Étape 4 : Vérification en base de données"""
    print_step(4, "VÉRIFICATION EN BASE DE DONNÉES")

    print_info("Envoi GET /auth/me pour récupérer les données depuis la BDD...")

    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        data = response.json()
        print_json(data, "Données utilisateur depuis la BDD")

        if response.status_code != 200:
            print_error(f"Échec récupération: {data.get('detail', 'Erreur inconnue')}")
            return False

        # Vérifications
        print(f"\n{Colors.BOLD}🔍 VÉRIFICATIONS:{Colors.END}")

        all_passed = True

        # Vérif email
        if data.get("email") == expected_email:
            print_success(f"Email correspond: {expected_email}")
        else:
            print_error(f"Email ne correspond pas: attendu={expected_email}, reçu={data.get('email')}")
            all_passed = False

        # Vérif role_arn
        if data.get("role_arn") == expected_role_arn:
            print_success(f"Role ARN correspond: {expected_role_arn}")
        else:
            print_error(f"Role ARN ne correspond pas: attendu={expected_role_arn}, reçu={data.get('role_arn')}")
            all_passed = False

        # Vérif ID (prouve que l'user existe en BDD)
        if data.get("id"):
            print_success(f"Utilisateur existe en BDD avec ID: {data.get('id')}")
        else:
            print_error("ID utilisateur non trouvé")
            all_passed = False

        # Vérif created_at
        if data.get("created_at"):
            print_success(f"Date de création: {data.get('created_at')}")

        return all_passed

    except Exception as e:
        print_error(f"Erreur lors de la vérification: {str(e)}")
        return False


def step5_scan_ec2(token, role_arn):
    """Étape 5 : Lancer un scan EC2"""
    print_step(5, "SCAN EC2 (eu-west-1, eu-west-2)")

    regions = ["eu-west-1", "eu-west-2"]
    print_info(f"Lancement du scan EC2 sur les régions: {', '.join(regions)}")

    payload = {
        "provider": "aws",
        "services": ["ec2"],
        "auth_mode": {
            "type": "sts",
            "role_arn": role_arn
        },
        "client_id": "CLI-Integration-Test",
        "regions": regions
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/scans",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )

        data = response.json()
        print_json(data, "Réponse Scan")

        if response.status_code == 202:
            scan_id = data.get("scan_id")
            print_success(f"Scan lancé avec succès ! ID: {scan_id}")
            print_info("Le scan s'exécute en arrière-plan...")
            return scan_id
        else:
            print_error(f"Échec du scan: {data.get('detail', 'Erreur inconnue')}")
            return None

    except Exception as e:
        print_error(f"Erreur lors du scan: {str(e)}")
        return None


def step6_wait_and_verify_scan(token, scan_id, max_wait=60):
    """Étape 6 : Attendre et vérifier les résultats du scan"""
    print_step(6, "VÉRIFICATION DES RÉSULTATS DU SCAN")

    print_info(f"Attente de la fin du scan (max {max_wait}s)...")

    # Attendre un peu que le scan se termine
    wait_time = 10
    print_info(f"⏳ Attente de {wait_time} secondes pour laisser le scan s'exécuter...")

    for i in range(wait_time):
        time.sleep(1)
        print(f"\r{Colors.YELLOW}   ⏳ {i+1}/{wait_time}s...{Colors.END}", end="", flush=True)
    print()  # Nouvelle ligne

    # Vérifier l'historique des scans
    print_info("Récupération de l'historique des scans...")

    try:
        response = requests.get(
            f"{API_BASE_URL}/scans/history",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            print_json(data, "Historique des scans")

            if data.get("scans") and len(data["scans"]) > 0:
                print_success(f"✅ {len(data['scans'])} scan(s) trouvé(s) en BDD !")
                return True
            else:
                print_warning("Aucun scan trouvé dans l'historique")
                return False
        else:
            print_error(f"Erreur récupération historique: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Erreur: {str(e)}")
        return False


def step7_get_ec2_instances(token):
    """Étape 7 : Récupérer les instances EC2 scannées"""
    print_step(7, "RÉCUPÉRATION DES INSTANCES EC2")

    print_info("Récupération des instances EC2 depuis la BDD...")

    try:
        response = requests.get(
            f"{API_BASE_URL}/ec2/instances",
            headers={"Authorization": f"Bearer {token}"}
        )

        data = response.json()

        if response.status_code == 200:
            instances = data.get("instances", [])
            total = data.get("total", 0)

            if total > 0:
                print_success(f"✅ {total} instance(s) EC2 trouvée(s) !")
                print_json(data, "Instances EC2")
                return True
            else:
                print_warning("Aucune instance EC2 trouvée (le compte AWS n'a peut-être pas d'instances)")
                print_json(data, "Réponse API")
                return True  # Pas une erreur, juste pas d'instances
        else:
            print_error(f"Erreur: {data.get('detail', 'Erreur inconnue')}")
            return False

    except Exception as e:
        print_error(f"Erreur: {str(e)}")
        return False


def step8_cleanup_scan_data(token):
    """Étape 8 (optionnelle) : Nettoyage des données de scan"""
    print_step(8, "NETTOYAGE DES DONNÉES DE SCAN (Optionnel)")

    confirm = get_input("Voulez-vous supprimer les données de scan ? (oui/non)")

    if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
        print_info("Nettoyage ignoré. Les données restent en BDD pour la démo frontend !")
        return False  # Retourne False pour indiquer qu'on n'a pas nettoyé

    try:
        response = requests.delete(
            f"{API_BASE_URL}/admin/clear-user-data?confirm=true",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        data = response.json()
        print_json(data, "Résultat du nettoyage")

        if response.status_code == 200:
            print_success("Données de scan supprimées !")
            return True
        else:
            print_error(f"Échec nettoyage: {data.get('detail', 'Erreur')}")
            return False

    except Exception as e:
        print_warning(f"Nettoyage non effectué: {str(e)}")
        return False


def step9_delete_user(token):
    """Étape 9 (optionnelle) : Suppression du compte utilisateur"""
    print_step(9, "SUPPRESSION DU COMPTE (Optionnel)")

    print(f"""
{Colors.YELLOW}{Colors.BOLD}⚠️  ATTENTION : Cette action est IRRÉVERSIBLE !{Colors.END}
{Colors.YELLOW}Le compte utilisateur et toutes ses données seront définitivement supprimés.{Colors.END}
""")

    confirm = get_input("Voulez-vous supprimer le compte utilisateur de test ? (oui/non)")

    if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
        print_info("Suppression du compte ignorée. L'utilisateur reste en BDD.")
        return False

    # Double confirmation pour la sécurité
    confirm2 = get_input("Êtes-vous VRAIMENT sûr ? Tapez 'SUPPRIMER' pour confirmer")

    if confirm2 != "SUPPRIMER":
        print_info("Suppression annulée.")
        return False

    try:
        response = requests.delete(
            f"{API_BASE_URL}/auth/me?confirm=true",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

        data = response.json()
        print_json(data, "Résultat de la suppression")

        if response.status_code == 200:
            print_success("🗑️ Compte utilisateur supprimé définitivement !")
            return True
        else:
            print_error(f"Échec suppression: {data.get('detail', 'Erreur')}")
            return False

    except Exception as e:
        print_warning(f"Suppression non effectuée: {str(e)}")
        return False


# ========================================
# FONCTION PRINCIPALE
# ========================================

def main():
    """Exécute le test d'intégration complet"""
    print_header("🧪 TEST D'INTÉGRATION CLI - CloudDiagnoze")

    print(f"""
{Colors.BOLD}Ce test va simuler le flux complet utilisateur :{Colors.END}
  1️⃣  Inscription (Signup)
  2️⃣  Connexion (Login)
  3️⃣  Configuration du Role ARN
  4️⃣  Vérification utilisateur en BDD
  5️⃣  Scan EC2 (eu-west-1, eu-west-2)
  6️⃣  Vérification historique des scans
  7️⃣  Récupération des instances EC2
  8️⃣  Nettoyage des données de scan (optionnel)
  9️⃣  Suppression du compte (optionnel)

{Colors.YELLOW}Prérequis: Le backend doit être lancé !{Colors.END}
""")

    # Vérification serveur
    if not check_server():
        sys.exit(1)

    print(f"\n{Colors.BOLD}📝 SAISIE DES INFORMATIONS{Colors.END}")
    print(f"{Colors.CYAN}{'─'*50}{Colors.END}")

    # Saisie des informations
    email = get_input("Email pour le test")
    password = get_input("Mot de passe (min 8 chars, 1 majuscule, 1 chiffre)", hide=True)
    role_arn = get_input("AWS Role ARN (ex: arn:aws:iam::123456789:role/MyRole)")

    print(f"\n{Colors.BOLD}🚀 DÉMARRAGE DES TESTS{Colors.END}")
    time.sleep(1)

    results = {
        "signup": False,
        "login": False,
        "configure_arn": False,
        "verify_user": False,
        "scan_ec2": False,
        "verify_scan": False,
        "get_instances": False
    }

    # ÉTAPE 1: Signup
    results["signup"] = step1_signup(email, password)
    if not results["signup"]:
        print_warning("L'inscription a échoué. Tentative de connexion (l'utilisateur existe peut-être déjà)...")

    time.sleep(0.5)

    # ÉTAPE 2: Login
    token = step2_login(email, password)
    results["login"] = token is not None

    if not results["login"]:
        print_error("Impossible de continuer sans token JWT.")
        print_header("❌ TEST ÉCHOUÉ")
        sys.exit(1)

    time.sleep(0.5)

    # ÉTAPE 3: Configure Role ARN
    results["configure_arn"] = step3_configure_role_arn(token, role_arn)

    time.sleep(0.5)

    # ÉTAPE 4: Verify User in Database
    results["verify_user"] = step4_verify_database(token, email, role_arn)

    time.sleep(0.5)

    # ÉTAPE 5: Scan EC2
    scan_id = step5_scan_ec2(token, role_arn)
    results["scan_ec2"] = scan_id is not None

    if results["scan_ec2"]:
        # ÉTAPE 6: Wait and verify scan
        results["verify_scan"] = step6_wait_and_verify_scan(token, scan_id)

        time.sleep(0.5)

        # ÉTAPE 7: Get EC2 instances
        results["get_instances"] = step7_get_ec2_instances(token)
    else:
        print_warning("Scan non lancé, étapes 6 et 7 ignorées")
        results["verify_scan"] = False
        results["get_instances"] = False

    # ÉTAPE 8: Cleanup scan data (optionnel)
    scan_data_deleted = step8_cleanup_scan_data(token)

    # ÉTAPE 9: Delete user account (optionnel)
    if scan_data_deleted:
        step9_delete_user(token)
    else:
        print(f"\n{Colors.YELLOW}ℹ️  Étape 9 ignorée car les données de scan n'ont pas été supprimées.{Colors.END}")
        print(f"{Colors.YELLOW}   (Pour supprimer le compte, supprimez d'abord les données de scan){Colors.END}")

    # ========================================
    # RÉSUMÉ FINAL
    # ========================================
    print_header("📊 RÉSUMÉ DES TESTS")

    print(f"{Colors.BOLD}Résultats:{Colors.END}\n")

    for test_name, passed in results.items():
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"  {test_name.replace('_', ' ').title():.<30} {status}")

    # Calcul du succès (on tolère l'échec du scan si AWS n'est pas configuré)
    core_tests = ["login", "configure_arn", "verify_user"]
    core_passed = all(results[t] for t in core_tests)
    all_passed = all(results.values())

    if all_passed:
        print_header("🎉 TOUS LES TESTS SONT PASSÉS !")
        print(f"""
{Colors.GREEN}{Colors.BOLD}Le flux complet Front-end ↔ Back-end fonctionne !{Colors.END}

{Colors.BOLD}Ce qui a été prouvé :{Colors.END}
  ✅ L'API d'inscription crée bien l'utilisateur en BDD
  ✅ L'API de connexion génère un token JWT valide
  ✅ L'API de mise à jour modifie bien les données en BDD
  ✅ L'API GET /me récupère les données depuis la BDD
  ✅ Le scan EC2 s'exécute et stocke les données en BDD
  ✅ Les instances EC2 sont récupérables via l'API

{Colors.CYAN}→ Tu peux maintenant te connecter sur le frontend et voir les résultats !{Colors.END}
""")
    elif core_passed:
        print_header("⚠️ TESTS PRINCIPAUX OK - SCAN AWS ÉCHOUÉ")
        print(f"""
{Colors.YELLOW}Les tests d'authentification fonctionnent, mais le scan AWS a échoué.{Colors.END}
{Colors.YELLOW}Vérifiez que :{Colors.END}
  - Le Role ARN est valide
  - Votre compte AWS a les permissions nécessaires
  - Les credentials AWS sont configurés dans .env
""")
    else:
        print_header("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print(f"{Colors.YELLOW}Vérifiez les erreurs ci-dessus et relancez le test.{Colors.END}")

    return 0 if core_passed else 1


if __name__ == "__main__":
    sys.exit(main())

