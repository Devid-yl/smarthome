# SmartHome - Guide de Démonstration

## 📋 Objectif

Ce guide fournit un plan structuré pour démontrer l'ensemble des fonctionnalités du projet SmartHome lors de la présentation académique, en mettant en évidence la conformité avec les 35 points requis.

**Durée recommandée** : 16-20 minutes  
**Format** : Démonstration live + explications techniques

---

## 🎯 Structure de la Présentation

### Introduction (2 minutes)
1. **Contexte du projet**
   - Système domotique intelligent
   - Technologies : Tornado 6.4+, PostgreSQL 15+, WebSocket
   - Architecture REST API complète

2. **Vue d'ensemble des objectifs**
   - 25 points fonctionnalités internes
   - 5 points API externe (météo)
   - 5 points système d'information (BDD)

---

## 🚀 Démonstration Détaillée

### PARTIE 1 : Authentification & Utilisateurs (3 minutes)

#### 1.1 Inscription et Connexion
**Objectif** : Démontrer la gestion des utilisateurs (3 points)

**Actions à faire** :
```
1. Ouvrir http://localhost:8001/login
2. Créer un compte :
   - Username: demo_user
   - Email: demo@example.com
   - Password: DemoPass123!
   - Téléphone: +33612345678
3. Vérifier la redirection automatique après inscription
4. Se déconnecter
5. Se reconnecter avec les identifiants
```

**Points à mentionner** :
- ✅ **Hachage bcrypt** des mots de passe (sécurité)
- ✅ **Cookies sécurisés** pour l'authentification
- ✅ **JWT optionnel** pour REST API
- ✅ **Validation côté serveur** (email format, mot de passe fort)

**Code à montrer** :
```python
# handlers/users_api.py - ligne 130
hashed_pw = hash_password(password)  # bcrypt avec salt automatique
```

---

#### 1.2 Profil Utilisateur
**Objectif** : Démontrer la gestion du profil (2 points)

**Actions à faire** :
```
1. Aller sur /profile
2. Modifier l'email et le téléphone
3. Télécharger une photo de profil (max 5MB)
4. Afficher les statistiques (nombre de maisons)
```

**Points à mentionner** :
- ✅ **Upload d'images** avec validation (JPG/PNG, 5MB max)
- ✅ **Modification sécurisée** (mot de passe requis pour certains changements)
- ✅ **Stockage organisé** dans `/media/profile_images/`

**Code à montrer** :
```python
# handlers/users_api.py - ligne 357
# Upload avec validation de taille et type
```

---

### PARTIE 2 : Gestion des Maisons (4 minutes)

#### 2.1 Création de Maison
**Objectif** : Démontrer le CRUD complet (4 points)

**Actions à faire** :
```
1. Aller sur /dashboard
2. Créer une nouvelle maison :
   - Nom: "Ma Maison Intelligente"
   - Adresse: "15 Rue de la Paix, Paris, France"
   - Dimensions: 10x8
3. Observer la grille générée automatiquement avec contours
4. Ajouter 3 pièces :
   - Salon
   - Cuisine
   - Chambre
```

**Points à mentionner** :
- ✅ **Grille JSON dynamique** avec murs automatiques
- ✅ **Format hybride** : ancien (array) + nouveau (layered)
- ✅ **Cascade delete** (suppression maison → tout effacé)
- ✅ **Permissions strictes** (propriétaire vs membres)

**Structure de grille à expliquer** :
```json
{
  "base": 0,              // 0=vide, 1=mur, 2xxx=pièce
  "sensors": [1, 5],      // IDs des capteurs
  "equipments": [2]       // IDs des équipements
}
```

---

#### 2.2 Membres de Maison
**Objectif** : Démontrer le système multi-utilisateurs (3 points)

**Actions à faire** :
```
1. Dans /members, inviter un utilisateur
   - Sélectionner utilisateur existant
   - Rôle: "Occupant"
2. Se connecter avec le 2e compte
3. Accepter l'invitation dans /invitations
4. Revenir au 1er compte
5. Modifier le rôle → "Administrateur"
6. Tester les permissions (occupant ne peut pas inviter)
```

**Points à mentionner** :
- ✅ **Système d'invitations** (pending/accepted/rejected)
- ✅ **2 rôles** : Administrateur, Occupant
- ✅ **Permissions granulaires** par rôle
- ✅ **Historique complet** des actions membres

**Table à montrer** :
```sql
-- models.py - HouseMember
role: administrateur | occupant
status: pending | accepted | rejected
```

---

### PARTIE 3 : IoT - Capteurs (3 minutes)

