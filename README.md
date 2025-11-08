# SmartHome

Application web simulant un système intelligent de domotique connectée. L’application SmartHome permettra de surveiller et piloter à distance différents équipements d’une maison (volets, portes, lumières, sonorisation), en fonction des conditions météorologiques, de la présence des occupants et de règles automatiques prédéfinies. 

---

## Table des matières

- [Fonctionnalités](#fonctionnalités)  
- [Technologies utilisées](#technologies-utilisées)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Utilisation](#utilisation)  
- [Contribuer](#contribuer)  
- [Licence](#licence)  

---

## Fonctionnalités

- Gestion multi-utilisateurs et authentification sécurisée  
- Gestion des maisons, pièces, capteurs et équipements  
- Création et exécution de scénarios d’automatisation  
- API REST pour la récupération et modification des données  
- Notifications et mises à jour en temps réel via WebSockets  
- Intégration optionnelle avec les API météo  

---

## Technologies utilisées

- **Backend :** Python (Django)  
- **Frontend :** HTML, CSS, JavaScript  
- **Base de données :** PostgreSQL
- **Communication temps réel :** WebSocket  
- **Gestion de version :** Git / GitHub  

---

## Installation

1. Cloner le dépôt :  
```
git clone https://github.com/Devid-yl/smarthome.git
cd smarthome
```

2. Créer un environnement virtuel Python :
```
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

3. Installer les dépendances :
```
pip install -r requirements.txt
```

4. Appliquer les migrations de la base de données :
```
python manage.py migrate
```

5. Lancer le serveur de développement :
```
python manage.py runserver
```

---

## Configuration

Fichier de configuration principal : settings.py

Variables importantes :
- DATABASE_URL : URL de connexion à la base de données
- SECRET_KEY : clé secrète pour Django
- DEBUG : activer/désactiver le mode debug
  
---

## Utilisation

- Accéder à l’interface web via http://127.0.0.1:8000/
- Créer des utilisateurs, maisons et équipements
- Définir des scénarios d’automatisation
- Consulter les données en temps réel
  
---

## Contribuer

- Fork le projet
- Créez une branche : git checkout -b feature/ma-fonctionnalité
- Committez vos changements : git commit -m "Description de la fonctionnalité"
- Poussez la branche : git push origin feature/ma-fonctionnalité
- Ouvrez une Pull Request
  
---

## Licence

...

