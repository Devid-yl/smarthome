# SmartHome - Architecture Technique

## 📐 Vue d'Ensemble

Document technique détaillant l'architecture complète du système SmartHome, les choix techniques, les flux de données, et les patterns utilisés.

**Version** : 3.0  
**Date** : 30 novembre 2024  
**Auteur** : David Yala

---

## 🏗️ Architecture Globale

### Diagramme de Haut Niveau

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Browser   │  │  Browser   │  │  REST API  │           │
│  │  (HTML/CSS/│  │  (WebSocket│  │  Client    │           │
│  │   JS)      │  │   Client)  │  │  (JWT)     │           │
│  └─────┬──────┘  └──────┬─────┘  └──────┬─────┘           │
│        │                │                │                  │
└────────┼────────────────┼────────────────┼──────────────────┘
         │                │                │
         │ HTTP/REST      │ WebSocket      │ HTTP + JWT
         │                │                │
┌────────▼────────────────▼────────────────▼──────────────────┐
│                 APPLICATION LAYER                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Tornado 6.4+ Web Server (Async)              │   │
│  │                                                       │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│  │  │  Handlers   │  │  WebSocket   │  │    JWT     │ │   │
│  │  │  (REST API) │  │   Manager    │  │    Auth    │ │   │
│  │  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘ │   │
│  │         │                │                 │        │   │
│  │  ┌──────▼────────────────▼─────────────────▼──────┐ │   │
│  │  │          Business Logic Layer                  │ │   │
│  │  │  - Automation Engine (B2B)                    │ │   │
│  │  │  - Permissions Manager                        │ │   │
│  │  │  - Event Logger                               │ │   │
│  │  └───────────────────────┬────────────────────────┘ │   │
│  │                          │                          │   │
│  │  ┌───────────────────────▼────────────────────────┐ │   │
│  │  │          Data Access Layer (ORM)              │ │   │
│  │  │    SQLAlchemy 2.0 Async + asyncpg            │ │   │
│  │  └───────────────────────┬────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────────┼──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│                    DATABASE LAYER                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         PostgreSQL 15+ (JSONB support)                 │  │
│  │                                                        │  │
│  │  ┌──────┐ ┌───────┐ ┌────────┐ ┌─────────────────┐  │  │
│  │  │users │ │houses │ │sensors │ │automation_rules │  │  │
│  │  └──────┘ └───────┘ └────────┘ └─────────────────┘  │  │
│  │  ┌──────────┐ ┌────────────┐ ┌────────────────┐    │  │
│  │  │equipments│ │house_members│ │event_history   │    │  │
│  │  └──────────┘ └────────────┘ └────────────────┘    │  │
│  │  ┌────────┐ ┌───────────────┐                      │  │
│  │  │rooms   │ │user_positions │                      │  │
│  │  └────────┘ └───────────────┘                      │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  EXTERNAL SERVICES                           │
│  ┌───────────────────┐      ┌──────────────────────┐        │
│  │  Open-Meteo API   │      │  Nominatim Geocoding │        │
│  │  (Weather Data)   │      │  (OpenStreetMap)     │        │
│  └───────────────────┘      └──────────────────────┘        │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Stack Technologique

### Backend

| Composant | Version | Rôle | Justification |
|-----------|---------|------|---------------|
| **Python** | 3.14.0 | Langage | Moderne, async/await natif |
| **Tornado** | 6.4+ | Web Framework | Performance async, WebSocket natif |
| **SQLAlchemy** | 2.0+ | ORM | Async support, type-safe, migrations |
| **asyncpg** | Latest | DB Driver | Driver PostgreSQL le plus rapide |
| **PostgreSQL** | 15+ | SGBD | Robuste, JSONB, contraintes |
| **bcrypt** | Latest | Hash passwords | Standard industrie, salt auto |
| **PyJWT** | 2.8+ | JWT tokens | Authentification stateless |

### Frontend

