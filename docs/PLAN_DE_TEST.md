# Plan de Test — CloudDiagnoze

> Document à destination du jury du Bachelor.
> Décrit la stratégie de tests, les périmètres couverts et la procédure d'exécution.

---

## 1. Objectifs

Le plan de test a pour but de garantir :

- **La fiabilité** des scanners cloud (EC2, S3) qui constituent le cœur métier de CloudDiagnoze.
- **La sécurité** des endpoints exposés par l'API (authentification, autorisations, isolation par utilisateur).
- **La cohérence** des données persistées en base (scans, ressources, métriques).
- **La non-régression** lors des évolutions futures (ajout de nouveaux scanners, refactorisations).

Les tests sont exécutés automatiquement en local par l'étudiant et constituent un filet de sécurité avant tout déploiement.

---

## 2. Stratégie de test

Deux niveaux de tests sont mis en place, conformément aux bonnes pratiques de l'industrie (pyramide de tests).

### 2.1 Tests unitaires

- **Périmètre** : composants isolés (scanners AWS, services).
- **Approche** : on instancie le composant, on lui injecte des dépendances simulées et on vérifie son comportement.
- **Outils** :
  - `pytest` comme framework de test.
  - `pytest-asyncio` car les scanners sont des coroutines (`async def scan()`).
  - **`moto`** (`mock_aws`) pour simuler les services AWS (EC2, S3, CloudWatch, STS) en mémoire, sans appel réel à AWS.
  - `pytest-mock` pour les mocks ponctuels (session de base de données par exemple).
  - `faker` pour générer des données de test réalistes.

L'utilisation de **Moto** permet de tester le code AWS **sans coût**, **sans dépendance réseau** et de manière **reproductible**.

### 2.2 Tests d'intégration

- **Périmètre** : endpoints HTTP de l'API FastAPI, de bout en bout (requête HTTP → routeur → service → base de données → réponse JSON).
- **Approche** : on lance un client de test (`fastapi.testclient.TestClient`) qui appelle l'API comme un vrai client, mais en in-process.
- **Base de données** : SQLite en mémoire (`sqlite:///:memory:`) avec `StaticPool` pour partager la connexion entre threads. Les tables sont recréées avant chaque test pour garantir l'isolation.
- **Override de dépendances** : `app.dependency_overrides[get_db]` est utilisé pour injecter la session de test à la place de la session de production.
- **Authentification** : les tests qui nécessitent un utilisateur connecté génèrent un JWT via `create_access_token` et le passent dans l'en-tête `Authorization`.

### 2.3 Test d'intégration CLI

Un script `tests/integration/cli_integration_test.py` permet de tester manuellement le flux complet (signup → login → configuration ARN) contre une instance réellement lancée du backend. Ce script est un outil de validation manuelle, hors du périmètre `pytest`.

---

## 3. Périmètres testés

| Domaine | Fichier de tests | Classes / Suites | Nombre de tests |
|---|---|---|---|
| **Scanner EC2** | `tests/aws_tests/test_ec2_scanner.py` | Basic, Errors, Metrics, EdgeCases, Integration | 15 |
| **Scanner S3** | `tests/aws_tests/test_s3_scanner.py` | Basic, Configurations, Metrics, EdgeCases, Integration | 17 |
| **Authentification** | `tests/integration/test_auth_endpoints.py` | Signup, Login, Me, ForgotPassword, ResetPassword | 21 |
| **Scans (création / export)** | `tests/integration/test_scan_endpoints.py` | CreateScan, ExportScan | 11 |
| **Lecture des données** | `tests/integration/test_events_endpoints.py` | ScansHistory, EC2Instances, S3Buckets | 12 |
| **Total** | | | **76** |

### Détails par domaine

**Scanner EC2** — couvre : scan d'une région vide, instance unique, instances multiples, régions multiples en parallèle, régions invalides, mélange de régions valides/invalides, métriques CloudWatch (CPU, réseau), instance sans métriques, instance arrêtée, tags, types d'instance variés, format ARN, validation du format de sortie.

