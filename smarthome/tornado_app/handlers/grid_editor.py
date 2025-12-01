import tornado.web
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..database import async_session_maker
from ..models import House


class EditHouseInsideHandler(tornado.web.RequestHandler):
    """Handler pour l'éditeur de grille d'intérieur"""

    def get_current_user(self):
        uid = self.get_secure_cookie("uid")
        return int(uid) if uid else None

    async def get(self, house_id):
        user_id = self.get_current_user()
        if not user_id:
            self.redirect("/app/login.html")
            return

        # DATABASE QUERY: Opération sur la base de données
        async with async_session_maker() as session:
            from ..utils.permissions import can_manage_house

            # Vérifier si l'utilisateur peut gérer la maison (propriétaire ou admin)
            if not await can_manage_house(session, user_id, int(house_id)):
                self.set_status(403)
                self.write(
                    "<h1>403 - Accès refusé</h1>"
                    "<p>Vous devez être propriétaire ou administrateur "
                    "pour modifier l'intérieur.</p>"
                )
                return

            result = await session.execute(
                select(House)
                .options(selectinload(House.rooms))
                .where(House.id == int(house_id))
            )
            house = result.scalar_one_or_none()

            if not house:
                self.set_status(404)
                self.write("<h1>404 - Maison introuvable</h1>")
                return

            self.render("edit_house_inside.html", house=house, error=None)

    async def post(self, house_id):
        user_id = self.get_current_user()
        if not user_id:
            self.redirect("/app/login.html")
            return

        grid_data = self.get_argument("grid", "[]")

        # DATABASE QUERY: Opération sur la base de données
        async with async_session_maker() as session:
            from ..utils.permissions import can_manage_house

            # Vérifier si l'utilisateur peut gérer la maison (propriétaire ou admin)
            if not await can_manage_house(session, user_id, int(house_id)):
                self.set_status(403)
                self.write(
                    "<h1>403 - Accès refusé</h1>"
                    "<p>Vous devez être propriétaire ou administrateur "
                    "pour modifier l'intérieur.</p>"
                )
                return

            result = await session.execute(
                select(House).where(House.id == int(house_id))
            )
            house = result.scalar_one_or_none()

            if not house:
                self.set_status(404)
                self.write("<h1>404 - Maison introuvable</h1>")
                return

            # Save grid to database
            import json

            try:
                grid = json.loads(grid_data)
                house.grid = grid
                await session.commit()
                
                # Broadcast grid update via WebSocket
                from .websocket import RealtimeHandler
                RealtimeHandler.broadcast_grid_update(int(house_id), grid)
            except json.JSONDecodeError:
                self.set_status(400)
                self.write("<h1>400 - Données de grille invalides</h1>")
                return

            # Redirect to house details page
            self.redirect(f"/app/house.html?id={house_id}")
