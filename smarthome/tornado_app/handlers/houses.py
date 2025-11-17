import tornado.web
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from ..models import House, Room
from ..database import async_session_maker


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_id = self.get_secure_cookie("uid")
        if not user_id:
            return None
        username = self.get_secure_cookie("uname")
        return {
            "id": int(user_id.decode()),
            "username": username.decode() if username else None
        }


class HouseListHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            result = await session.execute(
                select(House)
                .where(House.user_id == user_id)
                .options(selectinload(House.rooms))
            )
            houses = result.scalars().all()
            self.render("house_list.html", houses=houses)


class AddHouseHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("add_house.html", error=None)

    @tornado.web.authenticated
    async def post(self):
        name = self.get_argument("name", "")
        address = self.get_argument("address", "")
        length = int(self.get_argument("length", ""))
        width = int(self.get_argument("width", ""))

        if not name or not length or not width:
            self.render("add_house.html", error="Tous les champs requis doivent être remplis")
            return

        grid = [[0 for _ in range(width)] for _ in range(length)]

        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            new_house = House(
                user_id=user_id,
                name=name,
                address=address or None,
                length=length,
                width=width,
                grid=grid
            )
            session.add(new_house)
            await session.commit()
            self.redirect("/houses")


class AddRoomHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        house_id = self.get_argument("house_id", None)
        if not house_id:
            self.redirect("/houses")
            return
        self.render("add_room.html", house_id=house_id, error=None)

    @tornado.web.authenticated
    async def post(self):
        house_id = self.get_argument("house_id", "")
        name = self.get_argument("name", "")

        if not name or not house_id:
            self.render("add_room.html", house_id=house_id,
                        error="Tous les champs sont requis")
            return

        async with async_session_maker() as session:
            new_room = Room(
                house_id=int(house_id),
                name=name
            )
            session.add(new_room)
            await session.commit()
            self.redirect("/houses")


class EditHouseHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, house_id):
        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            result = await session.execute(
                select(House).where(
                    House.id == int(house_id),
                    House.user_id == user_id
                )
            )
            house = result.scalar_one_or_none()
            if not house:
                self.redirect("/houses")
                return
            
            # Vérifier s'il y a une grille temporaire
            temp_grid_cookie = self.get_secure_cookie(
                f"temp_grid_{house_id}"
            )
            has_temp_grid = temp_grid_cookie is not None
            
            self.render("edit_house.html", house=house,
                        error=None, has_temp_grid=has_temp_grid)

    @tornado.web.authenticated
    async def post(self, house_id):
        user_id = self.current_user["id"]
        name = self.get_argument("name", "")
        address = self.get_argument("address", "")

        if not name:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(House).where(House.id == int(house_id))
                )
                house = result.scalar_one_or_none()
                temp_grid_cookie = self.get_secure_cookie(
                    f"temp_grid_{house_id}"
                )
                has_temp_grid = temp_grid_cookie is not None
                self.render("edit_house.html", house=house,
                            error="Le nom est requis",
                            has_temp_grid=has_temp_grid)
                return

        async with async_session_maker() as session:
            result = await session.execute(
                select(House).where(
                    House.id == int(house_id),
                    House.user_id == user_id
                )
            )
            house = result.scalar_one_or_none()
            if not house:
                self.redirect("/houses")
                return

            house.name = name
            house.address = address or None
            
            # Appliquer la grille temporaire si elle existe
            temp_grid_cookie = self.get_secure_cookie(
                f"temp_grid_{house_id}"
            )
            if temp_grid_cookie:
                import json
                try:
                    temp_grid = json.loads(temp_grid_cookie.decode())
                    house.grid = temp_grid
                    # Supprimer le cookie temporaire
                    self.clear_cookie(f"temp_grid_{house_id}")
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            await session.commit()
            self.redirect("/houses")


class CancelEditHouseInsideHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, house_id):
        # Supprimer la grille temporaire
        self.clear_cookie(f"temp_grid_{house_id}")
        self.redirect(f"/houses/edit/{house_id}")


class DeleteHouseHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self, house_id):
        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            result = await session.execute(
                select(House).where(
                    House.id == int(house_id),
                    House.user_id == user_id
                )
            )
            house = result.scalar_one_or_none()
            if house:
                await session.delete(house)
                await session.commit()
            self.redirect("/houses")


class EditRoomHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, room_id):
        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            result = await session.execute(
                select(Room)
                .join(House)
                .where(
                    Room.id == int(room_id),
                    House.user_id == user_id
                )
            )
            room = result.scalar_one_or_none()
            if not room:
                self.redirect("/houses")
                return
            self.render("edit_room.html", room=room, error=None)

    @tornado.web.authenticated
    async def post(self, room_id):
        user_id = self.current_user["id"]
        name = self.get_argument("name", "")

        if not name:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Room).where(Room.id == int(room_id))
                )
                room = result.scalar_one_or_none()
                self.render("edit_room.html", room=room,
                            error="Le nom est requis")
                return

        async with async_session_maker() as session:
            result = await session.execute(
                select(Room)
                .join(House)
                .where(
                    Room.id == int(room_id),
                    House.user_id == user_id
                )
            )
            room = result.scalar_one_or_none()
            if not room:
                self.redirect("/houses")
                return

            room.name = name
            await session.commit()
            self.redirect("/houses")


class DeleteRoomHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self, room_id):
        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            result = await session.execute(
                select(Room)
                .join(House)
                .where(
                    Room.id == int(room_id),
                    House.user_id == user_id
                )
            )
            room = result.scalar_one_or_none()
            if room:
                await session.delete(room)
                await session.commit()
            self.redirect("/houses")


class EditHouseInsideHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self, house_id):
        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            result = await session.execute(
                select(House)
                .where(
                    House.id == int(house_id),
                    House.user_id == user_id
                )
                .options(selectinload(House.rooms))
            )
            house = result.scalar_one_or_none()
            if not house:
                self.redirect("/houses")
                return
            self.render("edit_house_inside.html", house=house, error=None)

    @tornado.web.authenticated
    async def post(self, house_id):
        user_id = self.current_user["id"]
        
        # Récupérer la grille envoyée depuis le formulaire (format JSON)
        import json
        grid_json = self.get_argument("grid", "[]")
        
        try:
            grid = json.loads(grid_json)
        except json.JSONDecodeError:
            self.redirect(f"/houses/edit_inside/{house_id}")
            return

        # Validation côté serveur : vérifier la connectivité
        if not self._validate_grid_connectivity(grid):
            async with async_session_maker() as session:
                result = await session.execute(
                    select(House)
                    .where(
                        House.id == int(house_id),
                        House.user_id == user_id
                    )
                    .options(selectinload(House.rooms))
                )
                house = result.scalar_one_or_none()
                if house:
                    error = ("Erreur : certaines pièces ont des "
                             "cases non adjacentes")
                    self.render("edit_house_inside.html",
                                house=house, error=error)
                    return

        # Stocker temporairement la grille dans un cookie sécurisé
        # (pas encore en BDD)
        self.set_secure_cookie(
            f"temp_grid_{house_id}",
            grid_json,
            expires_days=1
        )
        
        # Rediriger vers la page d'édition pour validation finale
        self.redirect(f"/houses/edit/{house_id}")
    
    def _validate_grid_connectivity(self, grid):
        """Valider connectivité des pièces (pas de trous)"""
        if not grid or len(grid) == 0:
            return True

        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        checked_rooms = set()

        for i in range(rows):
            for j in range(cols):
                value = grid[i][j]
                is_room = value >= 2000 and value < 3000
                if is_room and value not in checked_rooms:
                    checked_rooms.add(value)

                    # Trouver toutes les cases de cette pièce
                    room_cells = []
                    for row in range(rows):
                        for col in range(cols):
                            if grid[row][col] == value:
                                room_cells.append((row, col))

                    # Vérifier la connectivité avec BFS
                    connected = self._are_cells_connected(
                        room_cells, rows, cols
                    )
                    if not connected:
                        return False

        return True

    def _are_cells_connected(self, cells, max_rows, max_cols):
        """Algorithme BFS pour vérifier connectivité"""
        if len(cells) <= 1:
            return True

        visited = set()
        queue = [cells[0]]
        visited.add(cells[0])

        while queue:
            current = queue.pop(0)
            row, col = current

            # Vérifier les 4 voisins
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (row + dr, col + dc)
                in_bounds = (0 <= neighbor[0] < max_rows and
                             0 <= neighbor[1] < max_cols)
                if (neighbor not in visited and
                        neighbor in cells and in_bounds):
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == len(cells)
