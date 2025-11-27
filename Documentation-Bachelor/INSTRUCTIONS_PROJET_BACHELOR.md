# PROJET BACHELOR - EFREI TS

## Instructions complètes pour la réalisation du projet

---

## 1. RÉSUMÉ DES OBLIGATIONS

### 1.1 Analyse des besoins et cahier des charges
- **OBLIGATION** : Analyser les besoins des futurs utilisateurs du logiciel
- **OBLIGATION** : Former un cahier des charges
- **OBLIGATION** : Intégrer ce cahier des charges au journal de projet
- **OBLIGATION** : Rédiger le journal de projet dans la langue de la pentite albion (anglais)

### 1.2 Maquettage
- **OBLIGATION** : Maquetter le logiciel
- **OBLIGATION** : Intégrer cette maquette au journal de projet

### 1.3 Architecture logicielle (UML)
- **OBLIGATION** : Définir l'architecture logicielle du projet
- **OBLIGATION** : Intégrer cette définition au journal de projet
- **OBLIGATION** : Utiliser UML pour cette définition

#### 1.3.1 Découpage Interface utilisateur / Modules métiers
- **OBLIGATION** : Le logiciel doit présenter un découpage Interface utilisateur / Modules métiers
- **SI** ce découpage architectural implique une séparation logicielle :
  - **OBLIGATION** : Documenter la méthode de communication (typiquement MVC)

#### 1.3.2 Conception Orientée par le Domaine (Domain-Driven Design)
- **OBLIGATION** : Les modules métiers doivent être conçus en ayant les principes de la Conception Orientée par le Domaine en tête
- **OBLIGATION** : Assurer un niveau de sécurité total

#### 1.3.3 Base de données structurée
- **OBLIGATION** : Les modules métiers doivent exploiter des données enregistrées de manière structurée
- **RECOMMANDATION FORTE** : Employer une base de données SQL pour augmenter les chances de succès et limiter l'exotisme

#### 1.3.4 Documentation des formats de fichiers
- **OBLIGATION** : Documenter les éventuels formats de fichiers employés

### 1.4 Tests automatiques
- **OBLIGATION** : Le projet doit comporter des tests automatiques
- **OBLIGATION** : Incorporer à votre journal de projet un plan de test

### 1.5 Installation et configuration
- **OBLIGATION** : Être capable d'installer et configurer l'environnement de travail
- **OBLIGATION** : Permettre le travail sur le projet bachelor en toute autonomie

### 1.6 Déploiement
- **OBLIGATION** : Le projet doit pouvoir être déployé en suivant le plan de déploiement contenu dans le journal de projet
- **OBLIGATION** : Mise en production de manière automatique, idéalement
- Le déploiement doit inclure :
  - Installation des dépendances
  - Installation du logiciel
  - Fichier de configuration documenté OU interface de configuration intégrée

### 1.7 Mise à jour du système
- **OBLIGATION** : Le projet doit comporter une procédure ou mécanisme de mise à jour du système sous-jacent, des dépendances et du logiciel lui-même
- **OBLIGATION** : Ce mécanisme ou procédure doit être documenté dans le journal de projet

### 1.8 Méthode Agile SCRUM
- **OBLIGATION** : Être capable de travailler en équipe
- **OBLIGATION** : Participer à la gestion du projet en utilisant la méthode agile SCRUM

---

## 2. EXIGENCES SELON LE TYPE DE PROJET

**RÈGLE GÉNÉRALE** : Quel que soit le projet, celui-ci doit comporter une gestion de contenu dynamique.

### 2.1 Site Web

**Technologies requises :**
- Technologie d'interface utilisateur : HTML/CSS
- Langage de programmation côté interface utilisateur : JavaScript
- Communication avec modules métiers : Interface logicielle (REST, AJAX)
- Langage de programmation côté module métier : PHP
- Base de données : MariaDB