**Scanner S3** — couvre : scan sans buckets, bucket unique, buckets multiples, configurations (versioning, chiffrement, accès public), métriques (taille, nombre d'objets), buckets vides, format de sortie.

**Authentification** — couvre : inscription (succès, doublon, format invalide), connexion (succès, mauvais mot de passe, utilisateur inexistant), endpoint `/me` (avec et sans token), `forgot-password` (génération du token de reset), `reset-password` (validation du token, expiration).

**Scans** — couvre : création d'un scan (succès, sans authentification, sans Role ARN configuré), export des résultats (JSON, CSV, scan inexistant).

**Lecture des données** — couvre : historique des scans, liste des instances EC2 et des buckets S3, filtres, isolation par utilisateur (un utilisateur ne voit pas les données d'un autre).

---

## 4. Fixtures et utilitaires

Les fixtures partagées sont définies dans `tests/conftest.py` :

- `mock_aws_credentials` (autouse) — injecte des credentials AWS factices dans l'environnement pour éviter toute fuite ou erreur de configuration.
- `client_id`, `test_regions`, `single_region` — données de test réutilisables.
- `mock_db_session` — session SQLAlchemy mockée pour les tests qui n'ont pas besoin d'une vraie base.
- `faker_instance` — générateur de données réalistes.

Les fixtures spécifiques à AWS (création d'instances EC2, de buckets S3, de métriques CloudWatch) sont dans `tests/aws_tests/fixtures_ec2.py` et `tests/aws_tests/fixtures_s3.py`.

---

## 5. Exécution des tests

### 5.1 Prérequis

Installer les dépendances de test (déjà listées dans `CloudiagnozeApp/requirements.txt`) :

```bash
cd CloudiagnozeApp
pip install -r requirements.txt
```

Les paquets utilisés pour les tests sont : `pytest`, `pytest-asyncio`, `pytest-mock`, `pytest-cov`, `moto[ec2,s3,cloudwatch,sts]`, `faker`, `httpx`.

### 5.2 Lancer tous les tests

```bash
cd CloudiagnozeApp
pytest
```

La configuration `pytest.ini` active automatiquement le mode asyncio (`asyncio_mode = auto`), ce qui permet aux tests `async def test_...` de fonctionner sans décorateur explicite.

### 5.3 Lancer un sous-ensemble

```bash
# Uniquement les scanners AWS
pytest tests/aws_tests/

# Uniquement les tests d'intégration API
pytest tests/integration/

# Un seul fichier
pytest tests/integration/test_auth_endpoints.py

# Une seule classe
pytest tests/aws_tests/test_ec2_scanner.py::TestEC2ScannerBasic

# Un seul test
pytest tests/aws_tests/test_ec2_scanner.py::TestEC2ScannerBasic::test_scan_empty_region
```

### 5.4 Mode verbeux et couverture

```bash
# Verbeux (affiche chaque test)
pytest -v

# Couverture de code
pytest --cov=api --cov-report=term-missing
```

---

## 6. Limites connues

- Les tests d'intégration utilisent SQLite en mémoire ; quelques différences de comportement avec PostgreSQL (types, transactions) sont possibles mais restent marginales pour le périmètre testé.
- `moto` ne reproduit pas toujours fidèlement les métriques CloudWatch ; les tests vérifient donc la **structure** de la réponse plutôt que les valeurs exactes.
- Le script `cli_integration_test.py` nécessite un backend lancé manuellement ; il n'est pas exécuté par la suite `pytest`.

---

## 7. Améliorations futures

- Intégration des tests dans une pipeline CI (GitHub Actions) déclenchée à chaque push.
- Ajout d'un seuil minimum de couverture (par exemple 70 %) bloquant la fusion.
- Tests end-to-end automatisés avec un backend conteneurisé.

