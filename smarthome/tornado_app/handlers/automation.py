"""
Business Logic B2B: Communication Sensors → Equipments
Automation logic based on sensor data.
"""

from sqlalchemy import select
from ..models import Sensor, Equipment, EventHistory
from ..database import async_session_maker
from datetime import datetime
from .base import BaseAPIHandler


class AutomationRulesHandler(BaseAPIHandler):
    """
    POST /api/automation/trigger - Trigger automation
    Analyzes sensors and controls equipment according to database rules only.
    """

    async def post(self):
        """
        Apply automation rules from database:
        - Fetch all active rules
        - Evaluate sensor conditions
        - Execute equipment actions
        - Log to event history
        """
        actions_taken = []

        async with async_session_maker() as session:
            from ..models import AutomationRule

            # Fetch all active automation rules
            result = await session.execute(
                select(AutomationRule).where(AutomationRule.is_active == True)  # noqa
            )
            rules = result.scalars().all()

            for rule in rules:
                # Get the sensor for this rule
                sensor = await session.get(Sensor, rule.sensor_id)
                if not sensor or not sensor.is_active or sensor.value is None:
                    continue

                # Evaluate condition
                condition_met = False
                if rule.condition_operator == ">":
                    condition_met = sensor.value > rule.condition_value
                elif rule.condition_operator == "<":
                    condition_met = sensor.value < rule.condition_value
                elif rule.condition_operator == ">=":
                    condition_met = sensor.value >= rule.condition_value
                elif rule.condition_operator == "<=":
                    condition_met = sensor.value <= rule.condition_value
                elif rule.condition_operator == "==":
                    condition_met = sensor.value == rule.condition_value
                elif rule.condition_operator == "!=":
                    condition_met = sensor.value != rule.condition_value

                # Execute action if condition is met
                if condition_met:
                    equipment = await session.get(Equipment, rule.equipment_id)
                    if equipment and equipment.is_active:
                        if equipment.state != rule.action_state:
                            old_state = equipment.state
                            equipment.state = rule.action_state
                            equipment.last_update = datetime.utcnow()
                            rule.last_triggered = datetime.utcnow()

                            # Log to event history
                            event = EventHistory(
                                house_id=equipment.house_id,
                                user_id=None,  # Automatic action
                                event_type="automation_triggered",
                                entity_type="automation_rule",
                                entity_id=rule.id,
                                description=(
                                    f"Rule '{rule.name}' triggered: "
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
                                    "new_state": rule.action_state,
                                },
                            )
                            session.add(event)

                            actions_taken.append(
                                {
                                    "action": f"set_{rule.action_state}",
                                    "equipment_id": equipment.id,
                                    "equipment_name": equipment.name,
                                    "reason": (
                                        f"Rule: {rule.name} "
                                        f"({sensor.name} {sensor.value} "
                                        f"{rule.condition_operator} "
                                        f"{rule.condition_value})"
                                    ),
                                    "rule_id": rule.id,
                                    "rule_name": rule.name,
                                }
                            )

                            # Broadcast equipment update via WebSocket
                            from .websocket import RealtimeHandler

                            RealtimeHandler.broadcast_equipment_update(
                                equipment.id,
                                equipment.type,
                                equipment.state,
                                equipment.is_active,
                                equipment.house_id,
                            )

            # Commit all changes
            await session.commit()

        self.write_json(
            {
                "message": "Automation rules applied successfully",
                "actions_count": len(actions_taken),
                "actions": actions_taken,
            }
        )


class PresenceHandler(BaseAPIHandler):
    """GET /api/presence - État de tous les capteurs de présence"""

    async def get(self):
        """Récupérer l'état de tous les capteurs de présence"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Sensor).where(Sensor.type == "presence")
            )
            presence_sensors = result.scalars().all()

            self.write_json(
                {
                    "presence_sensors": [
                        {
                            "id": s.id,
                            "room_id": s.room_id,
                            "name": s.name,
                            "detected": bool(s.value) if s.value else False,
                            "last_update": (
                                s.last_update.isoformat() if s.last_update else None
                            ),
                        }
                        for s in presence_sensors
                    ]
                }
            )


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

            self.write_json(
                {
                    "sensors": {
                        "count": len(sensors),
                        "by_type": self._count_by_type(sensors, "type"),
                        "details": [
                            {
                                "id": s.id,
                                "type": s.type,
                                "value": s.value,
                                "unit": s.unit,
                            }
                            for s in sensors
                        ],
                    },
                    "equipments": {
                        "count": len(equipments),
                        "by_type": self._count_by_type(equipments, "type"),
                        "by_state": self._count_by_type(equipments, "state"),
                        "details": [
                            {"id": e.id, "type": e.type, "state": e.state}
                            for e in equipments
                        ],
                    },
                }
            )

    def _count_by_type(self, items, attr):
        """Compter les items par attribut"""
        counts = {}
        for item in items:
            key = getattr(item, attr)
            counts[key] = counts.get(key, 0) + 1
        return counts
