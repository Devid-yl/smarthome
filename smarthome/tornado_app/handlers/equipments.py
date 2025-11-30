import json
import tornado.web
from sqlalchemy import select
from ..models import Equipment, EventHistory
from ..database import async_session_maker
from datetime import datetime
from .base import BaseAPIHandler



class EquipmentsListHandler(BaseAPIHandler):
    """GET /api/equipments - Liste tous les équipements
    POST /api/equipments - Créer un équipement"""

    async def get(self):
        """
        Récupérer tous les équipements.
        Optionnel: filtrer par room/house/type.
        """
        room_id = self.get_argument("room_id", None)
        house_id = self.get_argument("house_id", None)
        equipment_type = self.get_argument("type", None)

        async with async_session_maker() as session:
            query = select(Equipment)
            if room_id:
                query = query.where(Equipment.room_id == int(room_id))
            elif house_id:
                query = query.where(Equipment.house_id == int(house_id))
            if equipment_type:
                query = query.where(Equipment.type == equipment_type)

            result = await session.execute(query)
            equipments = result.scalars().all()

            equipments_data = [
                {
                    "id": e.id,
                    "house_id": e.house_id,
                    "room_id": e.room_id,
                    "name": e.name,
                    "type": e.type,
                    "state": e.state,
                    "is_active": e.is_active,
                    "allowed_roles": e.allowed_roles,
                    "last_update": e.last_update.isoformat()
                    if e.last_update else None
                }
                for e in equipments
            ]

            self.write_json({"equipments": equipments_data})

    async def post(self):
        """Créer un nouvel équipement"""
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.write_error_json("Invalid JSON")
            return

        required = ["house_id", "name", "type"]
        if not all(k in data for k in required):
            self.write_error_json(
                f"Missing required fields: {', '.join(required)}")
            return

        # Valider le type d'équipement
        valid_types = ["shutter", "door", "light", "sound_system"]
        if data["type"] not in valid_types:
            self.write_error_json(
                f"Invalid equipment type. Must be: {valid_types}")
            return

        async with async_session_maker() as session:
            new_equipment = Equipment(
                house_id=int(data["house_id"]),
                room_id=int(data["room_id"]) if data.get("room_id") else None,
                name=data["name"],
                type=data["type"],
                state=data.get("state", "off"),
                is_active=data.get("is_active", True),
                allowed_roles=data.get("allowed_roles")
            )
            session.add(new_equipment)
            await session.commit()
            await session.refresh(new_equipment)

            # Enregistrer dans l'historique
            user_id_cookie = self.get_secure_cookie("uid")
            user_id = int(user_id_cookie.decode()) if user_id_cookie else None
            event = EventHistory(
                house_id=new_equipment.house_id,
                user_id=user_id,
                event_type='equipment_control',
                entity_type='equipment',
                entity_id=new_equipment.id,
                description=(
                    f"Nouvel équipement ajouté: {new_equipment.name} "
                    f"({new_equipment.type})"
                ),
                event_metadata={
                    "action": "create",
                    "equipment_type": new_equipment.type,
                    "initial_state": new_equipment.state
                },
                ip_address=self.request.remote_ip
            )
            session.add(event)
            await session.commit()

            self.write_json({
                "id": new_equipment.id,
                "house_id": new_equipment.house_id,
                "room_id": new_equipment.room_id,
                "name": new_equipment.name,
                "type": new_equipment.type,
                "state": new_equipment.state,
                "is_active": new_equipment.is_active,
                "allowed_roles": new_equipment.allowed_roles
            }, status=201)


