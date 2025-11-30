"""User position handlers for movement simulation."""
import json
from datetime import datetime
from sqlalchemy import select, and_

from ..database import async_session_maker
from ..models import UserPosition, House, User, Sensor, AutomationRule
from ..utils.permissions import get_user_house_permission, PermissionLevel
from .websocket import RealtimeHandler
from .base import BaseAPIHandler


class UserPositionHandler(BaseAPIHandler):
    """Handler for user position operations."""

    async def get(self, house_id: int):
        """Get all user positions in a house."""
        user_id_cookie = self.get_secure_cookie("uid")
        if not user_id_cookie:
            self.write_error_json("Not authenticated", 401)
            return
        user_id = int(user_id_cookie.decode())
        house_id = int(house_id)

        async with async_session_maker() as session:
            # Verify user is member of house
            perm = await get_user_house_permission(
                session, user_id, house_id
            )
            if perm == PermissionLevel.NONE:
                self.write_error_json("Access denied", 403)
                return

            # Get all active positions for this house
            query = (
                select(UserPosition, User)
                .join(User, UserPosition.user_id == User.id)
                .where(and_(
                    UserPosition.house_id == house_id,
                    UserPosition.is_active == True  # noqa: E712
                ))
            )
            result = await session.execute(query)
            rows = result.all()

            positions = [
                {
                    "user_id": position.user_id,
                    "username": user.username,
                    "profile_image": user.profile_image,
                    "x": position.x,
                    "y": position.y,
                    "last_update": position.last_update.isoformat()
                }
                for position, user in rows
            ]

            self.write({"positions": positions})

    async def post(self, house_id: int):
        """Update user position in a house. Body: {"x": int, "y": int}"""
        user_id_cookie = self.get_secure_cookie("uid")
        if not user_id_cookie:
            self.write_error_json("Not authenticated", 401)
            return
        user_id = int(user_id_cookie.decode())
        house_id = int(house_id)

        async with async_session_maker() as session:
            # Verify user is member of house
            perm = await get_user_house_permission(
                session, user_id, house_id
            )
            if perm == PermissionLevel.NONE:
                self.write_error_json("Access denied", 403)
                return

            # Parse request body
            try:
                data = json.loads(self.request.body)
                x = int(data["x"])
                y = int(data["y"])
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.write_error_json(f"Invalid data: {e}")
                return

            # Get house dimensions for validation
            house = await session.get(House, house_id)
            if not house:
                self.write_error_json("House not found", 404)
                return

            # Validate position within grid bounds
            # (use actual grid size, not house.width/length)
            if house.grid:
                grid_height = len(house.grid)
                grid_width = len(house.grid[0]) if grid_height > 0 else 0
            else:
                grid_height = house.length  # type: ignore
                grid_width = house.width  # type: ignore

            if not (0 <= x < grid_width and 0 <= y < grid_height):
                self.write_error_json(
                    f"Position out of bounds (0-{grid_width-1}, "
                    f"0-{grid_height-1})"
                )
                return

            # Check if position exists for this user/house
            query = select(UserPosition).where(and_(
                UserPosition.house_id == house_id,
                UserPosition.user_id == user_id
            ))
            result = await session.execute(query)
            position = result.scalar_one_or_none()

            if position:
                # Update existing position
                position.x = x  # type: ignore
                position.y = y  # type: ignore
                position.is_active = True  # type: ignore
                position.last_update = datetime.utcnow()  # type: ignore
            else:
                # Create new position
                position = UserPosition(
                    house_id=house_id,
                    user_id=user_id,
                    x=x,
                    y=y,
                    is_active=True
                )
                session.add(position)

            await session.commit()

            # Get user info for broadcast
            user = await session.get(User, user_id)
            if not user:
                self.write_error_json("User not found", 404)
                return

            # DÉTECTION AUTOMATIQUE DE PRÉSENCE
            # Trouver la pièce où se trouve l'utilisateur
            await self._update_presence_sensors(
                session, house, x, y, house_id
            )
            await session.commit()

            # Broadcast position update via WebSocket
            message = {
                "type": "user_position_changed",
                "house_id": house_id,
                "user_id": user_id,
                "username": user.username,
                "profile_image": user.profile_image,
                "x": x,
                "y": y,
                "timestamp": datetime.utcnow().isoformat()
            }
            for client in RealtimeHandler.clients:
                try:
                    client.write_message(json.dumps(message))
                except Exception as e:
                    print(f"Error broadcasting position: {e}")

            # user is guaranteed to exist here due to check above
            self.write({
                "success": True,
                "position": {
                    "x": x,
                    "y": y,
                    "user_id": user_id,
                    "username": user.username,
                    "profile_image": user.profile_image
                }
            })

    async def delete(self, house_id: int):
        """Deactivate user position (user leaves house)."""
        user_id_cookie = self.get_secure_cookie("uid")
        if not user_id_cookie:
            self.write_error_json("Not authenticated", 401)
            return
        user_id = int(user_id_cookie.decode())
        house_id = int(house_id)

        async with async_session_maker() as session:
            # Verify user is member of house
            perm = await get_user_house_permission(
                session, user_id, house_id
            )
            if perm == PermissionLevel.NONE:
                self.write_error_json("Access denied", 403)
                return

            # Find and deactivate position
            query = select(UserPosition).where(and_(
                UserPosition.house_id == house_id,
                UserPosition.user_id == user_id
            ))
            result = await session.execute(query)
            position = result.scalar_one_or_none()

            if position:
                position.is_active = False  # type: ignore
                await session.commit()

                # Broadcast deactivation
                message = {
                    "type": "user_position_deactivated",
                    "house_id": house_id,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                for client in RealtimeHandler.clients:
                    try:
                        client.write_message(json.dumps(message))
                    except Exception as e:
                        print(f"Error broadcasting deactivation: {e}")

            # Mettre à jour les capteurs de présence après départ
            await self._update_presence_sensors_on_leave(
                session, house_id, user_id
            )
            await session.commit()

            self.write({"success": True})

    async def _update_presence_sensors(self, session, house, x, y, house_id):
        """
        Met à jour automatiquement les capteurs de présence
        en fonction de la position de l'utilisateur.
        Détecte la présence sur les CASES où sont placés les capteurs.
        """
        # Retrieve toutes les positions actives dans cette maison
        query = select(UserPosition).where(and_(
            UserPosition.house_id == house_id,
            UserPosition.is_active == True  # noqa: E712
        ))
        result = await session.execute(query)
        all_positions = result.scalars().all()

        # Grouper les positions par cellule
        users_per_cell = {}
        for pos in all_positions:
            cell_key = (pos.x, pos.y)
            if cell_key not in users_per_cell:
                users_per_cell[cell_key] = 0
            users_per_cell[cell_key] += 1
        
        # Retrieve tous les capteurs de présence
        query = select(Sensor).where(and_(
            Sensor.house_id == house_id,
            Sensor.type == "presence"
        ))
        result = await session.execute(query)
        presence_sensors = result.scalars().all()
        
        # Pour chaque capteur, compter les utilisateurs sur ses cases
        if house.grid:
            for sensor in presence_sensors:
                # Trouver toutes les cases où ce capteur est placé
                sensor_cells = []
                for row_idx, row in enumerate(house.grid):
                    for col_idx, cell in enumerate(row):
                        # Check if le capteur est dans cette cellule
                        if isinstance(cell, dict):
                            cell_sensors = cell.get("sensors", [])
                            if sensor.id in cell_sensors:
                                sensor_cells.append((col_idx, row_idx))
                
                # Compter les utilisateurs sur ces cases
                user_count = 0
                for cell_pos in sensor_cells:
                    user_count += users_per_cell.get(cell_pos, 0)
                
                # Mettre à jour la valeur du capteur
                new_value = 1.0 if user_count > 0 else 0.0
                
                # Mettre à jour uniquement si changement
                if sensor.value != new_value:
                    old_value = sensor.value
                    sensor.value = new_value
                    sensor.last_update = datetime.utcnow()
                    
                    print(
                        f"[Presence] Sensor {sensor.id} ({sensor.name}) "
                        f"on {len(sensor_cells)} cell(s): "
                        f"{old_value} → {new_value} "
                        f"({user_count} user(s) detected)"
                    )
                    
                    # Broadcaster la mise à jour du capteur via WebSocket
                    RealtimeHandler.broadcast_sensor_update(
                        sensor.id,
                        sensor.value,
                        sensor.is_active,
                        sensor.house_id
                    )
                    
                    # Déclencher les règles d'automatisation pour ce capteur
                    await self._trigger_automation_for_sensor(
                        session, sensor
                    )

    async def _update_presence_sensors_on_leave(
        self, session, house_id, leaving_user_id
    ):
        """
        Met à jour les capteurs de présence après qu'un utilisateur
        quitte la simulation.
        """
        # Retrieve la maison
        house = await session.get(House, house_id)
        if not house:
            return
        
        # Retrieve toutes les positions actives restantes
        query = select(UserPosition).where(and_(
            UserPosition.house_id == house_id,
            UserPosition.is_active == True,  # noqa: E712
            UserPosition.user_id != leaving_user_id
        ))
        result = await session.execute(query)
        remaining_positions = result.scalars().all()
        
        # Grouper par cellule
        users_per_cell = {}
        for pos in remaining_positions:
            cell_key = (pos.x, pos.y)
            if cell_key not in users_per_cell:
                users_per_cell[cell_key] = 0
            users_per_cell[cell_key] += 1
        
        # Retrieve tous les capteurs de présence
        query = select(Sensor).where(and_(
            Sensor.house_id == house_id,
            Sensor.type == "presence"
        ))
        result = await session.execute(query)
        presence_sensors = result.scalars().all()
        
        # Pour chaque capteur, compter les utilisateurs sur ses cases
        if house.grid:
            for sensor in presence_sensors:
                # Trouver toutes les cases où ce capteur est placé
                sensor_cells = []
                for row_idx, row in enumerate(house.grid):
                    for col_idx, cell in enumerate(row):
                        if isinstance(cell, dict):
                            cell_sensors = cell.get("sensors", [])
                            if sensor.id in cell_sensors:
                                sensor_cells.append((col_idx, row_idx))
                
                # Compter les utilisateurs sur ces cases
                user_count = 0
                for cell_pos in sensor_cells:
                    user_count += users_per_cell.get(cell_pos, 0)
                
                # Mettre à jour la valeur
                new_value = 1.0 if user_count > 0 else 0.0
                
                if sensor.value != new_value:
                    sensor.value = new_value
                    sensor.last_update = datetime.utcnow()
                    
                    print(
                        f"[Presence] Sensor {sensor.id} updated "
                        f"after user left: {new_value}"
                    )
                    
                    # Broadcaster
                    RealtimeHandler.broadcast_sensor_update(
                        sensor.id,
                        sensor.value,
                        sensor.is_active,
                        sensor.house_id
                    )
                    
                    # Déclencher automatisations
                    await self._trigger_automation_for_sensor(
                        session, sensor
                    )

    async def _trigger_automation_for_sensor(self, session, sensor):
        """
        Déclenche les règles d'automatisation liées à un capteur spécifique.
        """
        from ..models import Equipment, EventHistory
        
        # Retrieve les règles actives pour ce capteur
        query = select(AutomationRule).where(and_(
            AutomationRule.sensor_id == sensor.id,
            AutomationRule.is_active == True  # noqa: E712
        ))
        result = await session.execute(query)
        rules = result.scalars().all()
        
        for rule in rules:
            # Évaluer la condition
            condition_met = False
            if sensor.value is not None:
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
            
            if condition_met:
                # Appliquer l'action
                equipment = await session.get(Equipment, rule.equipment_id)
                if equipment and equipment.is_active:
                    if equipment.state != rule.action_state:
                        old_state = equipment.state
                        equipment.state = rule.action_state
                        equipment.last_update = datetime.utcnow()
                        rule.last_triggered = datetime.utcnow()
                        
                        print(
                            f"[Automation] Rule '{rule.name}' triggered: "
                            f"{equipment.name} {old_state} → "
                            f"{rule.action_state}"
                        )
                        
                        # Enregistrer dans l'historique
                        event = EventHistory(
                            house_id=equipment.house_id,
                            user_id=None,
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
                        
                        # Broadcaster la mise à jour de l'équipement
                        RealtimeHandler.broadcast_equipment_update(
                            equipment.id,
                            equipment.type,
                            equipment.state,
                            equipment.is_active,
                            equipment.house_id
                        )