| Composant | Version | Rôle |
|-----------|---------|------|
| **HTML5** | - | Structure |
| **CSS3** | - | Styles (Grid, Flexbox) |
| **JavaScript** | ES6+ | Logique (Vanilla, pas de framework) |
| **WebSocket API** | Native | Temps réel |

### Outils de Développement

| Outil | Usage |
|-------|-------|
| **Git** | Versioning (GitHub) |
| **pgAdmin** | Administration PostgreSQL |
| **VSCode** | IDE avec extensions Python |
| **Postman** | Tests API REST |

---

## 📦 Structure du Projet

```
smarthome/
├── README.md                          # Documentation générale
├── PROJECT_REQUIREMENTS.md            # Conformité académique (35 points)
├── API_DOCUMENTATION.md               # Documentation API complète
├── DEMONSTRATION_GUIDE.md             # Guide de présentation
├── ARCHITECTURE.md                    # Ce fichier
├── BACKEND_DOCUMENTATION_STATUS.md    # État traduction EN
├── requirements.txt                   # Dépendances Python
├── server.pid                         # PID du serveur
│
├── smarthome/                         # Package principal
│   ├── __init__.py
│   └── tornado_app/                   # Application Tornado
│       ├── __init__.py
│       ├── app.py                     # Point d'entrée + routes
│       ├── config.py                  # Configuration (secret key, etc.)
│       ├── database.py                # SQLAlchemy setup async
│       ├── models.py                  # Modèles ORM (9 tables)
│       ├── auth.py                    # Bcrypt helpers
│       ├── jwt_auth.py                # JWT generation/validation
│       │
│       ├── handlers/                  # Request handlers
│       │   ├── __init__.py
│       │   ├── base.py                # BaseAPIHandler
│       │   ├── users_api.py           # User CRUD + auth
│       │   ├── houses_api.py          # House + Room CRUD
│       │   ├── sensors.py             # Sensor CRUD + updates
│       │   ├── equipments.py          # Equipment CRUD + control
│       │   ├── automation_rules.py    # Automation rules CRUD
│       │   ├── automation.py          # Automation engine (B2B)
│       │   ├── house_members.py       # Members + invitations
│       │   ├── event_history.py       # Event logging + cleanup
│       │   ├── user_positions.py      # Position tracking
│       │   ├── weather.py             # Weather API integration
│       │   ├── grid_editor.py         # Grid manipulation
│       │   └── websocket.py           # WebSocket handler
│       │
│       ├── services/                  # External services
│       │   ├── __init__.py
│       │   └── weather_service.py     # Open-Meteo + Nominatim
│       │
│       ├── utils/                     # Utilities
│       │   ├── __init__.py
│       │   ├── permissions.py         # Permission checks
│       │   └── grid_layers.py         # Grid format helpers
│       │
│       └── templates/                 # Jinja2 templates (minimal)
│           ├── base.html
│           └── edit_house_inside.html
│
├── static/                            # Frontend assets
│   ├── main.css                       # CSS principal
│   │
│   ├── app/                           # Single Page Components
│   │   ├── login.html                 # Page connexion
│   │   ├── register.html              # Page inscription
│   │   ├── dashboard.html             # Dashboard maisons
│   │   ├── profile.html               # Page profil
│   │   ├── house.html                 # Page maison (principale)
│   │   ├── house.js                   # Logique maison
│   │   ├── history.html               # Page historique
│   │   ├── members.html               # Page membres
│   │   ├── invitations.html           # Page invitations
│   │   ├── realtime.js                # WebSocket client
│   │   └── weather.js                 # Weather widget
│   │
│   └── css/                           # Styles par page
│       ├── auth.css                   # Login/Register
│       ├── dashboard.css              # Dashboard
│       ├── house.css                  # House page
│       ├── profile.css                # Profile
│       └── grid-editor.css            # Grid editor
│
└── media/                             # Uploads utilisateur
    └── profile_images/                # Photos de profil
```

---

## 🗄️ Modèle de Données

### Schéma Entité-Association

