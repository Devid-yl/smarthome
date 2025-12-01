"""
REST API for house and room management.
"""

import json
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..models import House, Room, EventHistory
from ..database import async_session_maker
from ..utils.permissions import can_manage_house
from .base import BaseAPIHandler


class HousesAPIHandler(BaseAPIHandler):
    """
    GET /api/houses - List all user's houses
    POST /api/houses - Create a new house
    """

    async def get(self):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        # DATABASE QUERY: Récupérer les maisons possédées et partagées de l'utilisateur
        async with async_session_maker() as session:
            from sqlalchemy import and_
            from ..models import HouseMember

            # Retrieve houses owned by the user
            owned_result = await session.execute(
                select(House)
                .where(House.user_id == current_user["id"])
                .options(selectinload(House.rooms))
            )
            owned_houses = owned_result.scalars().all()

            # Retrieve houses where user is an accepted member
            member_result = await session.execute(
                select(HouseMember)
                .where(
                    and_(
                        HouseMember.user_id == current_user["id"],
                        HouseMember.status == "accepted",
                    )
                )
                .options(selectinload(HouseMember.house))
            )
            memberships = member_result.scalars().all()

            houses_list = []

            # Add owned houses
            for h in owned_houses:
                houses_list.append(
                    {
                        "id": h.id,
                        "name": h.name,
                        "address": h.address,
                        "length": h.length,
                        "width": h.width,
                        "grid": h.grid,
                        "role": "proprietaire",
                        "is_owner": True,
                        "rooms": [{"id": r.id, "name": r.name} for r in h.rooms],
                    }
                )

            # Add shared houses
            for membership in memberships:
                if membership.house:
                    # Load rooms
                    await session.refresh(membership.house, ["rooms"])
                    houses_list.append(
                        {
                            "id": membership.house.id,
                            "name": membership.house.name,
                            "address": membership.house.address,
                            "length": membership.house.length,
                            "width": membership.house.width,
                            "grid": membership.house.grid,
                            "role": membership.role,
                            "is_owner": False,
                            "rooms": [
                                {"id": r.id, "name": r.name}
                                for r in membership.house.rooms
                            ],
                        }
                    )

            self.write_json({"houses": houses_list})

    async def post(self):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            return self.write_error_json("Invalid JSON", 400)

        name = data.get("name", "").strip()
        address = data.get("address", "").strip()
        length = data.get("length")
        width = data.get("width")

        if not name:
            return self.write_error_json("House name is required", 400)

        # Validate dimensions
        try:
            length = int(length) if length else 10
            width = int(width) if width else 10
            if length < 1 or width < 1 or length > 50 or width > 50:
                raise ValueError
        except (ValueError, TypeError):
            return self.write_error_json(
                "Length and width must be between 1 and 50", 400
            )

        # DATABASE QUERY: Créer une nouvelle maison avec grille et enregistrer dans l'historique
        async with async_session_maker() as session:
            # Create a grid with automatic wall borders
            # Actual grid: (length+2) x (width+2) for borders
            grid = []
            for i in range(length + 2):
                row = []
                for j in range(width + 2):
                    # Border = wall (1), interior = empty (0)
                    is_border = i == 0 or i == length + 1 or j == 0 or j == width + 1
                    row.append(1 if is_border else 0)
                grid.append(row)

            new_house = House(
                user_id=current_user["id"],
                name=name,
                address=address or "",
                length=length,
                width=width,
                grid=grid,  # Grid with wall borders
            )

            session.add(new_house)
            await session.commit()
            await session.refresh(new_house)

            # Enregistrer dans l'historique
            event = EventHistory(
                house_id=new_house.id,
                user_id=current_user["id"],
                event_type="house_modified",
                entity_type="house",
                entity_id=new_house.id,
                description=f"Maison créée: {new_house.name}",
                event_metadata={
                    "action": "create",
                    "dimensions": f"{length}x{width}",
                    "address": address,
                },
                ip_address=self.request.remote_ip,
            )
            session.add(event)
            await session.commit()

            self.write_json(
                {
                    "id": new_house.id,
                    "name": new_house.name,
                    "address": new_house.address,
                    "length": new_house.length,
                    "width": new_house.width,
                    "grid": new_house.grid,
                    "message": "House created successfully",
                },
                201,
            )


