# SmartHome

Application web simulant un système intelligent de domotique connectée. L’application SmartHome permettra de surveiller et piloter à distance différents équipements d’une maison (volets, portes, lumières, sonorisation), en fonction des conditions météorologiques, de la présence des occupants et de règles automatiques prédéfinies. 


## Table des matières



## Fonctionnalités



## Technologies utilisées



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


## Configuration

Fichier de configuration principal : settings.py

Variables importantes :
  

## Utilisation

  

## Contribuer

  

## Licence

...

# SmartHome (Tornado-only)

Cette version du projet SmartHome utilise uniquement **Tornado** (Django a été retiré).

Consultez la documentation complète ci-dessous pour l'architecture, l'installation, les routes et le déploiement.

## Architecture

### Stack technique
- Framework web: Tornado (asynchrone)
- Base de données: PostgreSQL (mêmes variables d'env que l'ancienne app Django)
- ORM: SQLAlchemy (async, asyncpg)
- Templates: Tornado templates
- Auth: cookies sécurisés + hachage compatible Django (PBKDF2-SHA256)

### Structure
```
smarthome/
	tornado_app/
		app.py
		config.py
		database.py
		models.py
		auth.py
		handlers/
			home.py
			accounts.py
			houses.py
		templates/
			base.html
			home.html
			login.html
			register.html
			house_list.html
			add_house.html
			add_room.html
static/
media/
.env
```

## Installation

1) Activez votre venv, installez les dépendances:
```bash
pip install -r requirements.txt
```

2) Configurez `.env` (exemple):
```env
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DEBUG=True
COOKIE_SECRET=change_me
PORT=8001
```

## Lancer
```bash
python -m smarthome.tornado_app.app
```

Ouvrez http://127.0.0.1:8001

## Notes
- Les fichiers et dossiers Django ont été supprimés.
- La DB est la même que précédemment (mêmes tables).
- Les fichiers statiques sont servis depuis `static/`, les médias depuis `media/`.