```
┌──────────────────┐
│      users       │
│──────────────────│
│ PK id            │
│    username      │──┐
│    email         │  │
│    password      │  │ 1
│    is_active     │  │
│    date_joined   │  │
│    profile_image │  │
│    phone_number  │  │
└──────────────────┘  │
                      │
                      │ owns
                      │
                      │
                    N │
┌─────────────────────▼────────────────────────┐
│                  houses                      │
│──────────────────────────────────────────────│
│ PK id                                        │
│ FK user_id → users.id (owner)                │
│    name                                      │
│    address                                   │
│    length, width                             │
│    grid (JSONB) ← Format hybride             │
└────┬──────────────────────────────────┬─────┘
     │                                   │
     │ 1                                 │ 1
     │                                   │
   N │                                 N │
┌────▼────────────┐            ┌────────▼──────────┐
│     rooms       │            │  house_members    │
│─────────────────│            │───────────────────│
│ PK id           │            │ PK id             │
│ FK house_id     │            │ FK house_id       │
│    name         │            │ FK user_id        │
└─────────────────┘            │ FK invited_by     │
                               │    role           │
     ┌─────────────────────────┤    status         │
     │                         │    invited_at     │
     │ 1                       │    accepted_at    │
     │                         └───────────────────┘
   N │
┌────▼────────────────┐
│      sensors        │
│─────────────────────│
│ PK id               │
│ FK house_id         │
│ FK room_id (NULL)   │
│    name             │
│    type             │ ← temperature | luminosity | rain | presence
│    value (Float)    │
│    unit             │
│    is_active        │
│    last_update      │
└─────────────────────┘

┌─────────────────────┐
│    equipments       │
│─────────────────────│
│ PK id               │
│ FK house_id         │
│ FK room_id (NULL)   │
│    name             │
│    type             │ ← shutter | door | light | sound_system
│    state            │
│    is_active        │
│    allowed_roles    │ ← JSONB: ["admin"] ou NULL
│    last_update      │
└─────────────────────┘

┌───────────────────────────┐
│    automation_rules       │
│───────────────────────────│
│ PK id                     │
│ FK house_id               │
│ FK sensor_id              │
│ FK equipment_id           │
│    name                   │
│    description            │
│    condition_operator     │ ← > < >= <= == !=
│    condition_value        │
│    action_state           │
│    is_active              │
│    created_at             │
│    last_triggered         │
└───────────────────────────┘

┌───────────────────────────┐
│     event_history         │
│───────────────────────────│
│ PK id                     │
│ FK house_id               │
│ FK user_id (NULL)         │
│    event_type             │ ← equipment_control | sensor_reading
│    entity_type            │    | automation_triggered | member_action
│    entity_id              │    | house_modified
│    description            │
│    event_metadata (JSONB) │
│    created_at             │
│    ip_address             │
└───────────────────────────┘

┌───────────────────────────┐
│     user_positions        │
│───────────────────────────│
│ PK id                     │
│ FK house_id               │
│ FK user_id                │
│    x, y                   │ ← Coordonnées dans la grille
│    last_update            │
└───────────────────────────┘
```

### Contraintes d'Intégrité

| Table | Foreign Key | Action |
|-------|-------------|--------|
| houses | user_id → users.id | CASCADE DELETE |
| rooms | house_id → houses.id | CASCADE DELETE |
| sensors | house_id → houses.id | CASCADE DELETE |
| sensors | room_id → rooms.id | SET NULL |
| equipments | house_id → houses.id | CASCADE DELETE |
| equipments | room_id → rooms.id | SET NULL |
| automation_rules | house_id → houses.id | CASCADE DELETE |
| automation_rules | sensor_id → sensors.id | CASCADE DELETE |
| automation_rules | equipment_id → equipments.id | CASCADE DELETE |
| house_members | house_id → houses.id | CASCADE DELETE |
| house_members | user_id → users.id | CASCADE DELETE |
| event_history | house_id → houses.id | CASCADE DELETE |
| event_history | user_id → users.id | SET NULL |
| user_positions | house_id → houses.id | CASCADE DELETE |
| user_positions | user_id → users.id | CASCADE DELETE |