class HouseDetailAPIHandler(BaseAPIHandler):
    """
    GET /api/houses/{id} - Détails d'une maison
    PUT /api/houses/{id} - Modifier une maison
    DELETE /api/houses/{id} - Supprimer une maison
    """

    async def get(self, house_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        # DATABASE QUERY: Récupérer les détails d'une maison avec vérification des permissions
        async with async_session_maker() as session:
            from ..utils.permissions import can_view_house, get_user_role_in_house

            house_id = int(house_id)

            # Vérifier les permissions de visualisation
            if not await can_view_house(session, current_user["id"], house_id):
                return self.write_error_json("Access denied", 403)

            result = await session.execute(
                select(House)
                .where(House.id == house_id)
                .options(selectinload(House.rooms))
            )
            house = result.scalar_one_or_none()

            if not house:
                return self.write_error_json("House not found", 404)

            # Obtenir le rôle de l'utilisateur
            user_role = await get_user_role_in_house(
                session, current_user["id"], house_id
            )

            self.write_json(
                {
                    "id": house.id,
                    "name": house.name,
                    "address": house.address,
                    "length": house.length,
                    "width": house.width,
                    "grid": house.grid,
                    "user_role": user_role,
                    "rooms": [
                        {"id": r.id, "name": r.name, "house_id": r.house_id}
                        for r in house.rooms
                    ],
                }
            )

    async def put(self, house_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            return self.write_error_json("Invalid JSON", 400)

        # DATABASE QUERY: Mettre à jour les informations d'une maison avec vérification des permissions
        async with async_session_maker() as session:
            from ..utils.permissions import can_manage_house

            house_id = int(house_id)

            # Vérifier les permissions de gestion
            if not await can_manage_house(session, current_user["id"], house_id):
                return self.write_error_json("Access denied", 403)

            result = await session.execute(select(House).where(House.id == house_id))
            house = result.scalar_one_or_none()

            if not house:
                return self.write_error_json("House not found", 404)

            # Suivre les changements
            changes = {}

            # Mettre à jour les champs
            if "name" in data:
                changes["name"] = {"old": house.name, "new": data["name"].strip()}
                house.name = data["name"].strip()
            if "address" in data:
                changes["address"] = {
                    "old": house.address,
                    "new": data["address"].strip(),
                }
                house.address = data["address"].strip()
            if "length" in data:
                try:
                    length = int(data["length"])
                    if 1 <= length <= 50:
                        changes["length"] = {"old": house.length, "new": length}
                        house.length = length
                except (ValueError, TypeError):
                    pass
            if "width" in data:
                try:
                    width = int(data["width"])
                    if 1 <= width <= 50:
                        changes["width"] = {"old": house.width, "new": width}
                        house.width = width
                except (ValueError, TypeError):
                    pass
            if "grid" in data:
                house.grid = data["grid"]

            await session.commit()
            await session.refresh(house)

            self.write_json(
                {
                    "id": house.id,
                    "name": house.name,
                    "address": house.address,
                    "length": house.length,
                    "width": house.width,
                    "grid": house.grid,
                    "message": "House updated successfully",
                }
            )

    async def delete(self, house_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        # DATABASE QUERY: Supprimer une maison et toutes ses dépendances (cascade)
        async with async_session_maker() as session:
            try:
                result = await session.execute(
                    select(House).where(
                        House.id == int(house_id), House.user_id == current_user["id"]
                    )
                )
                house = result.scalar_one_or_none()

                if not house:
                    return self.write_error_json("House not found", 404)

                # Les cascades supprimeront automatiquement:
                # - automation_rules (ON DELETE CASCADE)
                # - rooms et leurs sensors/equipments (cascade SQLAlchemy)
                await session.delete(house)
                await session.commit()

                self.write_json({"message": "House deleted successfully"})
            except Exception as e:
                await session.rollback()
                print(f"Error deleting house: {e}")
                return self.write_error_json(f"Cannot delete house: {str(e)}", 500)


class RoomsAPIHandler(BaseAPIHandler):
    """
    GET /api/houses/{house_id}/rooms - Liste les pièces d'une maison
    POST /api/houses/{house_id}/rooms - Créer une pièce
    """

    async def get(self, house_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        # DATABASE QUERY: Récupérer toutes les pièces d'une maison spécifique
        async with async_session_maker() as session:
            # Check that l'utilisateur peut gérer la maison
            if not await can_manage_house(session, current_user["id"], int(house_id)):
                return self.write_error_json("House not found", 404)

            result = await session.execute(
                select(House).where(House.id == int(house_id))
            )
            house = result.scalar_one_or_none()

            if not house:
                return self.write_error_json("House not found", 404)

            # Retrieve les pièces
            result = await session.execute(
                select(Room).where(Room.house_id == int(house_id))
            )
            rooms = result.scalars().all()

            self.write_json(
                {
                    "rooms": [
                        {"id": r.id, "name": r.name, "house_id": r.house_id}
                        for r in rooms
                    ]
                }
            )

    async def post(self, house_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            return self.write_error_json("Invalid JSON", 400)

        name = data.get("name", "").strip()
        if not name:
            return self.write_error_json("Room name is required", 400)

        # DATABASE QUERY: Créer une nouvelle pièce et enregistrer dans l'historique
        async with async_session_maker() as session:
            # Check that l'utilisateur peut gérer la maison
            if not await can_manage_house(session, current_user["id"], int(house_id)):
                return self.write_error_json("House not found", 404)

            result = await session.execute(
                select(House).where(House.id == int(house_id))
            )
            house = result.scalar_one_or_none()

            if not house:
                return self.write_error_json("House not found", 404)

            # Create la pièce
            new_room = Room(house_id=int(house_id), name=name)

            session.add(new_room)
            await session.commit()
            await session.refresh(new_room)

            # Enregistrer dans l'historique
            event = EventHistory(
                house_id=house.id,
                user_id=current_user["id"],
                event_type="house_modified",
                entity_type="room",
                entity_id=new_room.id,
                description=f"Pièce ajoutée: {new_room.name}",
                event_metadata={"action": "create", "room_name": new_room.name},
                ip_address=self.request.remote_ip,
            )
            session.add(event)
            await session.commit()

            self.write_json(
                {
                    "id": new_room.id,
                    "name": new_room.name,
                    "house_id": new_room.house_id,
                    "message": "Room created successfully",
                },
                201,
            )


class RoomDetailAPIHandler(BaseAPIHandler):
    """
    GET /api/rooms/{id} - Détails d'une pièce
    PUT /api/rooms/{id} - Modifier une pièce
    DELETE /api/rooms/{id} - Supprimer une pièce
    """

    async def get(self, room_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        # DATABASE QUERY: Récupérer les détails d'une pièce spécifique
        async with async_session_maker() as session:
            result = await session.execute(
                select(Room).join(House).where(Room.id == int(room_id))
            )
            room = result.scalar_one_or_none()

            if not room:
                return self.write_error_json("Room not found", 404)

            if not await can_manage_house(session, current_user["id"], room.house_id):
                return self.write_error_json("Room not found", 404)

            self.write_json(
                {"id": room.id, "name": room.name, "house_id": room.house_id}
            )

    async def put(self, room_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            return self.write_error_json("Invalid JSON", 400)

        # DATABASE QUERY: Mettre à jour le nom d'une pièce et enregistrer dans l'historique
        async with async_session_maker() as session:
            result = await session.execute(
                select(Room).join(House).where(Room.id == int(room_id))
            )
            room = result.scalar_one_or_none()

            if not room:
                return self.write_error_json("Room not found", 404)

            if not await can_manage_house(session, current_user["id"], room.house_id):
                return self.write_error_json("Room not found", 404)

            # Suivre les changements
            changes = {}
            if "name" in data:
                changes["name"] = {"old": room.name, "new": data["name"].strip()}
                room.name = data["name"].strip()

            # Enregistrer dans l'historique si changements
            if changes:
                event = EventHistory(
                    house_id=room.house_id,
                    user_id=current_user["id"],
                    event_type="house_modified",
                    entity_type="room",
                    entity_id=room.id,
                    description=(
                        f"Pièce renommée: {changes['name']['old']} → "
                        f"{changes['name']['new']}"
                    ),
                    event_metadata={"action": "update", "changes": changes},
                    ip_address=self.request.remote_ip,
                )
                session.add(event)

            await session.commit()
            await session.refresh(room)

            self.write_json(
                {
                    "id": room.id,
                    "name": room.name,
                    "house_id": room.house_id,
                    "message": "Room updated successfully",
                }
            )

    async def delete(self, room_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        # DATABASE QUERY: Supprimer une pièce et enregistrer dans l'historique
        async with async_session_maker() as session:
            result = await session.execute(
                select(Room).join(House).where(Room.id == int(room_id))
            )
            room = result.scalar_one_or_none()

            if not room:
                return self.write_error_json("Room not found", 404)

            if not await can_manage_house(session, current_user["id"], room.house_id):
                return self.write_error_json("Room not found", 404)

            # Enregistrer dans l'historique avant retrait
            event = EventHistory(
                house_id=room.house_id,
                user_id=current_user["id"],
                event_type="house_modified",
                entity_type="room",
                entity_id=room.id,
                description=f"Pièce retirée: {room.name}",
                event_metadata={"action": "delete", "room_name": room.name},
                ip_address=self.request.remote_ip,
            )
            session.add(event)

            await session.delete(room)
            await session.commit()

            self.write_json({"message": "Room deleted successfully"})
