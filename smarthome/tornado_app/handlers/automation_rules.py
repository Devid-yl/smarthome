"""
API handlers for automation rules.
"""

import json
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..models import AutomationRule, Sensor, Equipment
from ..database import async_session_maker
from .base import BaseAPIHandler


class AutomationRulesListHandler(BaseAPIHandler):
    """
    GET /api/automation/rules?house_id=X - List rules
    POST /api/automation/rules - Create a rule
    """

    async def get(self):
        """List all rules for a house."""
        house_id = self.get_argument("house_id", None)

        if not house_id:
            self.write_error_json("house_id requis", 400)
            return

        # DATABASE QUERY: Opération sur la base de données
        async with async_session_maker() as session:
            result = await session.execute(
                select(AutomationRule)
                .options(
                    selectinload(AutomationRule.sensor),
                    selectinload(AutomationRule.equipment),
                )
                .where(AutomationRule.house_id == int(house_id))
            )
            rules = result.scalars().all()

            self.write_json(
                {
                    "rules": [
                        {
                            "id": r.id,
                            "name": r.name,
                            "description": r.description,
                            "is_active": r.is_active,
                            "sensor": (
                                {
                                    "id": r.sensor.id,
                                    "name": r.sensor.name,
                                    "type": r.sensor.type,
                                }
                                if r.sensor
                                else None
                            ),
                            "condition_operator": r.condition_operator,
                            "condition_value": r.condition_value,
                            "equipment": (
                                {
                                    "id": r.equipment.id,
                                    "name": r.equipment.name,
                                    "type": r.equipment.type,
                                }
                                if r.equipment
                                else None
                            ),
                            "action_state": r.action_state,
                            "created_at": r.created_at,
                            "last_triggered": r.last_triggered,
                        }
                        for r in rules
                    ]
                }
            )

    async def post(self):
        """Create a new automation rule."""
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.write_error_json("Invalid JSON", 400)
            return

        required = [
            "house_id",
            "name",
            "sensor_id",
            "condition_operator",
            "condition_value",
            "equipment_id",
            "action_state",
        ]

        for field in required:
            if field not in data:
                self.write_error_json(f"Champ requis: {field}", 400)
                return

        # DATABASE QUERY: Opération sur la base de données
        async with async_session_maker() as session:
            try:
                # Convertir les IDs en entiers
                house_id = int(data["house_id"])
                sensor_id = int(data["sensor_id"])
                equipment_id = int(data["equipment_id"])

                # Check that le capteur et l'équipement existent
                sensor = await session.get(Sensor, sensor_id)
                equipment = await session.get(Equipment, equipment_id)

                if not sensor:
                    self.write_error_json("Capteur introuvable", 404)
                    return

                if not equipment:
                    self.write_error_json("Équipement introuvable", 404)
                    return

                rule = AutomationRule(
                    house_id=house_id,
                    name=data["name"],
                    description=data.get("description"),
                    sensor_id=sensor_id,
                    condition_operator=data["condition_operator"],
                    condition_value=float(data["condition_value"]),
                    equipment_id=equipment_id,
                    action_state=data["action_state"],
                    is_active=data.get("is_active", True),
                )

                session.add(rule)
                await session.commit()
                await session.refresh(rule)

                self.write_json(
                    {
                        "message": "Rule created",
                        "rule": {"id": rule.id, "name": rule.name},
                    },
                    201,
                )
            except Exception as e:
                await session.rollback()
                print(f"Error creating automation rule: {e}")
                self.write_error_json(str(e), 500)


class AutomationRuleDetailHandler(BaseAPIHandler):
    """
    GET /api/automation/rules/{id} - Détails d'une règle
    PUT /api/automation/rules/{id} - Modifier une règle
    DELETE /api/automation/rules/{id} - Supprimer une règle
    """

    async def get(self, rule_id):
        """Récupérer les détails d'une règle"""
        # DATABASE QUERY: Opération sur la base de données
        async with async_session_maker() as session:
            result = await session.execute(
                select(AutomationRule)
                .options(
                    selectinload(AutomationRule.sensor),
                    selectinload(AutomationRule.equipment),
                )
                .where(AutomationRule.id == int(rule_id))
            )
            rule = result.scalar_one_or_none()

            if not rule:
                self.write_error_json("Règle introuvable", 404)
                return

            self.write_json(
                {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "is_active": rule.is_active,
                    "sensor": {
                        "id": rule.sensor.id,
                        "name": rule.sensor.name,
                        "type": rule.sensor.type,
                    },
                    "condition_operator": rule.condition_operator,
                    "condition_value": rule.condition_value,
                    "equipment": {
                        "id": rule.equipment.id,
                        "name": rule.equipment.name,
                        "type": rule.equipment.type,
                    },
                    "action_state": rule.action_state,
                    "created_at": rule.created_at,
                    "last_triggered": rule.last_triggered,
                }
            )

    async def put(self, rule_id):
        """Modifier une règle"""
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.write_error_json("Invalid JSON", 400)
            return

        # DATABASE QUERY: Opération sur la base de données
        async with async_session_maker() as session:
            rule = await session.get(AutomationRule, int(rule_id))

            if not rule:
                self.write_error_json("Règle introuvable", 404)
                return

            # Mise à jour des champs
            if "name" in data:
                rule.name = data["name"]
            if "description" in data:
                rule.description = data["description"]
            if "is_active" in data:
                rule.is_active = data["is_active"]
            if "sensor_id" in data:
                # Check that le capteur existe
                sensor = await session.get(Sensor, int(data["sensor_id"]))
                if sensor:
                    rule.sensor_id = int(data["sensor_id"])
            if "condition_operator" in data:
                rule.condition_operator = data["condition_operator"]
            if "condition_value" in data:
                rule.condition_value = float(data["condition_value"])
            if "equipment_id" in data:
                # Check that l'équipement existe
                equipment = await session.get(Equipment, int(data["equipment_id"]))
                if equipment:
                    rule.equipment_id = int(data["equipment_id"])
            if "action_state" in data:
                rule.action_state = data["action_state"]

            await session.commit()

            self.write_json({"message": "Rule updated"})

    async def delete(self, rule_id):
        """Supprimer une règle"""
        # DATABASE QUERY: Opération sur la base de données
        async with async_session_maker() as session:
            rule = await session.get(AutomationRule, int(rule_id))

            if not rule:
                self.write_error_json("Règle introuvable", 404)
                return

            await session.delete(rule)
            await session.commit()

            self.write_json({"message": "Rule deleted"})