class EquipmentDetailHandler(BaseAPIHandler):
    """GET /api/equipments/{id} - Détails d'un équipement
    PUT /api/equipments/{id} - Mettre à jour un équipement
    DELETE /api/equipments/{id} - Supprimer un équipement"""

    async def get(self, equipment_id):
        """Récupérer les détails d'un équipement"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Equipment).where(Equipment.id == int(equipment_id))
            )
            equipment = result.scalar_one_or_none()

            if not equipment:
                self.write_error_json("Equipment not found", 404)
                return

            self.write_json({
                "id": equipment.id,
                "room_id": equipment.room_id,
                "name": equipment.name,
                "type": equipment.type,
                "state": equipment.state,
                "is_active": equipment.is_active,
                "allowed_roles": equipment.allowed_roles,
                "last_update": equipment.last_update.isoformat()
                if equipment.last_update else None
            })

    async def put(self, equipment_id):
        """Mettre à jour un équipement"""
        # Obtenir l'utilisateur courant depuis les cookies
        user_id_cookie = self.get_secure_cookie("uid")
        if not user_id_cookie:
            self.write_error_json("Not authenticated", 401)
            return
        user_id = int(user_id_cookie.decode())
        
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.write_error_json("Invalid JSON")
            return

        async with async_session_maker() as session:
            from ..utils.permissions import can_control_equipment
            
            result = await session.execute(
                select(Equipment).where(Equipment.id == int(equipment_id))
            )
            equipment = result.scalar_one_or_none()

            if not equipment:
                self.write_error_json("Equipment not found", 404)
                return

            # Vérifier les permissions de contrôle
            if not await can_control_equipment(
                session, user_id, equipment.house_id, equipment
            ):
                self.write_error_json("Access denied", 403)
                return

            # Suivre les changements pour l'historique
            changes = {}

            # Mise à jour des champs
            if "name" in data:
                changes["name"] = {
                    "old": equipment.name,
                    "new": data["name"]
                }
                equipment.name = data["name"]
            if "state" in data:
                changes["state"] = {
                    "old": equipment.state,
                    "new": data["state"]
                }
                equipment.state = data["state"]
            if "is_active" in data:
                changes["is_active"] = {
                    "old": equipment.is_active,
                    "new": data["is_active"]
                }
                equipment.is_active = data["is_active"]
            if "allowed_roles" in data:
                changes["allowed_roles"] = {
                    "old": equipment.allowed_roles,
                    "new": data["allowed_roles"]
                }
                equipment.allowed_roles = data["allowed_roles"]

            equipment.last_update = datetime.utcnow()

            # Enregistrer dans l'historique si changement d'état
            if changes:
                description_parts = []
                if "state" in changes:
                    old_s = changes['state']['old']
                    new_s = changes['state']['new']
                    description_parts.append(f"État: {old_s} → {new_s}")
                if "is_active" in changes:
                    old_a = changes['is_active']['old']
                    new_a = changes['is_active']['new']
                    description_parts.append(f"Actif: {old_a} → {new_a}")
                if "name" in changes:
                    description_parts.append("Nom modifié")
                
                desc = f"Équipement {equipment.name} modifié: "
                desc += ', '.join(description_parts)
                
                event = EventHistory(
                    house_id=equipment.house_id,
                    user_id=user_id,
                    event_type='equipment_control',
                    entity_type='equipment',
                    entity_id=equipment.id,
                    description=desc,
                    event_metadata={
                        "action": "update",
                        "changes": changes,
                        "equipment_type": equipment.type
                    },
                    ip_address=self.request.remote_ip
                )
                session.add(event)

            await session.commit()

            # Diffuser la mise à jour en temps réel via WebSocket
            print(
                f"[Equipment] Modification détectée: ID={equipment.id}, "
                f"state={equipment.state}, type={equipment.type}"
            )
            from .websocket import RealtimeHandler
            client_count = len(RealtimeHandler.clients)
            print(f"[Equipment] Clients WebSocket connectés: {client_count}")
            RealtimeHandler.broadcast_equipment_update(
                equipment.id,
                equipment.type,
                equipment.state,
                equipment.is_active,
                equipment.house_id
            )
            print(
                f"[Equipment] Broadcast envoyé pour "
                f"équipement ID={equipment.id}"
            )

            self.write_json({
                "id": equipment.id,
                "room_id": equipment.room_id,
                "name": equipment.name,
                "type": equipment.type,
                "state": equipment.state,
                "is_active": equipment.is_active,
                "last_update": equipment.last_update.isoformat()
            })

    async def delete(self, equipment_id):
        """Supprimer un équipement"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Equipment).where(Equipment.id == int(equipment_id))
            )
            equipment = result.scalar_one_or_none()

            if not equipment:
                self.write_error_json("Equipment not found", 404)
                return

            # Enregistrer dans l'historique avant suppression
            user_id_cookie = self.get_secure_cookie("uid")
            user_id = int(user_id_cookie.decode()) if user_id_cookie else None
            event = EventHistory(
                house_id=equipment.house_id,
                user_id=user_id,
                event_type='equipment_control',
                entity_type='equipment',
                entity_id=equipment.id,
                description=(
                    f"Équipement retiré: {equipment.name} "
                    f"({equipment.type})"
                ),
                event_metadata={
                    "action": "delete",
                    "equipment_type": equipment.type,
                    "final_state": equipment.state
                },
                ip_address=self.request.remote_ip
            )
            session.add(event)

            await session.delete(equipment)
            await session.commit()

            self.write_json({"message": "Equipment deleted successfully"})