### Indexes de Performance

```sql
-- Indexes automatiques sur clés primaires et foreign keys
CREATE INDEX idx_houses_user_id ON houses(user_id);
CREATE INDEX idx_rooms_house_id ON rooms(house_id);
CREATE INDEX idx_sensors_house_id ON sensors(house_id);
CREATE INDEX idx_sensors_room_id ON sensors(room_id);
CREATE INDEX idx_equipments_house_id ON equipments(house_id);
CREATE INDEX idx_equipments_room_id ON equipments(room_id);
CREATE INDEX idx_automation_rules_house_id ON automation_rules(house_id);
CREATE INDEX idx_automation_rules_sensor_id ON automation_rules(sensor_id);
CREATE INDEX idx_automation_rules_equipment_id ON automation_rules(equipment_id);
CREATE INDEX idx_house_members_house_id ON house_members(house_id);
CREATE INDEX idx_house_members_user_id ON house_members(user_id);
CREATE INDEX idx_event_history_house_id ON event_history(house_id);
CREATE INDEX idx_event_history_user_id ON event_history(user_id);
CREATE INDEX idx_event_history_created_at ON event_history(created_at DESC);
CREATE INDEX idx_user_positions_house_id ON user_positions(house_id);
CREATE INDEX idx_user_positions_user_id ON user_positions(user_id);
```

---

## 🔄 Flux de Données

### 1. Authentification

```
┌──────────┐      POST /api/auth/login       ┌──────────┐
│  Client  │───────────────────────────────>│  Tornado │
│          │   {username, password}           │          │
└──────────┘                                  └────┬─────┘
                                                   │
                                                   │ verify_password()
                                                   │ bcrypt.checkpw()
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │ PostgreSQL  │
                                            │   users     │
                                            └─────────────┘
                                                   │
                                                   │ User found
                                                   │
┌──────────┐      Set-Cookie: uid, uname    ┌────▼─────┐
│  Client  │<───────────────────────────────│  Tornado │
│          │   200 OK {user}                 │          │
└──────────┘                                  └──────────┘
```

### 2. Requête REST Authentifiée

```
┌──────────┐      GET /api/houses            ┌──────────┐
│  Client  │───────────────────────────────>│  Tornado │
│          │   Cookie: uid=1                  │ Handler  │
└──────────┘                                  └────┬─────┘
                                                   │
                                                   │ get_current_user()
                                                   │ decode cookie
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │ Permissions  │
                                            │   Check      │
                                            └──────┬───────┘
                                                   │
                                                   │ Authorized
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │ SQLAlchemy  │
                                            │   async     │
                                            └──────┬──────┘
                                                   │
                                                   │ SELECT houses
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │ PostgreSQL  │
                                            │  houses     │
                                            └──────┬──────┘
                                                   │
                                                   │ Results
                                                   │
┌──────────┐      200 OK {houses: [...]}    ┌────▼─────┐
│  Client  │<───────────────────────────────│  Tornado │
│          │   JSON response                 │          │
└──────────┘                                  └──────────┘
```

### 3. WebSocket Temps Réel

```
┌───────────┐      WS connect                ┌──────────┐
│ Client 1  │═══════════════════════════════>│  Tornado │
│           │   ws://host/ws/house/1          │ WebSocket│
└───────────┘                                  │ Handler  │
                                               └────┬─────┘
┌───────────┐      WS connect                      │
│ Client 2  │═══════════════════════════════>│    │
│           │   ws://host/ws/house/1               │
└───────────┘                                       │
                                                    │ Store connections
                                                    │ in house_clients[1]
                                                    │
                                               ┌────▼──────┐
                                               │ Clients   │
                                               │ Registry  │
                                               └───────────┘

──────────────────────────────────────────────────────────────

┌───────────┐   POST /api/equipments/5/control ┌──────────┐
│ Client 1  │────────────────────────────────>│  Tornado │
│           │   {state: "closed"}               │ Handler  │
└───────────┘                                   └────┬─────┘
                                                     │
                                                     │ Update DB
                                                     │
                                                     ▼
                                              ┌─────────────┐
                                              │ PostgreSQL  │
                                              │ equipments  │
                                              └──────┬──────┘
                                                     │
                                                     │ Success
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │ WebSocket    │
                                              │ Broadcast    │
                                              └───┬──────────┘
                                                  │
                   ┌──────────────────────────────┴────────────┐
                   │                                            │
                   ▼                                            ▼
            ┌───────────┐  WS message            ┌───────────┐
            │ Client 1  │<════════════════════   │ Client 2  │
            │           │  {type: "equipment_    │           │
            └───────────┘   update", ...}         └───────────┘
```

