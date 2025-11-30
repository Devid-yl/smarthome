# SmartHome REST API Documentation

## Overview

Complete REST API for the SmartHome intelligent home automation system. This API provides comprehensive endpoints for user management, house management, IoT sensors, equipment control, automation rules, and real-time updates.

**Base URL**: `http://localhost:8001`  
**API Version**: 3.0  
**Authentication**: Cookie-based + JWT (optional)  
**Response Format**: JSON

---

## Table of Contents

1. [Authentication & Users](#1-authentication--users)
2. [Houses & Rooms](#2-houses--rooms)
3. [Sensors (IoT)](#3-sensors-iot)
4. [Equipments](#4-equipments)
5. [Automation Rules](#5-automation-rules)
6. [House Members](#6-house-members)
7. [Event History](#7-event-history)
8. [User Positions](#8-user-positions)
9. [Weather Service](#9-weather-service)
10. [WebSocket](#10-websocket)

---

## 1. Authentication & Users

### 1.1 Register

Create a new user account.

**Endpoint**: `POST /api/auth/register`  
**Authentication**: None  
**Handler**: `RegisterAPIHandler` (`users_api.py`)

**Request Body**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "phone_number": "+33612345678"
}
```

**Response** (201 Created):
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "phone_number": "+33612345678"
  }
}
```

**Errors**:
- `400`: Username or email already exists
- `400`: Invalid email format
- `400`: Password too weak

---

### 1.2 Login

Authenticate user and create session.

**Endpoint**: `POST /api/auth/login`  
**Authentication**: None  
**Handler**: `LoginAPIHandler` (`users_api.py`)

**Request Body**:
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

**Set-Cookie**: `uid=1; uname=john_doe; HttpOnly; Secure`

**Errors**:
- `401`: Invalid credentials
- `403`: Account inactive

---

### 1.3 Logout

End current session.

**Endpoint**: `POST /api/auth/logout`  
**Authentication**: Required  
**Handler**: `LogoutAPIHandler` (`users_api.py`)

**Response** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

---

### 1.4 Get Current User

Retrieve authenticated user information.

**Endpoint**: `GET /api/auth/me`  
**Authentication**: Required  
**Handler**: `MeAPIHandler` (`users_api.py`)

**Response** (200 OK):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "phone_number": "+33612345678",
  "profile_image": "/media/profile_images/user_1.jpg",
  "date_joined": "2024-11-25T10:30:00Z"
}
```

---

### 1.5 Get Profile

Get detailed user profile.

**Endpoint**: `GET /api/users/me`  
**Authentication**: Required  
**Handler**: `ProfileHandler` (`users_api.py`)

**Response** (200 OK):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "phone_number": "+33612345678",
  "profile_image": "/media/profile_images/user_1.jpg",
  "date_joined": "2024-11-25T10:30:00Z",
  "houses_count": 3
}
```

---

### 1.6 Update Profile

Modify user profile information.

**Endpoint**: `PUT /api/users/me`  
**Authentication**: Required  
**Handler**: `ProfileHandler` (`users_api.py`)

**Request Body**:
```json
{
  "email": "newemail@example.com",
  "phone_number": "+33698765432",
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

**Response** (200 OK):
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "newemail@example.com",
    "phone_number": "+33698765432"
  }
}
```

**Errors**:
- `400`: Current password incorrect (if changing password)
- `400`: Email already in use

---

### 1.7 Delete Account

Permanently delete user account and all associated data.

**Endpoint**: `DELETE /api/users/me`  
**Authentication**: Required  
**Handler**: `ProfileHandler` (`users_api.py`)

**Request Body**:
```json
{
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "message": "Account deleted successfully"
}
```

**Errors**:
- `400`: Incorrect password
- `403`: Cannot delete account with active houses

---

### 1.8 Upload Profile Image

Upload profile picture (max 5MB, JPG/PNG).

**Endpoint**: `POST /api/upload-profile-image`  
**Authentication**: Required  
**Handler**: `UploadProfileImageHandler` (`users_api.py`)  
**Content-Type**: `multipart/form-data`

**Request**:
```
POST /api/upload-profile-image
Content-Type: multipart/form-data

profile_image: <file>
```

**Response** (200 OK):
```json
{
  "message": "Profile image uploaded successfully",
  "image_url": "/media/profile_images/user_1_1638123456.jpg"
}
```

**Errors**:
- `400`: No file provided
- `400`: Invalid file type (only JPG/PNG allowed)
- `400`: File too large (max 5MB)

---

## 2. Houses & Rooms

### 2.1 List Houses

Get all houses for authenticated user.

**Endpoint**: `GET /api/houses`  
**Authentication**: Required  
**Handler**: `HousesHandler` (`houses_api.py`)

**Response** (200 OK):
```json
{
  "houses": [
    {
      "id": 1,
      "name": "My Home",
      "address": "123 Main St, Paris",
      "length": 10,
      "width": 8,
      "is_owner": true,
      "role": null
    },
    {
      "id": 2,
      "name": "Vacation House",
      "address": "456 Beach Rd, Nice",
      "length": 12,
      "width": 10,
      "is_owner": false,
      "role": "administrateur"
    }
  ]
}
```

---

### 2.2 Create House

Create a new house.

**Endpoint**: `POST /api/houses`  
**Authentication**: Required  
**Handler**: `HousesHandler` (`houses_api.py`)

**Request Body**:
```json
{
  "name": "My Smart Home",
  "address": "15 Rue de la Paix, Paris, France",
  "length": 10,
  "width": 8
}
```

**Response** (201 Created):
```json
{
  "message": "House created successfully",
  "house": {
    "id": 1,
    "name": "My Smart Home",
    "address": "15 Rue de la Paix, Paris, France",
    "length": 10,
    "width": 8,
    "grid": [[0, 0, ...], ...]
  }
}
```

**Errors**:
- `400`: Invalid dimensions (min 1, max 50)
- `400`: Missing required fields

---

### 2.3 Get House Details

Get detailed information about a specific house.

**Endpoint**: `GET /api/houses/{id}`  
**Authentication**: Required  
**Handler**: `HouseDetailHandler` (`houses_api.py`)

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "My Smart Home",
  "address": "15 Rue de la Paix, Paris, France",
  "length": 10,
  "width": 8,
  "grid": [[0, 0, ...], ...],
  "is_owner": true,
  "role": null,
  "rooms": [
    {"id": 1, "name": "Living Room"},
    {"id": 2, "name": "Kitchen"}
  ],
  "sensors_count": 5,
  "equipments_count": 8
}
```

**Errors**:
- `404`: House not found
- `403`: Access denied

---

### 2.4 Update House

Modify house information.

**Endpoint**: `PUT /api/houses/{id}`  
**Authentication**: Required (owner only)  
**Handler**: `HouseDetailHandler` (`houses_api.py`)

**Request Body**:
```json
{
  "name": "Updated Home Name",
  "address": "New Address, Paris"
}
```

**Note**: `length` and `width` cannot be changed after creation.

**Response** (200 OK):
```json
{
  "message": "House updated successfully",
  "house": {
    "id": 1,
    "name": "Updated Home Name",
    "address": "New Address, Paris"
  }
}
```

**Errors**:
- `403`: Only owner can update house
- `404`: House not found

---

### 2.5 Delete House

Delete a house and all associated data (cascade).

**Endpoint**: `DELETE /api/houses/{id}`  
**Authentication**: Required (owner only)  
**Handler**: `HouseDetailHandler` (`houses_api.py`)

**Response** (200 OK):
```json
{
  "message": "House deleted successfully"
}
```

**Cascade Deletes**:
- All rooms
- All sensors
- All equipments
- All automation rules
- All members
- All event history
- All user positions

**Errors**:
- `403`: Only owner can delete house
- `404`: House not found

---

### 2.6 List Rooms

Get all rooms in a house.

**Endpoint**: `GET /api/houses/{id}/rooms`  
**Authentication**: Required  
**Handler**: `RoomsHandler` (`houses_api.py`)

**Response** (200 OK):
```json
{
  "rooms": [
    {
      "id": 1,
      "name": "Living Room",
      "house_id": 1
    },
    {
      "id": 2,
      "name": "Kitchen",
      "house_id": 1
    }
  ]
}
```

---

### 2.7 Create Room

Add a new room to a house.

**Endpoint**: `POST /api/houses/{id}/rooms`  
**Authentication**: Required (owner/admin)  
**Handler**: `RoomsHandler` (`houses_api.py`)

**Request Body**:
```json
{
  "name": "Bedroom"
}
```

**Response** (201 Created):
```json
{
  "message": "Room created successfully",
  "room": {
    "id": 3,
    "name": "Bedroom",
    "house_id": 1
  }
}
```

---

### 2.8 Delete Room

Remove a room (cascade delete sensors/equipments).

**Endpoint**: `DELETE /api/rooms/{id}`  
**Authentication**: Required (owner/admin)  
**Handler**: `RoomDetailHandler` (`houses_api.py`)

**Response** (200 OK):
```json
{
  "message": "Room deleted successfully"
}
```

---

## 3. Sensors (IoT)

### 3.1 List Sensors

Get all sensors for a house.

**Endpoint**: `GET /api/houses/{id}/sensors`  
**Authentication**: Required  
**Handler**: `SensorsHandler` (`sensors.py`)

**Query Parameters**:
- `room_id` (optional): Filter by room
- `type` (optional): Filter by type (temperature, luminosity, rain, presence)

**Response** (200 OK):
```json
{
  "sensors": [
    {
      "id": 1,
      "name": "Living Room Temperature",
      "type": "temperature",
      "value": 22.5,
      "unit": "°C",
      "room_id": 1,
      "room_name": "Living Room",
      "is_active": true,
      "last_update": "2024-11-30T14:30:00Z"
    },
    {
      "id": 2,
      "name": "Kitchen Luminosity",
      "type": "luminosity",
      "value": 450,
      "unit": "lux",
      "room_id": 2,
      "room_name": "Kitchen",
      "is_active": true,
      "last_update": "2024-11-30T14:25:00Z"
    }
  ]
}
```

---

### 3.2 Create Sensor

Add a new sensor to a house.

**Endpoint**: `POST /api/sensors`  
**Authentication**: Required (owner/admin)  
**Handler**: `SensorsHandler` (`sensors.py`)

**Request Body**:
```json
{
  "house_id": 1,
  "room_id": 1,
  "name": "Bedroom Temperature Sensor",
  "type": "temperature",
  "value": 20.0
}
```

**Sensor Types**:
- `temperature`: Temperature sensor (°C)
- `luminosity`: Light sensor (lux)
- `rain`: Rain detector (%)
- `presence`: Motion detector (boolean)

**Response** (201 Created):
```json
{
  "message": "Sensor created successfully",
  "sensor": {
    "id": 3,
    "name": "Bedroom Temperature Sensor",
    "type": "temperature",
    "value": 20.0,
    "unit": "°C",
    "house_id": 1,
    "room_id": 1,
    "is_active": true
  }
}
```

---

### 3.3 Get Sensor Details

Get information about a specific sensor.

**Endpoint**: `GET /api/sensors/{id}`  
**Authentication**: Required  
**Handler**: `SensorDetailHandler` (`sensors.py`)

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "Living Room Temperature",
  "type": "temperature",
  "value": 22.5,
  "unit": "°C",
  "house_id": 1,
  "room_id": 1,
  "room_name": "Living Room",
  "is_active": true,
  "last_update": "2024-11-30T14:30:00Z"
}
```

---

### 3.4 Update Sensor

Modify sensor information.

**Endpoint**: `PUT /api/sensors/{id}`  
**Authentication**: Required (owner/admin)  
**Handler**: `SensorDetailHandler` (`sensors.py`)

**Request Body**:
```json
{
  "name": "Updated Sensor Name",
  "is_active": false
}
```

**Response** (200 OK):
```json
{
  "message": "Sensor updated successfully",
  "sensor": {
    "id": 1,
    "name": "Updated Sensor Name",
    "is_active": false
  }
}
```

---

### 3.5 Update Sensor Value

Update sensor reading value.

**Endpoint**: `PATCH /api/sensors/{id}/value`  
**Authentication**: Required  
**Handler**: `SensorDetailHandler` (`sensors.py`)

**Request Body**:
```json
{
  "value": 25.5
}
```

**Response** (200 OK):
```json
{
  "message": "Sensor value updated",
  "sensor": {
    "id": 1,
    "value": 25.5,
    "last_update": "2024-11-30T15:00:00Z"
  }
}
```

**WebSocket Broadcast**: Sends `sensor_update` message to all connected clients.

---

### 3.6 Delete Sensor

Remove a sensor.

**Endpoint**: `DELETE /api/sensors/{id}`  
**Authentication**: Required (owner/admin)  
**Handler**: `SensorDetailHandler` (`sensors.py`)

**Response** (200 OK):
```json
{
  "message": "Sensor deleted successfully"
}
```

---

## 4. Equipments

### 4.1 List Equipments

Get all equipments for a house.

**Endpoint**: `GET /api/houses/{id}/equipments`  
**Authentication**: Required  
**Handler**: `EquipmentsHandler` (`equipments.py`)

**Query Parameters**:
- `room_id` (optional): Filter by room
- `type` (optional): Filter by type

**Response** (200 OK):
```json
{
  "equipments": [
    {
      "id": 1,
      "name": "Living Room Shutter",
      "type": "shutter",
      "state": "open",
      "room_id": 1,
      "room_name": "Living Room",
      "is_active": true,
      "allowed_roles": ["admin", "occupant"],
      "last_update": "2024-11-30T14:30:00Z"
    },
    {
      "id": 2,
      "name": "Kitchen Light",
      "type": "light",
      "state": "on",
      "room_id": 2,
      "room_name": "Kitchen",
      "is_active": true,
      "allowed_roles": null,
      "last_update": "2024-11-30T14:25:00Z"
    }
  ]
}
```

---

### 4.2 Create Equipment

Add a new equipment to a house.

**Endpoint**: `POST /api/equipments`  
**Authentication**: Required (owner/admin)  
**Handler**: `EquipmentsHandler` (`equipments.py`)

**Request Body**:
```json
{
  "house_id": 1,
  "room_id": 1,
  "name": "Main Door",
  "type": "door",
  "allowed_roles": ["admin"]
}
```

**Equipment Types**:
- `shutter`: Roller shutter (states: open/closed)
- `door`: Door (states: open/closed)
- `light`: Light (states: on/off)
- `sound_system`: Sound system (states: on/off)

**Response** (201 Created):
```json
{
  "message": "Equipment created successfully",
  "equipment": {
    "id": 3,
    "name": "Main Door",
    "type": "door",
    "state": "closed",
    "house_id": 1,
    "room_id": 1,
    "allowed_roles": ["admin"],
    "is_active": true
  }
}
```

---

### 4.3 Get Equipment Details

Get information about a specific equipment.

**Endpoint**: `GET /api/equipments/{id}`  
**Authentication**: Required  
**Handler**: `EquipmentDetailHandler` (`equipments.py`)

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "Living Room Shutter",
  "type": "shutter",
  "state": "open",
  "house_id": 1,
  "room_id": 1,
  "room_name": "Living Room",
  "is_active": true,
  "allowed_roles": ["admin", "occupant"],
  "last_update": "2024-11-30T14:30:00Z"
}
```

---

### 4.4 Update Equipment

Modify equipment information.

**Endpoint**: `PUT /api/equipments/{id}`  
**Authentication**: Required (owner/admin)  
**Handler**: `EquipmentDetailHandler` (`equipments.py`)

**Request Body**:
```json
{
  "name": "Updated Equipment Name",
  "is_active": true
}
```

**Response** (200 OK):
```json
{
  "message": "Equipment updated successfully",
  "equipment": {
    "id": 1,
    "name": "Updated Equipment Name",
    "is_active": true
  }
}
```

---

### 4.5 Control Equipment

Change equipment state.

**Endpoint**: `POST /api/equipments/{id}/control`  
**Authentication**: Required  
**Handler**: `EquipmentControlHandler` (`equipments.py`)

**Request Body**:
```json
{
  "state": "closed"
}
```

**Valid States by Type**:
- `shutter`, `door`: "open" or "closed"
- `light`, `sound_system`: "on" or "off"

**Response** (200 OK):
```json
{
  "message": "Equipment controlled successfully",
  "equipment": {
    "id": 1,
    "name": "Living Room Shutter",
    "state": "closed",
    "last_update": "2024-11-30T15:00:00Z"
  }
}
```

**WebSocket Broadcast**: Sends `equipment_update` message to all connected clients.

**Errors**:
- `403`: User does not have permission to control this equipment
- `400`: Invalid state for equipment type

---

### 4.6 Update Equipment Roles

Modify allowed roles for equipment control.

**Endpoint**: `PUT /api/equipments/{id}/roles`  
**Authentication**: Required (owner only)  
**Handler**: `EquipmentRolesHandler` (`equipments.py`)

**Request Body**:
```json
{
  "allowed_roles": ["admin"]
}
```

**Response** (200 OK):
```json
{
  "message": "Equipment roles updated successfully",
  "equipment": {
    "id": 1,
    "allowed_roles": ["admin"]
  }
}
```

**Notes**:
- `null` or empty array: Everyone can control
- Owner always has control regardless of roles

---

### 4.7 Delete Equipment

Remove an equipment.

**Endpoint**: `DELETE /api/equipments/{id}`  
**Authentication**: Required (owner/admin)  
**Handler**: `EquipmentDetailHandler` (`equipments.py`)

**Response** (200 OK):
```json
{
  "message": "Equipment deleted successfully"
}
```

---

## 5. Automation Rules

### 5.1 List Automation Rules

Get all automation rules for a house.

**Endpoint**: `GET /api/houses/{id}/automation`  
**Authentication**: Required  
**Handler**: `AutomationRulesHandler` (`automation_rules.py`)

**Response** (200 OK):
```json
{
  "rules": [
    {
      "id": 1,
      "name": "Close shutters when hot",
      "description": "Close shutters when temperature exceeds 28°C",
      "is_active": true,
      "sensor_id": 1,
      "sensor_name": "Living Room Temperature",
      "condition_operator": ">",
      "condition_value": 28.0,
      "equipment_id": 1,
      "equipment_name": "Living Room Shutter",
      "action_state": "closed",
      "created_at": "2024-11-25T10:00:00Z",
      "last_triggered": "2024-11-30T14:00:00Z"
    }
  ]
}
```

---

### 5.2 Create Automation Rule

Add a new automation rule.

**Endpoint**: `POST /api/automation/rules`  
**Authentication**: Required (owner/admin)  
**Handler**: `AutomationRulesHandler` (`automation_rules.py`)

**Request Body**:
```json
{
  "house_id": 1,
  "name": "Turn on lights when dark",
  "description": "Automatically turn on lights when luminosity is low",
  "sensor_id": 2,
  "condition_operator": "<",
  "condition_value": 200,
  "equipment_id": 2,
  "action_state": "on",
  "is_active": true
}
```

**Operators**: `>`, `<`, `>=`, `<=`, `==`, `!=`

**Response** (201 Created):
```json
{
  "message": "Automation rule created successfully",
  "rule": {
    "id": 2,
    "name": "Turn on lights when dark",
    "is_active": true
  }
}
```

---

### 5.3 Update Automation Rule

Modify an automation rule.

**Endpoint**: `PUT /api/automation/rules/{id}`  
**Authentication**: Required (owner/admin)  
**Handler**: `AutomationRuleDetailHandler` (`automation_rules.py`)

**Request Body**:
```json
{
  "name": "Updated Rule Name",
  "is_active": false
}
```

**Response** (200 OK):
```json
{
  "message": "Automation rule updated successfully"
}
```

---

### 5.4 Delete Automation Rule

Remove an automation rule.

**Endpoint**: `DELETE /api/automation/rules/{id}`  
**Authentication**: Required (owner/admin)  
**Handler**: `AutomationRuleDetailHandler` (`automation_rules.py`)

**Response** (200 OK):
```json
{
  "message": "Automation rule deleted successfully"
}
```

---

### 5.5 Trigger Automation

Manually execute all active automation rules.

**Endpoint**: `POST /api/automation/trigger`  
**Authentication**: Required  
**Handler**: `AutomationTriggerHandler` (`automation.py`)

**Response** (200 OK):
```json
{
  "message": "Automation triggered successfully",
  "results": [
    {
      "rule_id": 1,
      "rule_name": "Close shutters when hot",
      "triggered": true,
      "reason": "temperature (25.5°C) > 28°C",
      "action": "Set Living Room Shutter to closed"
    },
    {
      "rule_id": 2,
      "rule_name": "Turn on lights when dark",
      "triggered": false,
      "reason": "luminosity (450 lux) < 200",
      "action": null
    }
  ],
  "triggered_count": 1,
  "total_rules": 2
}
```

**WebSocket Broadcast**: Sends `automation_triggered` message for each triggered rule.

---

## 6. House Members

### 6.1 List House Members

Get all members of a house.

**Endpoint**: `GET /api/houses/{id}/members`  
**Authentication**: Required  
**Handler**: `HouseMembersHandler` (`house_members.py`)

**Response** (200 OK):
```json
{
  "members": [
    {
      "id": 1,
      "user_id": 2,
      "username": "alice",
      "email": "alice@example.com",
      "role": "administrateur",
      "status": "accepted",
      "invited_by": 1,
      "invited_at": "2024-11-20T10:00:00Z",
      "accepted_at": "2024-11-20T10:30:00Z"
    }
  ],
  "owner": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

---

### 6.2 Invite Member

Send invitation to join house.

**Endpoint**: `POST /api/houses/{id}/invite`  
**Authentication**: Required (owner/admin)  
**Handler**: `HouseMembersHandler` (`house_members.py`)

**Request Body**:
```json
{
  "user_id": 3,
  "role": "occupant"
}
```

**Roles**: `administrateur`, `occupant`

**Response** (201 Created):
```json
{
  "message": "Invitation sent successfully",
  "invitation": {
    "id": 2,
    "user_id": 3,
    "role": "occupant",
    "status": "pending"
  }
}
```

---

### 6.3 Update Member Role

Change member's role.

**Endpoint**: `PUT /api/members/{id}/role`  
**Authentication**: Required (owner only)  
**Handler**: `MemberDetailHandler` (`house_members.py`)

**Request Body**:
```json
{
  "role": "administrateur"
}
```

**Response** (200 OK):
```json
{
  "message": "Member role updated successfully"
}
```

---

### 6.4 Remove Member

Remove member from house.

**Endpoint**: `DELETE /api/members/{id}`  
**Authentication**: Required (owner/admin)  
**Handler**: `MemberDetailHandler` (`house_members.py`)

**Response** (200 OK):
```json
{
  "message": "Member removed successfully"
}
```

---

### 6.5 My Invitations

Get all pending invitations for current user.

**Endpoint**: `GET /api/invitations`  
**Authentication**: Required  
**Handler**: `MyInvitationsHandler` (`invitations.py`)

**Response** (200 OK):
```json
{
  "invitations": [
    {
      "id": 1,
      "house_id": 5,
      "house_name": "Beach House",
      "role": "occupant",
      "invited_by": 3,
      "inviter_username": "bob",
      "invited_at": "2024-11-29T10:00:00Z",
      "status": "pending"
    }
  ]
}
```

---

### 6.6 Accept Invitation

Accept house invitation.

**Endpoint**: `POST /api/invitations/{id}/accept`  
**Authentication**: Required  
**Handler**: `AcceptInvitationHandler` (`invitations.py`)

**Response** (200 OK):
```json
{
  "message": "Invitation accepted successfully"
}
```

---

### 6.7 Reject Invitation

Reject house invitation.

**Endpoint**: `POST /api/invitations/{id}/reject`  
**Authentication**: Required  
**Handler**: `RejectInvitationHandler` (`invitations.py`)

**Response** (200 OK):
```json
{
  "message": "Invitation rejected successfully"
}
```

---

## 7. Event History

### 7.1 Get Event History

Retrieve event logs for a house.

**Endpoint**: `GET /api/houses/{id}/history`  
**Authentication**: Required  
**Handler**: `EventHistoryHandler` (`event_history.py`)

**Query Parameters**:
- `limit` (default: 50, max: 500): Number of events
- `offset` (default: 0): Pagination offset
- `event_type` (optional): Filter by type
- `user_id` (optional): Filter by user
- `days` (optional): Events from last N days

**Response** (200 OK):
```json
{
  "events": [
    {
      "id": 1,
      "event_type": "equipment_control",
      "entity_type": "equipment",
      "entity_id": 1,
      "description": "User john_doe closed Living Room Shutter",
      "metadata": {
        "previous_state": "open",
        "new_state": "closed"
      },
      "created_at": "2024-11-30T15:00:00Z",
      "user_id": 1,
      "username": "john_doe",
      "ip_address": "192.168.1.100"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

**Event Types**:
- `equipment_control`: Equipment state changed
- `sensor_reading`: Sensor value updated
- `member_action`: Member joined/left/role changed
- `automation_triggered`: Automation rule executed
- `house_modified`: House information updated

---

### 7.2 Get Event Statistics

Get statistics about house events.

**Endpoint**: `GET /api/houses/{id}/history/stats`  
**Authentication**: Required  
**Handler**: `EventStatsHandler` (`event_history.py`)

**Query Parameters**:
- `days` (default: 7): Period in days

**Response** (200 OK):
```json
{
  "total_events": 150,
  "period_days": 7,
  "by_type": {
    "equipment_control": 80,
    "sensor_reading": 50,
    "automation_triggered": 15,
    "member_action": 5
  },
  "by_user": {
    "1": 100,
    "2": 50
  },
  "by_day": {
    "2024-11-30": 50,
    "2024-11-29": 40,
    "2024-11-28": 30
  },
  "user_names": {
    "1": "john_doe",
    "2": "alice"
  }
}
```

---

### 7.3 Cleanup Event History

Manually trigger history cleanup (owner only).

**Endpoint**: `POST /api/houses/{id}/history/cleanup`  
**Authentication**: Required (owner only)  
**Handler**: `EventCleanupHandler` (`event_history.py`)

**Response** (200 OK):
```json
{
  "success": true,
  "cleanup_result": {
    "deleted": 500,
    "total_before": 2744,
    "total_after": 800,
    "target": 800,
    "reason": "automatic_cleanup"
  }
}
```

**Cleanup Strategy**:
- Keeps all events from last 7 days
- Keeps important events up to 90 days
- Deletes low-priority events older than 7 days
- If total > 1000, deletes oldest until reaching 800 (80% of max)

---

### 7.4 Get Event Types

List available event and entity types.

**Endpoint**: `GET /api/event-types`  
**Authentication**: Required  
**Handler**: `EventTypesHandler` (`event_history.py`)

**Response** (200 OK):
```json
{
  "event_types": {
    "equipment_control": "Contrôle d'équipement",
    "sensor_reading": "Lecture de capteur",
    "member_action": "Action de membre",
    "automation_triggered": "Automatisation déclenchée",
    "house_modified": "Maison modifiée"
  },
  "entity_types": {
    "equipment": "Équipement",
    "sensor": "Capteur",
    "member": "Membre",
    "automation_rule": "Règle d'automatisation",
    "house": "Maison",
    "room": "Pièce"
  }
}
```

---

## 8. User Positions

### 8.1 Get User Positions

Get current positions of all users in a house.

**Endpoint**: `GET /api/houses/{id}/positions`  
**Authentication**: Required  
**Handler**: `UserPositionHandler` (`user_positions.py`)

**Response** (200 OK):
```json
{
  "positions": [
    {
      "user_id": 1,
      "username": "john_doe",
      "profile_image": "/media/profile_images/user_1.jpg",
      "x": 5,
      "y": 3,
      "last_update": "2024-11-30T15:00:00Z"
    }
  ]
}
```

---

### 8.2 Update User Position

Update current user's position (movement simulation).

**Endpoint**: `POST /api/houses/{id}/positions`  
**Authentication**: Required  
**Handler**: `UserPositionHandler` (`user_positions.py`)

**Request Body**:
```json
{
  "x": 7,
  "y": 4
}
```

**Response** (200 OK):
```json
{
  "message": "Position updated successfully",
  "position": {
    "user_id": 1,
    "x": 7,
    "y": 4,
    "last_update": "2024-11-30T15:05:00Z"
  }
}
```

**WebSocket Broadcast**: Sends `user_position` message to all connected clients.

---

## 9. Weather Service

### 9.1 Get Weather

Get current weather for house location.

**Endpoint**: `GET /api/weather/{house_id}`  
**Authentication**: Required  
**Handler**: `WeatherHandler` (`weather.py`)

**Response** (200 OK):
```json
{
  "house_id": 1,
  "house_name": "My Smart Home",
  "address": "15 Rue de la Paix, Paris, France",
  "weather": {
    "temperature": 18.5,
    "humidity": 65,
    "wind_speed": 12.5,
    "weather_code": 3,
    "condition": "Nuageux",
    "icon": "cloudy"
  },
  "timestamp": "2024-11-30T15:00:00Z"
}
```

**Weather Codes** (WMO):
- `0`: Clear sky
- `1,2,3`: Mainly clear, partly cloudy
- `45,48`: Fog
- `51-55`: Drizzle
- `61-65`: Rain
- `71-75`: Snow

**Errors**:
- `400`: House has no address configured
- `500`: Weather API unavailable

---

### 9.2 Validate Address

Validate and geocode an address.

**Endpoint**: `POST /api/weather/validate-address`  
**Authentication**: Required  
**Handler**: `ValidateAddressHandler` (`weather.py`)

**Request Body**:
```json
{
  "address": "15 Rue de la Paix, Paris, France"
}
```

**Response** (200 OK):
```json
{
  "valid": true,
  "location": "Paris, Île-de-France, France",
  "latitude": 48.8698,
  "longitude": 2.3316,
  "country": "France",
  "timezone": "Europe/Paris"
}
```

**Response** (Invalid):
```json
{
  "valid": false,
  "message": "Address not found"
}
```

---

## 10. WebSocket

### 10.1 Connection

Connect to house real-time updates.

**URL**: `ws://localhost:8001/ws/{house_id}`  
**Authentication**: Cookie-based  
**Handler**: `HouseWebSocketHandler` (`websocket.py`)

**Connection**:
```javascript
const ws = new WebSocket(`ws://localhost:8001/ws/${houseId}`);

ws.onopen = () => {
    console.log('Connected to house updates');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleMessage(data);
};

ws.onclose = () => {
    console.log('Disconnected');
    // Implement reconnection logic
};
```

---

### 10.2 Message Types

#### Equipment Update
```json
{
  "type": "equipment_update",
  "equipment": {
    "id": 1,
    "name": "Living Room Shutter",
    "state": "closed",
    "last_update": "2024-11-30T15:00:00Z"
  }
}
```

#### Sensor Update
```json
{
  "type": "sensor_update",
  "sensor": {
    "id": 1,
    "name": "Living Room Temperature",
    "value": 25.5,
    "unit": "°C",
    "last_update": "2024-11-30T15:00:00Z"
  }
}
```

#### User Position
```json
{
  "type": "user_position",
  "position": {
    "user_id": 1,
    "username": "john_doe",
    "profile_image": "/media/profile_images/user_1.jpg",
    "x": 7,
    "y": 4,
    "last_update": "2024-11-30T15:00:00Z"
  }
}
```

#### Member Joined
```json
{
  "type": "member_joined",
  "member": {
    "user_id": 2,
    "username": "alice",
    "role": "occupant"
  }
}
```

#### Member Left
```json
{
  "type": "member_left",
  "user_id": 2
}
```

#### Automation Triggered
```json
{
  "type": "automation_triggered",
  "automation": {
    "rule_id": 1,
    "rule_name": "Close shutters when hot",
    "equipment_id": 1,
    "equipment_name": "Living Room Shutter",
    "action": "closed",
    "reason": "temperature (30°C) > 28°C"
  }
}
```

---

## Error Responses

All endpoints return structured error responses:

```json
{
  "error": "Description of the error",
  "code": "ERROR_CODE"
}
```

### Common HTTP Status Codes

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `204 No Content`: Request succeeded, no response body
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate)
- `500 Internal Server Error`: Server error

---

## Rate Limiting

**Current Status**: Not implemented  
**Future**: 100 requests per minute per user

---

## Changelog

### Version 3.0 (2024-11-30)
- Added event history with automatic cleanup
- Added house members management
- Added invitations system
- Added user positions tracking
- Added weather service integration
- Added WebSocket real-time updates
- Added automation rules CRUD
- Enhanced equipment permissions

### Version 2.0 (2024-11-25)
- Complete REST API implementation
- JWT authentication (optional)
- Async SQLAlchemy 2.0
- PostgreSQL migration

### Version 1.0 (2024-11-20)
- Initial release
- Basic CRUD operations

---

## Support

**Documentation**: See `PROJECT_REQUIREMENTS.md`  
**Repository**: https://github.com/Devid-yl/smarthome  
**Author**: David Yala

---

**Last Updated**: November 30, 2025  
**API Version**: 3.0