#### 3.1 Capteurs Multiples
**Objectif** : Démontrer les 4 types de capteurs (4 points)

**Actions à faire** :
```
1. Dans /house, ajouter des capteurs :
   
   A. Capteur Température
      - Nom: "Salon - Température"
      - Type: temperature
      - Valeur: 22.5°C
   
   B. Capteur Luminosité
      - Nom: "Cuisine - Lumière"
      - Type: luminosity
      - Valeur: 450 lux
   
   C. Capteur Pluie
      - Nom: "Extérieur - Pluie"
      - Type: rain
      - Valeur: 0% (pas de pluie)
   
   D. Capteur Présence
      - Nom: "Entrée - Mouvement"
      - Type: presence
      - Valeur: false (aucun mouvement)

2. Modifier la température → 28°C
3. Observer la mise à jour en temps réel (WebSocket)
```

**Points à mentionner** :
- ✅ **4 types de capteurs** IoT différents
- ✅ **Unités automatiques** (°C, lux, %, bool)
- ✅ **Valeurs flottantes** pour précision
- ✅ **Timestamp automatique** (last_update)
- ✅ **État actif/inactif** configurable

**Code à montrer** :
```python
# models.py - Sensor
type: temperature | luminosity | rain | presence
value: Float (stockage précis)
unit: String (calculé automatiquement)
```

---

### PARTIE 4 : IoT - Équipements (3 minutes)

#### 4.1 Équipements Multiples
**Objectif** : Démontrer les 4 types d'équipements (4 points)

**Actions à faire** :
```
1. Ajouter des équipements :
   
   A. Volet Roulant
      - Nom: "Salon - Volet"
      - Type: shutter
      - États: open/closed
   
   B. Porte
      - Nom: "Porte d'Entrée"
      - Type: door
      - États: open/closed
      - Permissions: Admin uniquement
   
   C. Lumière
      - Nom: "Cuisine - LED"
      - Type: light
      - États: on/off
   
   D. Système Audio
      - Nom: "Salon - Sonos"
      - Type: sound_system
      - États: on/off

2. Contrôler chaque équipement
3. Tester les permissions (avec compte occupant)
4. Observer WebSocket (tous les clients voient les changements)
```

**Points à mentionner** :
- ✅ **4 types d'équipements** différents
- ✅ **États binaires** adaptés au type
- ✅ **Permissions par rôle** (allowed_roles: [])
- ✅ **Broadcast WebSocket** automatique
- ✅ **Historique complet** des actions

**Structure permissions** :
```json
{
  "allowed_roles": ["administrateur"],  // Seuls les admins
  "allowed_roles": null                // Tout le monde
}
```

---

### PARTIE 5 : Automatisation (4 minutes)

#### 5.1 Règles d'Automatisation
**Objectif** : Démontrer la logique B2B (5 points)

**Actions à faire** :
```
1. Créer des règles dans /house (onglet Automation) :
   
   Règle 1: Confort Thermique
   - Si Température > 28°C
   - Alors Fermer les volets
   
   Règle 2: Économie d'Énergie
   - Si Luminosité < 200 lux
   - Alors Allumer les lumières
   
   Règle 3: Sécurité Pluie
   - Si Pluie > 50%
   - Alors Fermer les volets

2. Modifier les valeurs des capteurs pour déclencher
   - Température → 30°C
   - Observer l'action automatique
   
3. Voir l'historique des déclenchements
4. Désactiver/Réactiver une règle
```

**Points à mentionner** :
- ✅ **6 opérateurs** : `>`, `<`, `>=`, `<=`, `==`, `!=`
- ✅ **Évaluation automatique** (trigger endpoint)
- ✅ **État actif/inactif** par règle
- ✅ **Timestamp last_triggered**
- ✅ **Historique détaillé** avec metadata

**Logique B2B à expliquer** :
```python
# automation.py - ligne 47
if rule.condition_operator == '>':
    condition_met = sensor.value > rule.condition_value

if condition_met:
    equipment.state = rule.action_state
    # Log dans event_history
```

---

#### 5.2 Test de l'Automatisation
**Actions à faire** :
```
1. Ouvrir 2 navigateurs (2 utilisateurs différents)
2. Modifier un capteur dans navigateur 1
3. Observer :
   - Mise à jour WebSocket des capteurs (temps réel)
   - Déclenchement automatique des règles
   - Changement d'état des équipements
   - Notification WebSocket pour tous les clients
4. Vérifier l'historique des événements
```

---

### PARTIE 6 : API Externe - Météo (2 minutes)

#### 6.1 Intégration Open-Meteo
**Objectif** : Démontrer l'API externe (5 points)