**Obligations spécifiques :**
- Disposer d'un script d'installation
- Disposer d'une interface de configuration de base intégrée
- Intégrer un système de mise à jour via un compte administrateur

### 2.2 Application Mobile

**Technologies requises :**
- Technologie d'interface utilisateur : Jetpack compose OU XML+AndroidViews
- Langages de programmation :
  - Pour la gestion de l'interface : Un langage
  - Pour les modules métiers : Un autre langage
  - **IMPORTANT** : Les deux doivent être clairement identifiés et séparés (Kotlin)
- Base de données : SQLite

**Obligations spécifiques :**
- Disposer d'un script d'installation transparent
- Système de déploiement de mise à jour automatique lancé par le système d'installation
- Le système de déploiement de mise à jour automatique doit être géré par ce même système

### 2.3 Logiciel de Bureau

**Technologies requises :**
- Technologie d'interface utilisateur : Winform, WPF ou Qt
- Langages de programmation :
  - Pour la gestion de l'interface : Un langage
  - Pour les modules métiers : Un autre langage
  - **IMPORTANT** : Les deux doivent être clairement identifiés et séparés (C, C++, C#, VB)
- Base de données : SQLite
- Fichiers structurés : JSON, XML, INI, Dabsic

**Obligations spécifiques :**
- Disposer d'un logiciel d'installation
- Le logiciel intègre un système de mise à jour à proposition automatique

---

## 3. RÉSUMÉ DU PASSAGE EN JURY

### 3.1 Structure de la soutenance

**Présentation du projet : 40 minutes**
- Durant cette phase, vous déroulez votre diaporama

**Entretien technique : 45 minutes**
- Durant cette phase, le jury vous questionne

**Questionnaire professionnel : 30 minutes**
- En présence d'un surveillant
- Le questionnaire comprend :
  - Deux questions fermées à choix unique posées en français
  - Deux questions ouvertes posées en anglais amenant une réponse à formuler en anglais

**Entretien final : 20 minutes**
- Échange final avec le jury

### 3.2 Matériel requis pour la soutenance

**OBLIGATION** : Disposer d'un diaporama préparé à l'avance
**OBLIGATION** : Disposer d'une machine permettant de faire la démonstration du projet
**OBLIGATION** : Chaque jury devra disposer d'un exemplaire du journal de projet

---

## 4. DÉROULÉ RECOMMANDÉ DE LA PRÉSENTATION

### Phase 1 : Présentation du projet (Diaporama)

**1. En anglais : Expliquer la nature du projet**

**2. Présenter le cahier des charges, abordez :**
- 2.1 - Charte graphique (Logo, couleur, police)
- 2.2 - Maquette (Zoning, Wireframe), exploitant Figma
- 2.3 - Diagrammes des cas d'utilisation

### Phase 2 : Entretien technique (Diaporama)

**3. Présenter les modules métiers, abordez :**
- 3.1 - Présenter les technologies utilisées et justifier les choix
- 3.2 - Diagrammes de classes
- 3.3 - Diagrammes de base de données
- 3.4 - Diagrammes de séquence
- 3.5 - Diagrammes de déploiement
- 3.6 - Diagrammes de cas d'utilisations
- 3.7 - Diagrammes d'état
- 3.8 - Diagrammes d'activités

**4. Faire la démonstration du projet**
- 4.1 - Exécuter des scénarios de test et de démonstration préparés à l'avance
- 4.2 - Donner la preuve des relations entre interfaces, modules métiers et base de données avec des manipulations manuelles
- 4.3 - Si pertinent : Aborder les sujets du SEO, du SOA et de l'analyse automatique de site
- 4.4 - Faire la démonstration de conception réactive (responsive design) du logiciel et expliquer comment vous avez procédé

**5. Montrer le code source**

Placer des captures d'écrans bien choisies dans le diaporama et avoir l'éditeur déjà ouvert sur les fichiers que vous souhaitez manipuler plus en détail.

- 5.1 - Montrer la connexion avec la base de données et les requêtes
- 5.2 - Montrer comment l'administration du logiciel est faite, si cela est pertinent
- 5.3 - Montrer la manière dont vous sécurisez le logiciel : chiffrement, rôles et autorisations des utilisateurs, contre-mesure contre les injections, digestion des mots de passe, etc.
- 5.4 - Montrer le rapport entre l'organisation du code et la conception du logiciel afin de démontrer que celle-ci est réelle
- 5.5 - Montrer la méthode de test et les jeux de test automatique
- 5.6 - Aborder le sujet du RGPD et la manière dont vous assurez son respect

**6. Aborder la méthode de maintenance, de mise en production, de mise à jour**
- 6.1 - Démontrer que les tests unitaires conditionnent le déploiement
- 6.2 - Montrer la manière dont le logiciel est déployé
- 6.3 - Mettre en avant le mécanisme de mise à jour intégré et son fonctionnement
- 6.4 - Parler de la manière dont vous assurez la sécurité du logiciel à l'avenir (Recommandations de l'ANSSI, etc.)
- 6.5 - Plus généralement, parler de la manière dont vous faites de la veille logicielle

