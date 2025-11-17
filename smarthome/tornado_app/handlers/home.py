import tornado.web
from sqlalchemy import select
from ..models import User
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


class HomeHandler(BaseHandler):
    async def get(self):
        user_data = None
        if self.current_user:
            user_id = self.current_user["id"]
            async with async_session_maker() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user_data = result.scalar_one_or_none()
        
        self.render("home.html", user=user_data)
