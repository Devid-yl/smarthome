"""
Business Logic B2B: Communication Sensors → Equipments
Logique d'automatisation basée sur les données des capteurs
"""
import json
import tornado.web
from sqlalchemy import select
from ..models import Sensor, Equipment, EventHistory
from ..database import async_session_maker
from datetime import datetime
from .base import BaseAPIHandler



class AutomationRulesHandler(BaseAPIHandler):
    """
    POST /api/automation/trigger - Déclencher l'automatisation
    Analyse les capteurs et contrôle les équipements selon des règles
    """

    async def post(self):
        """
        Logique B2B principale:
        1. Appliquer les règles personnalisées (DB)
        2. Appliquer les règles par défaut (hard-codées)
        """
        actions_taken = []

        async with async_session_maker() as session:
            # ÉTAPE 1: Appliquer les règles personnalisées
            from ..models import AutomationRule
            
            result = await session.execute(
                select(AutomationRule).where(
                    AutomationRule.is_active == True  # noqa
                )
            )
            custom_rules = result.scalars().all()
            
            for rule in custom_rules:
                # Retrieve le capteur
                sensor = await session.get(Sensor, rule.sensor_id)
                if not sensor or not sensor.is_active or sensor.value is None:
                    continue
                
                # Évaluer la condition
                condition_met = False
                if rule.condition_operator == '>':
                    condition_met = sensor.value > rule.condition_value
                elif rule.condition_operator == '<':
                    condition_met = sensor.value < rule.condition_value
                elif rule.condition_operator == '>=':
                    condition_met = sensor.value >= rule.condition_value
                elif rule.condition_operator == '<=':
                    condition_met = sensor.value <= rule.condition_value
                elif rule.condition_operator == '==':
                    condition_met = sensor.value == rule.condition_value
                elif rule.condition_operator == '!=':
                    condition_met = sensor.value != rule.condition_value
                
                # Appliquer l'action si condition vraie
                if condition_met:
                    equipment = await session.get(Equipment, rule.equipment_id)
                    if equipment and equipment.is_active:
                        if equipment.state != rule.action_state:
                            old_state = equipment.state
                            equipment.state = rule.action_state
                            equipment.last_update = datetime.utcnow()
                            rule.last_triggered = datetime.utcnow()
                            
                            # Enregistrer dans l'historique
                            event = EventHistory(
                                house_id=equipment.house_id,
                                user_id=None,  # Action automatique
                                event_type='automation_triggered',
                                entity_type='automation_rule',
                                entity_id=rule.id,
                                description=(
                                    f"Règle '{rule.name}' déclenchée: "
                                    f"{equipment.name} {old_state} → "
                                    f"{rule.action_state}"
                                ),
                                event_metadata={
                                    "rule_name": rule.name,
                                    "sensor_id": sensor.id,
                                    "sensor_name": sensor.name,
                                    "sensor_value": sensor.value,
                                    "condition": (
                                        f"{rule.condition_operator} "
                                        f"{rule.condition_value}"
                                    ),
                                    "equipment_id": equipment.id,
                                    "equipment_name": equipment.name,
                                    "old_state": old_state,
                                    "new_state": rule.action_state
                                }
                            )
                            session.add(event)
                            
                            actions_taken.append({
                                "action": f"set_{rule.action_state}",
                                "equipment_id": equipment.id,
                                "equipment_name": equipment.name,
                                "reason": (
                                    f"Custom rule: {rule.name} "
                                    f"({sensor.name} "
                                    f"{rule.condition_operator} "
                                    f"{rule.condition_value})"
                                ),
                                "rule_id": rule.id
                            })
            
            # ÉTAPE 2: Appliquer les règles par défaut
            # 1. Récupérer tous les capteurs actifs
            result = await session.execute(
                select(Sensor).where(Sensor.is_active == True)  # noqa
            )
            sensors = result.scalars().all()

            # 2. Récupérer tous les équipements actifs
            result = await session.execute(
                select(Equipment).where(Equipment.is_active == True)  # noqa
            )
            equipments = result.scalars().all()

            # Grouper par room_id pour logique locale
            sensors_by_room = {}
            equipments_by_room = {}

            for sensor in sensors:
                if sensor.room_id not in sensors_by_room:
                    sensors_by_room[sensor.room_id] = []
                sensors_by_room[sensor.room_id].append(sensor)

            for equipment in equipments:
                if equipment.room_id not in equipments_by_room:
                    equipments_by_room[equipment.room_id] = {}
                if equipment.type not in equipments_by_room[equipment.room_id]:
                    equipments_by_room[equipment.room_id][equipment.type] = []
                equipments_by_room[equipment.room_id][equipment.type].append(
                    equipment
                )

            # 3. Appliquer les règles par pièce
            for room_id, room_sensors in sensors_by_room.items():
                room_equips = equipments_by_room.get(room_id, {})

                for sensor in room_sensors:
                    # RÈGLE 1: Température → Volets
                    if sensor.type == "temperature" and sensor.value:
                        if sensor.value > 28:  # Trop chaud
                            for shutter in room_equips.get("shutter", []):
                                if shutter.state != "closed":
                                    shutter.state = "closed"
                                    shutter.last_update = datetime.utcnow()
                                    actions_taken.append({
                                        "action": "close_shutter",
                                        "equipment_id": shutter.id,
                                        "equipment_name": shutter.name,
                                        "reason": f"Temperature {sensor.value}°C > 28°C",  # noqa
                                        "room_id": room_id
                                    })

                    # RÈGLE 2: Luminosité → Lumières
                    if sensor.type == "luminosity" and sensor.value:
                        if sensor.value < 200:  # Trop sombre
                            for light in room_equips.get("light", []):
                                if light.state != "on":
                                    light.state = "on"
                                    light.last_update = datetime.utcnow()
                                    actions_taken.append({
                                        "action": "turn_on_light",
                                        "equipment_id": light.id,
                                        "equipment_name": light.name,
                                        "reason": f"Luminosity {sensor.value} lux < 200",  # noqa
                                        "room_id": room_id
                                    })
                        elif sensor.value > 500:  # Assez lumineux
                            for light in room_equips.get("light", []):
                                if light.state != "off":
                                    light.state = "off"
                                    light.last_update = datetime.utcnow()
                                    actions_taken.append({
                                        "action": "turn_off_light",
                                        "equipment_id": light.id,
                                        "equipment_name": light.name,
                                        "reason": f"Luminosity {sensor.value} lux > 500",  # noqa
                                        "room_id": room_id
                                    })

                    # RÈGLE 3: Pluie → Volets
                    if sensor.type == "rain" and sensor.value:
                        if sensor.value > 50:  # Pluie détectée (>50%)
                            for shutter in room_equips.get("shutter", []):
                                if shutter.state != "closed":
                                    shutter.state = "closed"
                                    shutter.last_update = datetime.utcnow()
                                    actions_taken.append({
                                        "action": "close_shutter",
                                        "equipment_id": shutter.id,
                                        "equipment_name": shutter.name,
                                        "reason": f"Rain detected {sensor.value}%",  # noqa
                                        "room_id": room_id
                                    })

                    # RÈGLE 4: Présence → Lumières + Sono
                    if sensor.type == "presence" and sensor.value:
                        if sensor.value == 1:  # Présence détectée
                            # Allumer les lumières
                            for light in room_equips.get("light", []):
                                if light.state != "on":
                                    light.state = "on"
                                    light.last_update = datetime.utcnow()
                                    actions_taken.append({
                                        "action": "turn_on_light",
                                        "equipment_id": light.id,
                                        "equipment_name": light.name,
                                        "reason": "Presence detected",
                                        "room_id": room_id
                                    })

                            # Activer le système sonore
                            for sono in room_equips.get("sound_system", []):
                                if sono.state != "on":
                                    sono.state = "on"
                                    sono.last_update = datetime.utcnow()
                                    actions_taken.append({
                                        "action": "turn_on_sound",
                                        "equipment_id": sono.id,
                                        "equipment_name": sono.name,
                                        "reason": "Presence detected",
                                        "room_id": room_id
                                    })
                        elif sensor.value == 0:  # Pas de présence
                            # Éteindre les lumières après un délai
                            for light in room_equips.get("light", []):
                                if light.state != "off":
                                    light.state = "off"
                                    light.last_update = datetime.utcnow()
                                    actions_taken.append({
                                        "action": "turn_off_light",
                                        "equipment_id": light.id,
                                        "equipment_name": light.name,
                                        "reason": "No presence detected",
                                        "room_id": room_id
                                    })

            # Sauvegarder toutes les modifications
            await session.commit()
            
            # Broadcaster les changements d'équipements via WebSocket
            from .websocket import RealtimeHandler
            for action in actions_taken:
                if action.get("equipment_id"):
                    # Retrieve l'équipement pour avoir son type et house_id
                    equip = await session.get(Equipment, action["equipment_id"])
                    if equip:
                        RealtimeHandler.broadcast_equipment_update(
                            equip.id,
                            equip.type,
                            equip.state,
                            equip.is_active,
                            equip.house_id
                        )

        self.write_json({
            "message": "Automation rules applied",
            "actions_count": len(actions_taken),
            "actions": actions_taken
        })


