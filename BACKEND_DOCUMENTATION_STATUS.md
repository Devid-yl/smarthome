# Backend Documentation Status

## English Documentation Standard

**All backend code (Python, handlers, models, services) MUST be documented in English.**

---

## Current Status Assessment

### ✅ Compliant Files
- `API_DOCUMENTATION.md` - Complete English API reference
- `PROJECT_REQUIREMENTS.md` - Academic requirements mapping (French for academic context)
- Most code is well-structured

### ⚠️ Files Requiring Translation

The following files contain French docstrings/comments that need to be translated to English:

#### Handlers (`smarthome/tornado_app/handlers/`)
1. **`users_api.py`**
   - Line 2: `"""API REST pour la gestion des utilisateurs"""`
   - Line 14: `"""Base handler pour les API REST."""`
   - Line 89: `"""POST /api/auth/register - Inscription d'un utilisateur"""`
   - And multiple other French docstrings

2. **`houses_api.py`**
   - French docstrings for all handlers
   - Examples: "Liste des maisons", "Créer une maison"

3. **`sensors.py`**
   - French docstrings
   - Examples: "Créer un capteur", "Mettre à jour un capteur"

4. **`equipments.py`**
   - French docstrings
   - Examples: "Liste des équipements", "Contrôler un équipement"

5. **`automation_rules.py`**
   - French docstrings
   - Examples: "Règles d'automatisation"

6. **`automation.py`**
   - French docstrings

7. **`house_members.py`**
   - French docstrings
   - Examples: "Membres de la maison", "Inviter un membre"

8. **`event_history.py`**
   - Line 11: `"""Handler pour consulter l'historique des événements."""`
   - Line 16: `"""Liste l'historique des événements d'une maison."""`
   - And many others

9. **`user_positions.py`**
   - French docstrings

10. **`weather.py`**
    - French docstrings

11. **`grid_editor.py`**
    - French docstrings

12. **`websocket.py`**
    - Likely has French comments

#### Models (`smarthome/tornado_app/models.py`)
- Some French comments may exist
- Model docstrings need review

#### Services (`smarthome/tornado_app/services/`)
- `weather_service.py` - Check for French comments

#### Utilities (`smarthome/tornado_app/utils/`)
- All utility files need review

---

## Translation Guidelines

### Documentation Format

All Python docstrings should follow this format:

```python
"""Short one-line description.

Detailed multi-line description if needed.

Args:
    param_name (type): Description.

Returns:
    type: Description.

Raises:
    ExceptionType: When this happens.
"""
```

### Handler Method Documentation

```python
async def get(self, house_id):
    """
    Get house details.
    
    Retrieves detailed information about a specific house including
    all rooms, sensors, and equipment counts.
    
    Args:
        house_id (str): The house ID from URL path.
        
    Returns:
        JSON response with house details.
        
    Raises:
        404: House not found or access denied.
    """
```

### Class Documentation

```python
class HouseDetailHandler(BaseAPIHandler):
    """
    Handler for house detail operations.
    
    Provides GET, PUT, DELETE operations for individual houses.
    Requires user to be owner or member of the house.
    
    Endpoints:
        GET /api/houses/{id} - Get house details
        PUT /api/houses/{id} - Update house
        DELETE /api/houses/{id} - Delete house (owner only)
    """
```

---

## Translation Priority

### High Priority (Core API Handlers)
1. ✅ `users_api.py` - User management
2. ✅ `houses_api.py` - House/Room management
3. ✅ `sensors.py` - IoT sensors
4. ✅ `equipments.py` - Equipment control
5. ✅ `automation_rules.py` - Automation rules
6. ✅ `event_history.py` - Event logging

### Medium Priority (Supporting Features)
7. ✅ `house_members.py` - Member management
8. ✅ `user_positions.py` - Position tracking
9. ✅ `weather.py` - Weather service
10. ✅ `automation.py` - Automation triggers

### Low Priority (Editor & WebSocket)
11. ✅ `grid_editor.py` - Grid editing
12. ✅ `websocket.py` - Real-time updates

---

## Example Translations

### Before (French)
```python
class SensorsHandler(BaseAPIHandler):
    """Liste et création des capteurs."""
    
    async def get(self):
        """
        Liste tous les capteurs d'une maison.
        
        Query parameters:
        - house_id: ID de la maison (requis)
        - room_id: Filtrer par pièce (optionnel)
        """
```

### After (English)
```python
class SensorsHandler(BaseAPIHandler):
    """
    Handler for sensor list and creation.
    
    Provides endpoints to list all sensors in a house
    and create new sensor instances.
    """
    
    async def get(self):
        """
        List all sensors for a house.
        
        Query Parameters:
            house_id (int): House ID (required)
            room_id (int, optional): Filter by room
            
        Returns:
            JSON array of sensor objects with details.
            
        Raises:
            400: Missing house_id parameter
            403: User not authorized for this house
            404: House not found
        """
```

---

## Action Items

To complete English documentation:

1. **Automated Search**
   ```bash
   # Find all French docstrings
   grep -r "\"\"\".*[àâäéèêëïîôùûüÿæœç]" smarthome/tornado_app/handlers/
   grep -r "'''.*[àâäéèêëïîôùûüÿæœç]" smarthome/tornado_app/handlers/
   ```

2. **Manual Review**
   - Go through each handler file
   - Translate class docstrings
   - Translate method docstrings
   - Update inline comments

3. **Verify Consistency**
   - Ensure all docstrings use English
   - Check that terminology matches API_DOCUMENTATION.md
   - Validate docstring format (Google/NumPy style)

4. **Commit Changes**
   ```bash
   git add smarthome/tornado_app/
   git commit -m "docs: Translate all backend documentation to English"
   ```

---

## Notes

- **Frontend can remain in French** - User-facing text is for French users
- **API_DOCUMENTATION.md is the reference** - Use same terminology
- **Models should have English docstrings** - They're part of backend
- **Comments explaining logic should be English** - Professional standard

---

**Status**: ⚠️ **Translation Required**  
**Target Completion**: Before final project submission  
**Estimated Time**: 2-3 hours for complete review and translation

---

**Last Updated**: November 30, 2024  
**Responsible**: David Yala
