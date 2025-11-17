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

        if not name:
            self.render("add_house.html", error="Le nom est requis")
            return

        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            new_house = House(
                user_id=user_id,
                name=name,
                address=address or None
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
            self.render("edit_house.html", house=house, error=None)

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
                self.render("edit_house.html", house=house,
                            error="Le nom est requis")
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
            await session.commit()
            self.redirect("/houses")


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