**Actions à faire** :
```
1. Dans /house, cliquer sur "Météo"
2. Observer les données affichées :
   - Température actuelle
   - Humidité
   - Vitesse du vent
   - Condition météo (icône)
   - Nom de la ville
   
3. Tester avec adresse différente :
   - Modifier l'adresse de la maison
   - Recharger la météo
   - Vérifier la géolocalisation automatique
```

**Points à mentionner** :
- ✅ **API Open-Meteo** (gratuite, sans clé)
- ✅ **Géocodage automatique** (Nominatim)
- ✅ **Parsing d'adresse** intelligent
- ✅ **Gestion d'erreurs** complète
- ✅ **Cache potentiel** (optimisation)

**Code à montrer** :
```python
# services/weather_service.py - ligne 15
@staticmethod
async def get_coordinates(city_name: str):
    # Nominatim geocoding API
    url = f"https://nominatim.openstreetmap.org/search"
    # Returns: latitude, longitude, name, country
```

**API appelée** :
```
GET https://api.open-meteo.com/v1/forecast
  ?latitude=48.8566
  &longitude=2.3522
  &current=temperature_2m,relative_humidity_2m,wind_speed_10m
```

---

### PARTIE 7 : Historique des Événements (2 minutes)

#### 7.1 Système d'Événements
**Objectif** : Démontrer la traçabilité complète (3 points)

**Actions à faire** :
```
1. Aller sur /history
2. Observer les différents types d'événements :
   - equipment_control (contrôle manuel)
   - sensor_reading (nouvelles valeurs)
   - automation_triggered (règles déclenchées)
   - member_action (invitations, rôles)
   - house_modified (changements structure)

3. Filtrer par :
   - Type d'événement
   - Utilisateur
   - Période (7 derniers jours)

4. Tester la pagination (50 par page)

5. Voir les statistiques :
   - Total par type
   - Total par utilisateur
   - Total par jour
```

**Points à mentionner** :
- ✅ **5 types d'événements** distincts
- ✅ **Metadata JSON** pour détails
- ✅ **IP address tracking**
- ✅ **Cleanup automatique** (>1000 événements)
- ✅ **Stratégie de rétention** intelligente

**Système de cleanup à expliquer** :
```python
# event_history.py - ligne 265
MAX_EVENTS = 1000
TARGET_AFTER_CLEANUP = 800

# 3 étapes :
# 1. Supprimer événements peu importants > 7 jours
# 2. Supprimer événements importants > 90 jours
# 3. Si encore > 1000, supprimer les plus anciens
```

---

#### 7.2 Nettoyage Automatique
**Actions à faire** :
```
1. Afficher le nombre d'événements (dans stats)
2. Déclencher nettoyage manuel (bouton "Nettoyer")
3. Observer :
   - Nombre avant/après
   - Types préservés (importants gardés)
   - Confirmation du résultat
```

---

### PARTIE 8 : Temps Réel - WebSocket (2 minutes)

#### 8.1 Communication Bidirectionnelle
**Objectif** : Démontrer le WebSocket (3 points)

**Actions à faire** :
```
1. Ouvrir /house dans 2 navigateurs (ou 2 onglets)
2. Dans navigateur 1 :
   - Modifier un capteur
   - Contrôler un équipement
   - Déclencher une règle

3. Observer dans navigateur 2 :
   - Mise à jour instantanée (< 100ms)
   - Aucun refresh nécessaire
   - Tous les changements synchronisés

4. Ouvrir la console développeur (F12)
5. Observer les messages WebSocket :
   - sensor_update
   - equipment_update
   - automation_triggered
   - user_position
```

**Points à mentionner** :
- ✅ **WebSocket persistant** (connexion maintenue)
- ✅ **Broadcast automatique** à tous les clients
- ✅ **Messages typés** JSON
- ✅ **Reconnexion automatique** si déconnexion
- ✅ **Format structuré** pour chaque type

**Structure message WebSocket** :
```json
{
  "type": "equipment_update",
  "equipment": {
    "id": 1,
    "name": "Salon - Volet",
    "state": "closed",
    "last_update": "2024-11-30T15:00:00Z"
  }
}
```

**Code à montrer** :
```javascript
// static/app/realtime.js - ligne 45
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleRealtimeUpdate(data);
};
```

---

### PARTIE 9 : Simulation de Mouvement (1 minute)

#### 9.1 Positionnement Utilisateurs
**Objectif** : Démontrer le tracking utilisateurs (2 points)