### 4. Automatisation (B2B Logic)

```
┌──────────┐   POST /api/automation/trigger   ┌──────────┐
│  Client  │────────────────────────────────>│  Tornado │
│          │                                   │ Handler  │
└──────────┘                                   └────┬─────┘
                                                    │
                                                    │ Load active rules
                                                    │
                                                    ▼
                                             ┌─────────────┐
                                             │ PostgreSQL  │
                                             │ automation_ │
                                             │   rules     │
                                             └──────┬──────┘
                                                    │
                    ┌───────────────────────────────┤
                    │                               │
                    │ For each rule:                │
                    │                               │
                    ▼                               │
             ┌─────────────┐                        │
             │ Load Sensor │                        │
             │   + Value   │                        │
             └──────┬──────┘                        │
                    │                               │
                    │ Evaluate condition            │
                    │ (sensor.value > threshold)    │
                    │                               │
                    ▼                               │
             ┌──────────────┐                       │
             │ Condition    │                       │
             │    Met?      │                       │
             └──────┬───────┘                       │
                    │ Yes                           │
                    │                               │
                    ▼                               │
          ┌─────────────────┐                       │
          │ Load Equipment  │                       │
          │ Update State    │                       │
          └────────┬────────┘                       │
                   │                                │
                   │ Log event                      │
                   │                                │
                   ▼                                │
            ┌─────────────┐                         │
            │ event_      │                         │
            │  history    │                         │
            └──────┬──────┘                         │
                   │                                │
                   │ WebSocket broadcast            │
                   │                                │
                   ▼                                │
            ┌──────────────┐                        │
            │ All Clients  │◄───────────────────────┘
            │  in house    │
            └──────────────┘

┌──────────┐   200 OK {actions_taken: [...]}  ┌──────────┐
│  Client  │<───────────────────────────────  │  Tornado │
│          │                                   │          │
└──────────┘                                   └──────────┘
```

### 5. API Externe - Météo

```
┌──────────┐   GET /api/weather/1             ┌──────────┐
│  Client  │────────────────────────────────>│  Tornado │
│          │                                   │ Handler  │
└──────────┘                                   └────┬─────┘
                                                    │
                                                    │ Load house
                                                    │
                                                    ▼
                                             ┌─────────────┐
                                             │ PostgreSQL  │
                                             │   houses    │
                                             └──────┬──────┘
                                                    │
                                                    │ address
                                                    │ "Paris, France"
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │ WeatherService   │
                                          │ get_coordinates()│
                                          └────────┬─────────┘
                                                   │
                                                   │ HTTP GET
                                                   │
                                                   ▼
                                        ┌───────────────────────┐
                                        │ Nominatim API         │
                                        │ (OpenStreetMap)       │
                                        │ Geocoding Service     │
                                        └────────┬──────────────┘
                                                 │
                                                 │ {lat: 48.85, lon: 2.35}
                                                 │
                                                 ▼
                                          ┌──────────────────┐
                                          │ WeatherService   │
                                          │ get_weather()    │
                                          └────────┬─────────┘
                                                   │
                                                   │ HTTP GET
                                                   │
                                                   ▼
                                        ┌───────────────────────┐
                                        │ Open-Meteo API        │
                                        │ Weather Forecast      │
                                        │ (WMO Data)            │
                                        └────────┬──────────────┘
                                                 │
                                                 │ {temp: 18.5, humidity: 65, ...}
                                                 │
┌──────────┐   200 OK {weather: {...}}   ┌─────▼──────┐
│  Client  │<──────────────────────────── │  Tornado   │
│          │   JSON with weather data     │            │
└──────────┘                               └────────────┘
```

