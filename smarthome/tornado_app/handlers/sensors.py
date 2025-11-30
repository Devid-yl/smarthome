import json
import tornado.web
from sqlalchemy import select
from ..models import Sensor, EventHistory
from ..database import async_session_maker
from datetime import datetime
from .websocket import RealtimeHandler
from .base import BaseAPIHandler



class SensorsListHandler(BaseAPIHandler):
    """GET /api/sensors - List all sensors
    POST /api/sensors - Create a sensor"""

    async def get(self):
        """
        Get all sensors.
        Optional: filter by room_id or house_id.
        """
        room_id = self.get_argument("room_id", None)
        house_id = self.get_argument("house_id", None)

        async with async_session_maker() as session:
            query = select(Sensor)
            if room_id:
                query = query.where(Sensor.room_id == int(room_id))
            elif house_id:
                query = query.where(Sensor.house_id == int(house_id))

            result = await session.execute(query)
            sensors = result.scalars().all()

            sensors_data = [
                {
                    "id": s.id,
                    "house_id": s.house_id,
                    "room_id": s.room_id,
                    "name": s.name,
                    "type": s.type,
                    "value": s.value,
                    "unit": s.unit,
                    "is_active": s.is_active,
                    "last_update": s.last_update.isoformat()
                    if s.last_update else None
                }
                for s in sensors
            ]

            self.write_json({"sensors": sensors_data})

    async def post(self):
        """Create a new sensor."""
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

        # Validate sensor type
        valid_types = ["temperature", "luminosity", "rain", "presence"]
        if data["type"] not in valid_types:
            self.write_error_json(
                f"Invalid sensor type. Must be one of: {valid_types}")
            return

        async with async_session_maker() as session:
            new_sensor = Sensor(
                house_id=data["house_id"],
                room_id=data.get("room_id"),
                name=data["name"],
                type=data["type"],
                value=data.get("value", 0.0),
                unit=data.get("unit", self._get_default_unit(data["type"])),
                is_active=data.get("is_active", True)
            )
            session.add(new_sensor)
            await session.commit()
            await session.refresh(new_sensor)

            # Record to event history
            user_id_cookie = self.get_secure_cookie("uid")
            user_id = int(user_id_cookie.decode()) if user_id_cookie else None
            event = EventHistory(
                house_id=new_sensor.house_id,
                user_id=user_id,
                event_type='sensor_reading',
                entity_type='sensor',
                entity_id=new_sensor.id,
                description=(
                    f"Nouveau capteur ajouté: {new_sensor.name} "
                    f"({new_sensor.type})"
                ),
                event_metadata={
                    "action": "create",
                    "sensor_type": new_sensor.type,
                    "initial_value": new_sensor.value,
                    "unit": new_sensor.unit
                },
                ip_address=self.request.remote_ip
            )
            session.add(event)
            await session.commit()

            self.write_json({
                "id": new_sensor.id,
                "house_id": new_sensor.house_id,
                "room_id": new_sensor.room_id,
                "name": new_sensor.name,
                "type": new_sensor.type,
                "value": new_sensor.value,
                "unit": new_sensor.unit,
                "is_active": new_sensor.is_active
            }, status=201)

    def _get_default_unit(self, sensor_type):
        units = {
            "temperature": "°C",
            "luminosity": "lux",
            "rain": "%",
            "presence": "bool"
        }
        return units.get(sensor_type, "")


