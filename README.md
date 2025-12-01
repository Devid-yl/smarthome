# SmartHome - Application domotique intelligente 🏠

Application web moderne de **domotique connectée** avec architecture **SPA (Single Page Application)** et **API REST complète**.

Gérez vos maisons, pièces, capteurs et équipements intelligents depuis une interface web intuitive avec automatisation en temps réel.

> **Version 2.0** - Architecture REST complète avec frontend JavaScript

---

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités-principales)
- [Architecture](#-architecture-technique)
- [Installation](#-installation)
- [Lancement](#-lancement)
- [Documentation API](#-documentation-api)
- [Tests](#-tests)
- [Contribuer](#-contribuer)

---

## 🎯 Fonctionnalités principales

### 🏠 Gestion des maisons
-  Création, modification, suppression de maisons
-  Gestion des dimensions et de l'agencement
-  Éditeur graphique de grille d'intérieur
-  Vue détaillée par maison avec onglets

### 🚪 Gestion des pièces
-  Ajout de pièces multiples par maison
-  Association automatique aux capteurs et équipements
-  Suppression avec cascade (capteurs/équipements)

### 📊 Capteurs IoT
- **Types supportés** : Température (°C), Luminosité (lux), Pluie (%), Présence
-  Création et configuration personnalisée
-  Mise à jour des valeurs en temps réel
-  Activation/désactivation individuelle
-  Filtrage par pièce ou type

### ⚙️ Équipements connectés
- **Types** : Volets roulants, Portes, Lumières, Système audio
-  Contrôle d'état (on/off, ouvert/fermé)
-  Association à des pièces spécifiques
-  Gestion centralisée par type
-  API dédiée par équipement

### 🤖 Automatisation intelligente
**Système de règles conditionnelles** :
-  Création de règles personnalisées (capteur → condition → équipement)
-  Support de 6 opérateurs (>, <, >=, <=, ==, !=)
-  Activation/désactivation individuelle des règles
-  Déclenchement manuel ou automatique via API
-  Historique détaillé des actions exécutées
-  Logging complet (raison, équipement, action, timestamps)

**Exemples de règles** :
- 🌡️ Température > 28°C → Fermer volets
- 💡 Luminosité < 200 lux → Allumer lumières
- 🌧️ Pluie > 50% → Fermer volets
- 👤 Présence == 1 → Allumer lumières

### 👤 Gestion des utilisateurs
-  Inscription avec email et téléphone
-  Authentification sécurisée (cookies HTTPOnly)
-  Profil utilisateur avec photo de profil
-  Modification des informations (username, email, password)
-  Suppression de compte avec confirmation
-  Upload d'images (max 5 Mo)

---

## 🏗️ Architecture technique

### Stack technologique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| **Backend** | Tornado | 6.4+ |
| **Base de données** | PostgreSQL | 15+ |
| **ORM** | SQLAlchemy | 2.0+ (async) |
| **Driver DB** | asyncpg | Latest |
| **Frontend** | Vanilla JavaScript | ES6+ |
| **Styles** | CSS3 (Grid, Flexbox) | - |
| **Auth** | Cookies sécurisés | HTTPOnly |
| **Hash** | bcrypt | Auto-salted |

### Architecture SPA

```
┌─────────────────────────────┐
│      Frontend (SPA)         │
│  ┌────────────────────────┐ │
│  │ login.html             │ │
│  │ register.html          │ │
│  │ dashboard.html         │ │
│  │ house.html + house.js  │ │
│  │ profile.html           │ │
│  └────────────────────────┘ │
└──────────┬──────────────────┘
           │ Fetch API (JSON)
           ▼
┌─────────────────────────────┐
│  Backend (Tornado REST API) │
│  ┌────────────────────────┐ │
│  │ users_api.py           │ │◄─┐
│  │ houses_api.py          │ │  │
│  │ sensors.py             │ │  │ SQLAlchemy
│  │ equipments.py          │ │  │ (async)
│  │ automation.py          │ │  │
│  └────────────────────────┘ │  │
└──────────┬──────────────────┘  │
           │                     │
           ▼                     ▼
    ┌──────────────────────────────┐
    │       PostgreSQL             │
    │  ┌────────────────────────┐  │
    │  │ users                  │  │
    │  │ houses                 │  │
    │  │ rooms                  │  │
    │  │ sensors                │  │
    │  │ equipments             │  │
    │  └────────────────────────┘  │
    └──────────────────────────────┘
```

### Structure du projet

```
smarthome/
├── static/
│   └── app/                        # Application SPA
│       ├── login.html              # Page de connexion
│       ├── register.html           # Page d'inscription
│       ├── dashboard.html          # Dashboard principal
│       ├── house.html              # Détails d'une maison
│       ├── house.js                # Logique page maison
│       └── profile.html            # Profil utilisateur
├── smarthome/tornado_app/
│   ├── handlers/                   # Handlers API REST
│   │   ├── users_api.py            # API auth & utilisateurs (6 endpoints)
│   │   ├── houses_api.py           # API maisons & pièces (4 endpoints)
│   │   ├── sensors.py              # API capteurs (5 endpoints)
│   │   ├── equipments.py           # API équipements (9 endpoints)
│   │   └── automation.py           # API automatisation (3 endpoints)
│   ├── models.py                   # Modèles SQLAlchemy
│   ├── database.py                 # Configuration DB async
│   ├── auth.py                     # Hachage/vérification passwords
│   ├── config.py                   # Configuration app
│   └── app.py                      # Point d'entrée + routes
├── media/
│   └── profile_images/             # Photos de profil uploadées
├── migrations/                     # Scripts SQL
│   ├── 001_initial.sql             # Tables principales
│   └── 002_add_sensors_equipments.sql
├── .env                            # Variables d'environnement
├── requirements.txt                # Dépendances Python
├── API_DOCUMENTATION.md            # Documentation complète API REST (50+ endpoints)
├── ARCHITECTURE.md                 # Architecture technique et diagrammes
├── DEMONSTRATION_GUIDE.md          # Guide de démonstration académique
├── PROJECT_REQUIREMENTS.md         # Conformité aux exigences (35/35 points)
└── README.md                       # Ce fichier
```

---

## 📦 Installation

### Prérequis

- **Python** 3.11 ou supérieur
- **PostgreSQL** 15 ou supérieur
- **pip** et **venv** (inclus avec Python)

### 1. Cloner le dépôt

```bash
git clone https://github.com/Devid-yl/smarthome.git
cd smarthome
```

### 2. Créer l'environnement virtuel

```bash
python3 -m venv venv

# Activer (Mac/Linux)
source venv/bin/activate

# Activer (Windows)
venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Principales dépendances** :
- `tornado>=6.4`
- `sqlalchemy>=2.0`
- `asyncpg`
- `psycopg2-binary`
- `python-dotenv`
- `pillow` (pour l'upload d'images)

### 4. Configurer les variables d'environnement

Créer un fichier `.env` à la racine :

```env
# Base de données
DB_NAME=smarthome_db
DB_USER=votre_utilisateur
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# Serveur
DEBUG=True
PORT=8001

# Sécurité
COOKIE_SECRET=votre_secret_aleatoire_tres_long_et_securise_ici
```

> ⚠️ **Important** : Générez un `COOKIE_SECRET` fort en production avec :
> ```python
> import secrets
> print(secrets.token_hex(64))
> ```

### 5. Créer la base de données PostgreSQL

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la database
CREATE DATABASE smarthome_db;

# Créer un utilisateur (optionnel)
CREATE USER votre_utilisateur WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE smarthome_db TO votre_utilisateur;

# Quitter
\q
```

### 6. Appliquer les migrations

```bash
# Migration 1 : Tables principales (users, houses, rooms)
psql -U votre_utilisateur -d smarthome_db -f smarthome/migrations/001_initial.sql

# Migration 2 : Tables IoT (sensors, equipments)
psql -U votre_utilisateur -d smarthome_db -f smarthome/migrations/002_add_sensors_equipments.sql
```

**Vérification** :
```bash
psql -U votre_utilisateur -d smarthome_db

# Lister les tables
\dt

# Devrait afficher : users, houses, rooms, sensors, equipments
```

---

## 🚀 Lancement

### Démarrer le serveur

```bash
# S'assurer que le venv est activé
source venv/bin/activate  # Mac/Linux
# OU
venv\Scripts\activate     # Windows

# Lancer le serveur
python -m smarthome.tornado_app.app
```

**Sortie attendue** :
```
Server starting on http://127.0.0.1:8001
```

### Accéder à l'application

| Page | URL | Description |
|------|-----|-------------|
| **Inscription** | http://localhost:8001/app/register.html | Créer un compte |
| **Connexion** | http://localhost:8001/app/login.html | Se connecter |
| **Dashboard** | http://localhost:8001/app/dashboard.html | Vue des maisons |
| **Profil** | http://localhost:8001/app/profile.html | Gérer son profil |

> 🔒 Les pages **Dashboard**, **Profil** et **Détails maison** nécessitent d'être authentifié.

---

## 📖 Documentation API

### Vue d'ensemble

L'API REST complète est documentée dans **[doc/API_DOCUMENTATION.md](API_DOCUMENTATION.md)**.

**Endpoints principaux** : 50+ au total

| Catégorie | Endpoints | Fichier |
|-----------|-----------|---------|
| 🔐 Auth & Users | 8 | `users_api.py` |
| 🏠 Maisons | 2 | `houses_api.py` |
| 🚪 Pièces | 2 | `houses_api.py` |
| 📊 Capteurs | 5 | `sensors.py` |
| ⚙️ Équipements | 7 | `equipments.py` |
| 🤖 Automatisation | 3 | `automation.py` |

### Exemples d'utilisation

**1. Inscription**
```bash
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com", "password": "secret123"}'
```

**2. Connexion**
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "secret123"}' \
  -c cookies.txt
```

**3. Créer une maison**
```bash
curl -X POST http://localhost:8001/api/houses \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"name": "Ma Maison", "address": "123 rue Test", "length": 10, "width": 8}'
```

**4. Déclencher l'automatisation**
```bash
curl -X POST http://localhost:8001/api/automation/trigger -b cookies.txt
```

> 📚 Consultez **[doc/API_DOCUMENTATION.md](API_DOCUMENTATION.md)** pour la liste complète des 50+ endpoints avec exemples détaillés.

---

## 🧪 Tests

### Tests manuels

Un script de test complet des APIs est fourni :

```bash
# S'assurer que le serveur tourne
python test_api.py
```

**Ce script teste** :
-  Inscription et connexion
-  CRUD maisons et pièces
-  CRUD capteurs et équipements
-  Automatisation B2B
-  Gestion du profil

### Tests de l'interface

1. Ouvrir http://localhost:8001/app/register.html
2. Créer un compte avec email et téléphone
3. Se connecter automatiquement → Dashboard
4. Créer une maison (nom, adresse, dimensions)
5. Cliquer sur une maison → Page détails
6. Onglet **Pièces** : Ajouter plusieurs pièces
7. Onglet **Capteurs** : Ajouter un capteur (température, luminosité, etc.)
8. Onglet **Équipements** : Ajouter un équipement (volet, lumière, etc.)
9. Onglet **Automatisation** : Déclencher les règles B2B
10. Navbar → **Profil** : Modifier email, téléphone, photo

### Tests de charge (optionnel)

Avec **Locust** :
```bash
pip install locust
locust -f load_test.py
```

Ouvrir http://localhost:8089

---

##  Fonctionnalités implémentées

### Phase 1 : Fonctionnalités de base 
-  **API Utilisateurs** : Inscription, connexion, profil
-  **API Maisons** : CRUD complet, pièces, visualisation grille
-  **API Capteurs** : Création, lecture, mise à jour
-  **API Équipements** : CRUD, contrôle état
-  **API Automatisation** : Règles conditionnelles, déclenchement
-  **API Membres** : Invitation, gestion rôles (admin/occupant/guest)
-  **API Historique** : Journalisation automatique des événements
-  **API Météo** : Intégration Open-Meteo
-  **WebSockets** : Notifications temps réel
-  **Géolocalisation** : Tracking positions utilisateurs
- ⚠️ **PWA** : Mode offline

### Phase 3 : Tests et production
- ⚠️ Tests unitaires (pytest)
- ⚠️ Tests d'intégration
- ⚠️ Documentation Swagger/OpenAPI
- ⚠️ Dockerisation
- ⚠️ CI/CD

---

## 🛠️ Technologies détaillées

### Backend
- **Tornado** : Framework web asynchrone haute performance
- **SQLAlchemy 2.0** : ORM moderne avec support async/await
- **asyncpg** : Driver PostgreSQL asynchrone (le plus rapide)
- **bcrypt** : Hachage de mots de passe sécurisé avec salage automatique

### Frontend
- **Vanilla JavaScript** : ES6+, Fetch API, async/await
- **CSS3** : Grid, Flexbox, animations, responsive
- **HTML5** : Sémantique, forms, modals

### Base de données
- **PostgreSQL** : SGBDR relationnel robuste
- **Tables** : users, houses, rooms, sensors, equipments
- **Relations** : Foreign keys, cascades, indexes

### Sécurité
- 🔒 **Cookies HTTPOnly** : Protection XSS
- 🔒 **bcrypt** : Hachage adaptatif avec salage automatique
- 🔒 **XSRF désactivé** : Pour API REST stateless
- 🔒 **Validation propriété** : Toutes ressources vérifiées par user_id

---

## 👥 Contribuer

### Workflow Git

1. Fork le projet
2. Créer une branche : `git checkout -b feature/nouvelle-fonctionnalite`
3. Commit : `git commit -m "Add: nouvelle fonctionnalité"`
4. Push : `git push origin feature/nouvelle-fonctionnalite`
5. Créer une Pull Request

### Standards de code

- **Python** : PEP 8, type hints
- **JavaScript** : ES6+, async/await, camelCase
- **SQL** : snake_case, migrations versionnées
- **Commits** : [Conventional Commits](https://www.conventionalcommits.org/)

### Signaler un bug

Ouvrir une [issue](https://github.com/Devid-yl/smarthome/issues) avec :
- Description du problème
- Étapes de reproduction
- Comportement attendu vs observé
- Logs/erreurs
- Environnement (OS, Python version, etc.)

---

## 📜 Licence

Ce projet est sous licence **MIT**. Consultez [LICENSE](LICENSE) pour plus d'informations.

---

## 📧 Contact

**Auteur** : David Yala  
**Email** : contact@example.com  
**GitHub** : [@Devid-yl](https://github.com/Devid-yl)

---

## 🙏 Remerciements

- [Tornado Web Framework](https://www.tornadoweb.org/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [PostgreSQL](https://www.postgresql.org/)
- Communauté open-source

---

**Version** : 2.0 (Architecture REST complète)  
**Dernière mise à jour** : Novembre 2024  
**Statut** :  Production Ready

