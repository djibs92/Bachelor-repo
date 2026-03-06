# CloudDiagnoze

Plateforme SaaS de scan et d'analyse d'infrastructure AWS (EC2, S3, VPC, RDS).

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et démarré
- Credentials AWS avec les permissions nécessaires (voir ci-dessous)

## Démarrage rapide

### 1. Cloner le dépôt

```bash
git clone <URL_DU_REPO>
cd Bachelor_Exam
```

### 2. Configurer l'environnement

```bash
cp .env.example .env
```

Ouvrir `.env` et remplir les valeurs :

```env
# Base de données — choisir des mots de passe forts
DB_ROOT_PASSWORD=un_mot_de_passe_root
DB_PASSWORD=un_mot_de_passe_user

# JWT — générer avec : python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=votre_cle_secrete_generee

# AWS — vos credentials IAM
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=eu-west-1
```

### 3. Lancer l'application

```bash
docker compose up -d --build
```

L'application démarre en ~30 secondes. Accéder à : **http://localhost**

> **Note Windows** : Si Docker Desktop ne démarre pas, vérifier que WSL2 est activé.

## Permissions IAM requises

L'utilisateur AWS doit avoir les permissions suivantes :

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "s3:List*", "s3:GetBucket*",
        "rds:Describe*",
        "cloudwatch:GetMetricStatistics",
        "sts:AssumeRole"
      ],
      "Resource": "*"
    }
  ]
}
```

## Utilisation

1. Ouvrir **http://localhost** et créer un compte
2. Dans **Config Scan**, saisir votre **Role ARN** AWS (ex: `arn:aws:iam::123456789012:role/CloudDiagnozeRole`)
3. Sélectionner les services à scanner (EC2, S3, VPC, RDS) et les régions
4. Lancer le scan — les résultats apparaissent dans les dashboards

## Commandes utiles

```bash
# Voir les logs
docker compose logs -f backend

# Arrêter (données conservées)
docker compose down

# Reset complet (supprime toutes les données)
docker compose down -v && docker compose up -d --build
```

## Architecture

```
Nginx :80  →  /api/*  →  FastAPI :8000  →  boto3  →  AWS
                               ↓
                           MariaDB :3306
```