class PresenceHandler(BaseAPIHandler):
    """GET /api/presence - État de tous les capteurs de présence"""

    async def get(self):
        """Récupérer l'état de tous les capteurs de présence"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Sensor).where(Sensor.type == "presence")
            )
            presence_sensors = result.scalars().all()

            self.write_json({
                "presence_sensors": [
                    {
                        "id": s.id,
                        "room_id": s.room_id,
                        "name": s.name,
                        "detected": bool(s.value) if s.value else False,
                        "last_update": s.last_update.isoformat()
                        if s.last_update else None
                    }
                    for s in presence_sensors
                ]
            })


class SensorToEquipmentStatusHandler(BaseAPIHandler):
    """GET /api/status - Vue globale capteurs + équipements"""

    async def get(self):
        """Récupérer l'état global du système (capteurs + équipements)"""
        async with async_session_maker() as session:
            # Capteurs
            result = await session.execute(
                select(Sensor).where(Sensor.is_active == True)  # noqa
            )
            sensors = result.scalars().all()

            # Équipements
            result = await session.execute(
                select(Equipment).where(Equipment.is_active == True)  # noqa
            )
            equipments = result.scalars().all()

            self.write_json({
                "sensors": {
                    "count": len(sensors),
                    "by_type": self._count_by_type(sensors, "type"),
                    "details": [
                        {
                            "id": s.id,
                            "type": s.type,
                            "value": s.value,
                            "unit": s.unit
                        }
                        for s in sensors
                    ]
                },
                "equipments": {
                    "count": len(equipments),
                    "by_type": self._count_by_type(equipments, "type"),
                    "by_state": self._count_by_type(equipments, "state"),
                    "details": [
                        {
                            "id": e.id,
                            "type": e.type,
                            "state": e.state
                        }
                        for e in equipments
                    ]
                }
            })

    def _count_by_type(self, items, attr):
        """Compter les items par attribut"""
        counts = {}
        for item in items:
            key = getattr(item, attr)
            counts[key] = counts.get(key, 0) + 1
        return counts