# Handlers spécialisés par type d'équipement

class ShuttersHandler(BaseAPIHandler):
    """GET/PUT /api/volets - Contrôle des volets roulants"""

    async def get(self):
        """Liste tous les volets"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Equipment).where(Equipment.type == "shutter")
            )
            shutters = result.scalars().all()

            self.write_json({
                "volets": [
                    {
                        "id": s.id,
                        "room_id": s.room_id,
                        "name": s.name,
                        "state": s.state,
                        "is_active": s.is_active
                    }
                    for s in shutters
                ]
            })

    async def put(self):
        """Contrôler tous les volets (ouverture/fermeture globale)"""
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.write_error_json("Invalid JSON")
            return

        if "state" not in data:
            self.write_error_json("Missing 'state' field")
            return

        async with async_session_maker() as session:
            result = await session.execute(
                select(Equipment).where(Equipment.type == "shutter")
            )
            shutters = result.scalars().all()

            for shutter in shutters:
                shutter.state = data["state"]
                shutter.last_update = datetime.utcnow()

            await session.commit()

            self.write_json({
                "message": f"All shutters set to {data['state']}",
                "count": len(shutters)
            })


class DoorsHandler(BaseAPIHandler):
    """GET/PUT /api/portes - Contrôle des portes"""

    async def get(self):
        """Liste toutes les portes"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Equipment).where(Equipment.type == "door")
            )
            doors = result.scalars().all()

            self.write_json({
                "portes": [
                    {
                        "id": d.id,
                        "room_id": d.room_id,
                        "name": d.name,
                        "state": d.state,
                        "is_active": d.is_active
                    }
                    for d in doors
                ]
            })

    async def put(self):
        """Contrôler toutes les portes"""
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.write_error_json("Invalid JSON")
            return

        if "state" not in data:
            self.write_error_json("Missing 'state' field")
            return

        async with async_session_maker() as session:
            result = await session.execute(
                select(Equipment).where(Equipment.type == "door")
            )
            doors = result.scalars().all()

            for door in doors:
                door.state = data["state"]
                door.last_update = datetime.utcnow()

            await session.commit()

            self.write_json({
                "message": f"All doors set to {data['state']}",
                "count": len(doors)
            })


class LightsHandler(BaseAPIHandler):
    """GET/PUT /api/lumieres - Contrôle des lumières"""

    async def get(self):
        """Liste toutes les lumières"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Equipment).where(Equipment.type == "light")
            )
            lights = result.scalars().all()

            self.write_json({
                "lumieres": [
                    {
                        "id": light.id,
                        "room_id": light.room_id,
                        "name": light.name,
                        "state": light.state,
                        "is_active": light.is_active
                    }
                    for light in lights
                ]
            })

    async def put(self):
        """Contrôler toutes les lumières"""
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.write_error_json("Invalid JSON")
            return

        if "state" not in data:
            self.write_error_json("Missing 'state' field")
            return

        async with async_session_maker() as session:
            result = await session.execute(
                select(Equipment).where(Equipment.type == "light")
            )
            lights = result.scalars().all()

            for light in lights:
                light.state = data["state"]
                light.last_update = datetime.utcnow()

            await session.commit()

            self.write_json({
                "message": f"All lights set to {data['state']}",
                "count": len(lights)
            })


class SoundSystemHandler(BaseAPIHandler):
    """GET/PUT /api/sono - Contrôle du système sonore"""

    async def get(self):
        """Liste tous les systèmes sonores"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Equipment).where(Equipment.type == "sound_system")
            )
            sound_systems = result.scalars().all()

            self.write_json({
                "sono": [
                    {
                        "id": s.id,
                        "room_id": s.room_id,
                        "name": s.name,
                        "state": s.state,
                        "is_active": s.is_active
                    }
                    for s in sound_systems
                ]
            })

    async def put(self):
        """Contrôler tous les systèmes sonores"""
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.write_error_json("Invalid JSON")
            return

        if "state" not in data:
            self.write_error_json("Missing 'state' field")
            return

        async with async_session_maker() as session:
            result = await session.execute(
                select(Equipment).where(Equipment.type == "sound_system")
            )
            sound_systems = result.scalars().all()

            for system in sound_systems:
                system.state = data["state"]
                system.last_update = datetime.utcnow()

            await session.commit()

            self.write_json({
                "message": f"All sound systems set to {data['state']}",
                "count": len(sound_systems)
            })