**7. Aborder les raisons qui vous ont fait choisir l'informatique**

---

## 5. CONSIGNES IMPORTANTES

### 5.1 Attitude professionnelle
- **EXIGENCE** : Être professionnel
- **EXIGENCE** : Faire la démonstration des compétences
- **IMPORTANT** : Même si les compétences ne sont pas entièrement reflétées par le projet, vous avez le droit de parler de vos autres projets
- **RAPPEL** : Le jury est présent pour vous évaluer

### 5.2 Format des livrables
- **Journal de projet** : En anglais
- **Diaporama** : Préparé à l'avance
- **Exemplaires du journal** : Un par membre du jury

### 5.3 Évaluation
Le jury évalue vos compétences techniques, votre capacité à communiquer et votre professionnalisme tout au long de la soutenance.

---

## CHECKLIST DE VALIDATION

### Documentation (Journal de projet)
- [ ] Analyse des besoins des utilisateurs
- [ ] Cahier des charges complet
- [ ] Maquettes du logiciel
- [ ] Architecture logicielle en UML
- [ ] Documentation du découpage Interface/Modules
- [ ] Documentation de la méthode de communication (si applicable)
- [ ] Justification de l'utilisation d'une base de données SQL
- [ ] Documentation des formats de fichiers
- [ ] Plan de test
- [ ] Plan de déploiement
- [ ] Procédure de mise à jour
- [ ] Tout rédigé en anglais

### Architecture technique
- [ ] Découpage Interface utilisateur / Modules métiers
- [ ] Conception orientée domaine (DDD)
- [ ] Sécurité totale assurée
- [ ] Base de données structurée (SQL recommandé)
- [ ] Gestion de contenu dynamique

### Code et tests
- [ ] Tests automatiques implémentés
- [ ] Code organisé selon l'architecture définie
- [ ] Méthodes de sécurisation (chiffrement, rôles, anti-injection, etc.)
- [ ] Respect du RGPD

### Déploiement
- [ ] Script/système d'installation fonctionnel
- [ ] Configuration documentée ou interface de configuration
- [ ] Mécanisme de mise à jour automatique
- [ ] Tests unitaires conditionnant le déploiement

### Méthode de travail
- [ ] Utilisation de SCRUM
- [ ] Travail en équipe démontrable

### Soutenance
- [ ] Diaporama préparé
- [ ] Machine de démonstration prête
- [ ] Exemplaires du journal de projet (un par jury)
- [ ] Scénarios de test préparés
- [ ] Éditeur ouvert sur les fichiers clés
- [ ] Présentation de 40 minutes prête (avec partie en anglais)

---

**Date de création du document** : 2025-10-05
**Source** : Document numérisé.pdf - EFREI TS Projet Bachelor