**Actions à faire** :
```
1. Dans /house, activer "Simuler position"
2. Cliquer sur différentes cellules de la grille
3. Observer :
   - Badge utilisateur se déplace
   - Position mise à jour en temps réel
   - Autres utilisateurs voient les mouvements

4. Avec 2 navigateurs :
   - 2 utilisateurs simultanés
   - Chacun voit l'autre se déplacer
   - Badges avec pseudo et photo
```

**Points à mentionner** :
- ✅ **Table user_positions** dédiée
- ✅ **Coordonnées X/Y** dans la grille
- ✅ **Timestamp last_update**
- ✅ **WebSocket broadcast** automatique
- ✅ **Affichage visuel** avec badges

---

### PARTIE 10 : Base de Données (2 minutes)

#### 10.1 Structure de la Base
**Objectif** : Démontrer la conception BDD (5 points)

**Actions à faire** :
```
1. Ouvrir pgAdmin ou psql
2. Montrer les 9 tables :
   - users
   - houses
   - rooms
   - sensors
   - equipments
   - automation_rules
   - house_members
   - event_history
   - user_positions

3. Expliquer les relations :
   - Foreign keys
   - Cascade deletes
   - Indexes

4. Montrer des requêtes complexes :
   - Jointures multiples
   - Agrégations
   - Sous-requêtes
```

**Schéma à dessiner** :
```
users (1) ─── (N) houses (1) ─┬─ (N) rooms
                               ├─ (N) sensors
                               ├─ (N) equipments
                               ├─ (N) automation_rules
                               ├─ (N) house_members
                               ├─ (N) event_history
                               └─ (N) user_positions
```

**Points à mentionner** :
- ✅ **9 tables** normalisées
- ✅ **Foreign keys** avec contraintes
- ✅ **Cascade delete** pour intégrité
- ✅ **Indexes** pour performance
- ✅ **JSONB** pour flexibilité (grid, metadata)

**Requête à montrer** :
```sql
-- Statistiques complètes d'une maison
SELECT 
    h.name,
    COUNT(DISTINCT r.id) as rooms,
    COUNT(DISTINCT s.id) as sensors,
    COUNT(DISTINCT e.id) as equipments,
    COUNT(DISTINCT ar.id) as rules,
    COUNT(DISTINCT hm.id) as members
FROM houses h
LEFT JOIN rooms r ON r.house_id = h.id
LEFT JOIN sensors s ON s.house_id = h.id
LEFT JOIN equipments e ON e.house_id = h.id
LEFT JOIN automation_rules ar ON ar.house_id = h.id
LEFT JOIN house_members hm ON hm.house_id = h.id AND hm.status = 'accepted'
WHERE h.id = 1
GROUP BY h.id, h.name;
```

---

## 📊 Récapitulatif des Points

### Fonctionnalités Internes (25/25 points)

| Fonctionnalité | Points | Démontré |
|---------------|--------|----------|
| Authentification utilisateur | 3 | ✅ Inscription, login, JWT |
| Gestion profil | 2 | ✅ Modification, upload photo |
| CRUD maisons | 4 | ✅ Create, Read, Update, Delete |
| Multi-utilisateurs | 3 | ✅ Invitations, rôles, permissions |
| Capteurs IoT (4 types) | 4 | ✅ Temperature, luminosity, rain, presence |
| Équipements (4 types) | 4 | ✅ Shutter, door, light, sound_system |
| Automatisation | 5 | ✅ Règles, conditions, actions, trigger |
| Historique événements | 3 | ✅ 5 types, filtres, stats, cleanup |
| WebSocket temps réel | 3 | ✅ Broadcast, messages typés |
| Simulation mouvement | 2 | ✅ Positions, tracking temps réel |

**Total** : **25/25** ✅

---

### API Externe (5/5 points)

| Fonctionnalité | Points | Démontré |
|---------------|--------|----------|
| Intégration Open-Meteo | 3 | ✅ Météo temps réel |
| Géocodage automatique | 1 | ✅ Nominatim API |
| Gestion erreurs | 1 | ✅ Validation adresse |

**Total** : **5/5** ✅

---

### Système d'Information (5/5 points)

| Fonctionnalité | Points | Démontré |
|---------------|--------|----------|
| 9 tables normalisées | 2 | ✅ Structure complète |
| Relations & contraintes | 1 | ✅ Foreign keys, cascade |
| Requêtes complexes | 1 | ✅ Jointures, agrégations |
| Performance (indexes) | 1 | ✅ Optimisations |

**Total** : **5/5** ✅

---

## 🎓 **TOTAL GÉNÉRAL : 35/35 points** ✅

---

## 💡 Conseils pour la Présentation

### Avant la Démonstration