---

## 🔐 Sécurité

### Authentification

```python
# auth.py - Bcrypt hashing
def hash_password(password: str) -> str:
    """
    Hash password with bcrypt (automatically generates salt).
    
    Cost factor: 12 rounds (2^12 iterations)
    Salt: 16 bytes random (included in hash)
    """
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against bcrypt hash.
    
    Constant-time comparison to prevent timing attacks.
    """
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )
```

### Cookies Sécurisés

```python
# BaseAPIHandler - Cookie configuration
self.set_secure_cookie(
    "uid",
    str(user.id),
    expires_days=30,
    httponly=True,    # Pas accessible depuis JavaScript
    secure=True,      # HTTPS only (production)
    samesite='Lax'    # Protection CSRF
)
```

### JWT Optionnel

```python
# jwt_auth.py
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback-dev-key')
ALGORITHM = 'HS256'
EXPIRATION_MINUTES = 60

def generate_token(user_id: int, email: str) -> str:
    """Generate JWT token for API authentication."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

### Permissions

```python
# utils/permissions.py
async def check_house_permission(
    session, 
    house_id: int, 
    user_id: int, 
    required_role: str = None
) -> tuple[bool, Optional[str]]:
    """
    Check if user has access to house.
    
    Returns:
        (has_access, user_role)
    
    Roles:
        - owner: Full control
        - administrateur: Manage members, devices
        - occupant: View and control devices
    """
    house = await session.get(House, house_id)
    if not house:
        return False, None
    
    # Owner has all permissions
    if house.user_id == user_id:
        return True, 'owner'
    
    # Check membership
    member = await session.execute(
        select(HouseMember).where(
            and_(
                HouseMember.house_id == house_id,
                HouseMember.user_id == user_id,
                HouseMember.status == 'accepted'
            )
        )
    )
    member = member.scalar_one_or_none()
    
    if not member:
        return False, None
    
    # Check role if required
    if required_role:
        role_hierarchy = {
            'owner': 3,
            'administrateur': 2,
            'occupant': 1
        }
        
        user_level = role_hierarchy.get(member.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            return False, member.role
    
    return True, member.role
```

### Validation Données

```python
# Validation côté serveur (exemple)
def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Requirements:
        - Min 8 characters
        - At least 1 uppercase
        - At least 1 lowercase
        - At least 1 digit
        - At least 1 special char
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase"
    
    if not re.search(r'\d', password):
        return False, "Password must contain a digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain special character"
    
    return True, "Valid"
```

---

## ⚡ Performance

### Async/Await

```python
# Toutes les opérations I/O sont asynchrones
async def get(self, house_id):
    # Non-blocking database query
    async with async_session_maker() as session:
        result = await session.execute(
            select(House).where(House.id == int(house_id))
        )
        house = result.scalar_one_or_none()
```

### Connection Pooling

```python
# database.py - SQLAlchemy async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,              # 10 connections permanentes
    max_overflow=20,           # +20 connections temporaires
    pool_pre_ping=True,        # Test connection health
    pool_recycle=3600          # Recycle après 1h
)
```

### Optimisations Requêtes

```python
# Eager loading pour éviter N+1 queries
from sqlalchemy.orm import selectinload

result = await session.execute(
    select(House)
    .options(
        selectinload(House.rooms),
        selectinload(House.sensors),
        selectinload(House.equipments)
    )
    .where(House.id == house_id)
)
```

### Event History Cleanup

```python
# event_history.py - Automatic cleanup
MAX_EVENTS_PER_HOUSE = 1000
TARGET_AFTER_CLEANUP = 800  # 80% of max