class SensorDetailHandler(BaseAPIHandler):
    """GET /api/sensors/{id} - Sensor details
    PUT /api/sensors/{id} - Update a sensor
    DELETE /api/sensors/{id} - Delete a sensor"""

    async def get(self, sensor_id):
        """Get sensor details."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Sensor).where(Sensor.id == int(sensor_id))
            )
            sensor = result.scalar_one_or_none()

            if not sensor:
                self.write_error_json("Sensor not found", 404)
                return

            self.write_json({
                "id": sensor.id,
                "house_id": sensor.house_id,
                "room_id": sensor.room_id,
                "name": sensor.name,
                "type": sensor.type,
                "value": sensor.value,
                "unit": sensor.unit,
                "is_active": sensor.is_active,
                "last_update": sensor.last_update.isoformat()
                if sensor.last_update else None
            })

    async def put(self, sensor_id):
        """Mettre à jour un capteur (valeur, état, etc.)"""
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.write_error_json("Invalid JSON")
            return

        async with async_session_maker() as session:
            result = await session.execute(
                select(Sensor).where(Sensor.id == int(sensor_id))
            )
            sensor = result.scalar_one_or_none()

            if not sensor:
                self.write_error_json("Sensor not found", 404)
                return

            # Suivre les changements pour l'historique
            changes = {}

            # Mise à jour des champs
            if "name" in data:
                changes["name"] = {
                    "old": sensor.name,
                    "new": data["name"]
                }
                sensor.name = data["name"]
            if "value" in data:
                changes["value"] = {
                    "old": sensor.value,
                    "new": data["value"]
                }
                sensor.value = data["value"]
            if "is_active" in data:
                changes["is_active"] = {
                    "old": sensor.is_active,
                    "new": data["is_active"]
                }
                sensor.is_active = data["is_active"]
            if "unit" in data:
                changes["unit"] = {
                    "old": sensor.unit,
                    "new": data["unit"]
                }
                sensor.unit = data["unit"]

            sensor.last_update = datetime.utcnow()

            # Enregistrer dans l'historique
            if changes:
                user_id_cookie = self.get_secure_cookie("uid")
                user_id = int(user_id_cookie.decode()) \
                    if user_id_cookie else None
                
                description_parts = []
                if "value" in changes:
                    old_v = changes['value']['old']
                    new_v = changes['value']['new']
                    description_parts.append(
                        f"Valeur: {old_v} → {new_v}"
                    )
                if "is_active" in changes:
                    old_a = changes['is_active']['old']
                    new_a = changes['is_active']['new']
                    description_parts.append(f"Actif: {old_a} → {new_a}")
                if "name" in changes or "unit" in changes:
                    description_parts.append("Configuration modifiée")
                
                desc = f"Capteur {sensor.name} modifié: "
                desc += ', '.join(description_parts)
                
                event = EventHistory(
                    house_id=sensor.house_id,
                    user_id=user_id,
                    event_type='sensor_reading',
                    entity_type='sensor',
                    entity_id=sensor.id,
                    description=desc,
                    event_metadata={
                        "action": "update",
                        "changes": changes,
                        "sensor_type": sensor.type
                    },
                    ip_address=self.request.remote_ip
                )
                session.add(event)

            await session.commit()

            # Diffuser la mise à jour en temps réel via WebSocket
            if "value" in changes or "is_active" in changes:
                RealtimeHandler.broadcast_sensor_update(
                    sensor.id,
                    sensor.value,
                    sensor.is_active,
                    sensor.house_id
                )

            self.write_json({
                "id": sensor.id,
                "room_id": sensor.room_id,
                "name": sensor.name,
                "type": sensor.type,
                "value": sensor.value,
                "unit": sensor.unit,
                "is_active": sensor.is_active,
                "last_update": sensor.last_update.isoformat()
            })

    async def delete(self, sensor_id):
        """Supprimer un capteur"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Sensor).where(Sensor.id == int(sensor_id))
            )
            sensor = result.scalar_one_or_none()

            if not sensor:
                self.write_error_json("Sensor not found", 404)
                return

            # Enregistrer dans l'historique avant suppression
            user_id_cookie = self.get_secure_cookie("uid")
            user_id = int(user_id_cookie.decode()) if user_id_cookie else None
            event = EventHistory(
                house_id=sensor.house_id,
                user_id=user_id,
                event_type='sensor_reading',
                entity_type='sensor',
                entity_id=sensor.id,
                description=(
                    f"Capteur retiré: {sensor.name} "
                    f"({sensor.type})"
                ),
                event_metadata={
                    "action": "delete",
                    "sensor_type": sensor.type,
                    "final_value": sensor.value
                },
                ip_address=self.request.remote_ip
            )
            session.add(event)

            await session.delete(sensor)
            await session.commit()

            self.write_json({"message": "Sensor deleted successfully"})


class SensorValueHandler(BaseAPIHandler):
    """PUT /api/sensors/{id}/value - Mettre à jour uniquement la valeur"""

    async def put(self, sensor_id):
        """Mettre à jour la valeur d'un capteur (endpoint rapide)"""
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.write_error_json("Invalid JSON")
            return

        if "value" not in data:
            self.write_error_json("Missing 'value' field")
            return

        async with async_session_maker() as session:
            result = await session.execute(
                select(Sensor).where(Sensor.id == int(sensor_id))
            )
            sensor = result.scalar_one_or_none()

            if not sensor:
                self.write_error_json("Sensor not found", 404)
                return

            old_value = sensor.value
            sensor.value = data["value"]
            sensor.last_update = datetime.utcnow()

            # Enregistrer dans l'historique (si changement significatif)
            if old_value != data["value"]:
                user_id_cookie = self.get_secure_cookie("uid")
                user_id = int(user_id_cookie.decode()) \
                    if user_id_cookie else None
                event = EventHistory(
                    house_id=sensor.house_id,
                    user_id=user_id,
                    event_type='sensor_reading',
                    entity_type='sensor',
                    entity_id=sensor.id,
                    description=(
                        f"Capteur {sensor.name}: "
                        f"{old_value} → {data['value']} {sensor.unit}"
                    ),
                    event_metadata={
                        "action": "value_update",
                        "sensor_type": sensor.type,
                        "old_value": old_value,
                        "new_value": data["value"]
                    },
                    ip_address=self.request.remote_ip
                )
                session.add(event)

            await session.commit()

            # Diffuser la mise à jour en temps réel via WebSocket
            RealtimeHandler.broadcast_sensor_update(
                sensor.id,
                sensor.value,
                sensor.is_active,
                sensor.house_id
            )

            self.write_json({
                "id": sensor.id,
                "type": sensor.type,
                "value": sensor.value,
                "unit": sensor.unit,
                "last_update": sensor.last_update.isoformat()
            })
