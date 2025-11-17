import tornado.web
from sqlalchemy import select
from datetime import datetime
from pathlib import Path
from ..models import User
from ..auth import hash_password
from ..database import async_session_maker
from ..config import get_settings


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


class ProfileHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                self.redirect("/login")
                return
            self.render("profile.html", user=user)


class EditProfileHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                self.redirect("/login")
                return
            self.render("edit_profile.html", user=user, error=None)

    @tornado.web.authenticated
    async def post(self):
        user_id = self.current_user["id"]
        username = self.get_argument("username", "")
        email = self.get_argument("email", "")
        phone_number = self.get_argument("phone_number", "")
        new_password = self.get_argument("new_password", "")
        confirm_password = self.get_argument("confirm_password", "")

        if not all([username, email]):
            async with async_session_maker() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                self.render("edit_profile.html", user=user,
                            error="Nom d'utilisateur et email requis")
                return

        if new_password and new_password != confirm_password:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                self.render("edit_profile.html", user=user,
                            error="Mots de passe différents")
                return

        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                self.redirect("/login")
                return

            # Check if username already exists (except current user)
            result = await session.execute(
                select(User).where(
                    User.username == username,
                    User.id != user_id
                )
            )
            if result.scalar_one_or_none():
                self.render("edit_profile.html", user=user,
                            error="Nom d'utilisateur déjà pris")
                return

            # Update user info
            user.username = username
            user.email = email
            user.phone_number = phone_number or None

            # Update password if provided
            if new_password:
                user.password = hash_password(new_password)

            # Handle profile image upload
            if "profile_image" in self.request.files:
                fileinfo = self.request.files["profile_image"][0]
                if fileinfo["filename"]:
                    ext = Path(fileinfo["filename"]).suffix
                    filename = f"{username}_{datetime.now().timestamp()}{ext}"

                    settings = get_settings()
                    media_path = Path(settings["media_path"])
                    profile_dir = media_path / "profile_images"
                    profile_dir.mkdir(exist_ok=True)

                    filepath = profile_dir / filename
                    with open(filepath, "wb") as f:
                        f.write(fileinfo["body"])

                    user.profile_image = f"profile_images/{filename}"

            await session.commit()

            # Update cookie if username changed
            self.set_secure_cookie("uname", user.username)
            self.redirect("/profile")


class DeleteProfileHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self):
        user_id = self.current_user["id"]
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                await session.delete(user)
                await session.commit()

        # Clear cookies and redirect to home
        self.clear_cookie("uid")
        self.clear_cookie("uname")
        self.redirect("/")