# Strategy:
# 1. Delete low-priority events > 7 days
# 2. Delete important events > 90 days
# 3. If still > 1000, delete oldest until 800

# Triggered randomly (1% chance) on each event insert
if random.random() < 0.01:
    await cleanup_old_events(session, house_id)
```

---

## 🧪 Tests & Déploiement

### Tests Unitaires (À implémenter)

```python
# tests/test_auth.py
import pytest
from smarthome.tornado_app.auth import hash_password, verify_password

def test_password_hashing():
    """Test bcrypt hashing and verification."""
    password = "TestPass123!"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPass", hashed) is False

def test_password_uniqueness():
    """Test that same password produces different hashes (salt)."""
    password = "SamePassword"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
```

### Commandes Utiles

```bash
# Lancer l'application
python3 -m smarthome.tornado_app.app

# Lancer PostgreSQL
pg_ctl -D /usr/local/var/postgres start
pg_ctl -D /usr/local/var/postgres stop

# Tests (à implémenter)
pytest tests/

# Linting
flake8 smarthome/
black smarthome/

# Type checking
mypy smarthome/

# Coverage (à implémenter)
pytest --cov=smarthome --cov-report=html
```

### Déploiement Production

```bash
# 1. Configuration
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
export JWT_SECRET_KEY="your-super-secret-key-here"
export TORNADO_PORT=8001

# 2. Installation dépendances
pip install -r requirements.txt

# 3. Migrations (SQLAlchemy)
# À implémenter avec Alembic

# 4. Lancement serveur
python3 -m smarthome.tornado_app.app

# 5. (Optionnel) Reverse proxy Nginx
# nginx.conf:
# upstream tornado {
#     server 127.0.0.1:8001;
# }
# 
# server {
#     listen 80;
#     server_name smarthome.example.com;
#     
#     location / {
#         proxy_pass http://tornado;
#         proxy_http_version 1.1;
#         proxy_set_header Upgrade $http_upgrade;
#         proxy_set_header Connection "upgrade";
#     }
# }
```

---

## 📈 Évolutions Futures

### Court Terme

- [ ] **Tests automatisés** (pytest + coverage > 80%)
- [ ] **Migrations Alembic** (gestion versions schéma)
- [ ] **Rate limiting** (100 req/min par user)
- [ ] **Logging structuré** (JSON logs + rotation)
- [ ] **Métriques Prometheus** (performance monitoring)

### Moyen Terme

- [ ] **API GraphQL** (en plus de REST)
- [ ] **Support multi-langues** (i18n backend)
- [ ] **Notifications push** (PWA + Service Workers)
- [ ] **Export données** (GDPR compliance)
- [ ] **Backup automatique** (PostgreSQL dumps)

### Long Terme

- [ ] **Intégration IA** (prédiction automatisation)
- [ ] **Mobile apps** (React Native)
- [ ] **Support MQTT** (vrais devices IoT)
- [ ] **Clustering** (multi-serveurs)
- [ ] **Kubernetes** (orchestration containers)

---

## 📚 Références

### Documentation Officielle

- **Tornado** : https://www.tornadoweb.org/en/stable/
- **SQLAlchemy** : https://docs.sqlalchemy.org/en/20/
- **PostgreSQL** : https://www.postgresql.org/docs/
- **bcrypt** : https://github.com/pyca/bcrypt/
- **PyJWT** : https://pyjwt.readthedocs.io/
- **Open-Meteo** : https://open-meteo.com/en/docs

### Patterns & Best Practices

- **REST API Design** : https://restfulapi.net/
- **WebSocket Protocol** : https://datatracker.ietf.org/doc/html/rfc6455
- **Async Python** : https://docs.python.org/3/library/asyncio.html
- **Security** : https://owasp.org/www-project-top-ten/

---

**Fin de l'Architecture Technique**

---

**Dernière mise à jour** : 30 novembre 2024  
**Version** : 3.0  
**Auteur** : David Yala