1. **Préparation environnement**
   ```bash
   # Lancer PostgreSQL
   pg_ctl -D /usr/local/var/postgres start
   
   # Lancer l'application
   cd smarthome
   source venv/bin/activate
   python3 -m smarthome.tornado_app.app
   
   # Ouvrir navigateurs
   - Chrome (utilisateur 1)
   - Firefox (utilisateur 2)
   ```

2. **Données de test**
   - Créer 2 comptes utilisateurs à l'avance
   - Préparer une maison avec données complètes
   - Avoir des événements dans l'historique

3. **Documentation prête**
   - `PROJECT_REQUIREMENTS.md` ouvert
   - `API_DOCUMENTATION.md` en référence
   - Diagrammes d'architecture imprimés

---

### Pendant la Démonstration

1. **Expliquer avant de faire**
   - Annoncer ce que vous allez montrer
   - Expliquer pourquoi c'est important
   - Pointer vers les points du projet

2. **Montrer le code pertinent**
   - Models.py pour la BDD
   - Handlers pour la logique
   - Services pour l'API externe

3. **Utiliser la console développeur**
   - Network tab pour voir les requêtes REST
   - WebSocket tab pour voir les messages
   - Console pour voir les logs

4. **Mettre en évidence les choix techniques**
   - Tornado pour performance asynchrone
   - PostgreSQL pour robustesse
   - WebSocket pour temps réel
   - JSONB pour flexibilité

---

### Questions Fréquentes à Anticiper

**Q1: Pourquoi Tornado et pas Flask/Django ?**
```
R: Tornado supporte nativement async/await et WebSocket,
   essentiel pour le temps réel. Performance supérieure
   pour applications avec I/O intensif.
```

**Q2: Comment gérez-vous la sécurité ?**
```
R: - Bcrypt pour hash des mots de passe (salt automatique)
   - JWT optionnel pour API REST
   - Validation stricte côté serveur
   - Permissions granulaires par rôle
   - Cookies HttpOnly/Secure
```

**Q3: Pourquoi 2 formats de grille (array + layered) ?**
```
R: - Ancien format (array): Rétrocompatibilité
   - Nouveau format (layered): Permet overlay de capteurs
     et équipements sur la même cellule, plus flexible
```

**Q4: Comment gérez-vous la montée en charge ?**
```
R: - Async/await pour non-blocking I/O
   - Connection pooling PostgreSQL (SQLAlchemy)
   - Indexes sur foreign keys
   - Cleanup automatique historique (limite 1000)
   - WebSocket avec broadcast efficace
```

**Q5: Pourquoi Open-Meteo et pas OpenWeatherMap ?**
```
R: - Gratuit sans limite
   - Pas de clé API nécessaire
   - Données précises (WMO)
   - Documentation excellente
   - Nominatim pour géocodage (OpenStreetMap)
```

---

## 📸 Captures d'Écran Recommandées

Préparer ces captures pour la présentation :

1. **Dashboard** - Vue d'ensemble des maisons
2. **House Grid** - Grille avec capteurs/équipements
3. **Automation Rules** - Liste des règles actives
4. **Event History** - Historique avec filtres
5. **Weather Widget** - Intégration météo
6. **Members Management** - Système d'invitations
7. **WebSocket Console** - Messages temps réel
8. **Database Schema** - ERD complet
9. **API Response** - Exemple JSON
10. **Performance Metrics** - Si disponible

---

## 🎯 Points Forts à Mettre en Avant

1. **Architecture Moderne**
   - Async/await natif
   - WebSocket temps réel
   - REST API complète

2. **Qualité du Code**
   - Docstrings en anglais
   - Type hints Python
   - Validation stricte

3. **Sécurité**
   - Authentification robuste
   - Permissions granulaires
   - Validation données

4. **Évolutivité**
   - Structure modulaire
   - API externe extensible
   - Système d'événements flexible

5. **Expérience Utilisateur**
   - Interface responsive
   - Feedback temps réel
   - Gestion erreurs claire

---

## ✅ Checklist Finale

Avant la présentation, vérifier :

- [ ] PostgreSQL démarré et accessible
- [ ] Application Tornado lancée (port 8001)
- [ ] 2 comptes utilisateurs créés
- [ ] Maison avec données complètes
- [ ] Historique avec événements variés
- [ ] 2 navigateurs ouverts (Chrome + Firefox)
- [ ] Console développeur prête (F12)
- [ ] Documentation imprimée/affichée
- [ ] Captures d'écran préparées
- [ ] Timer 16 minutes configuré

---

**Bonne présentation ! 🚀**

---

**Dernière mise à jour** : 30 novembre 2024  
**Auteur** : David Yala  
**Version** : 1.0
