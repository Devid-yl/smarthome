import tornado.web
from sqlalchemy import select
from datetime import datetime
from ..models import User
from ..auth import verify_password, hash_password
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


class RegisterHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect("/")
            return
        self.render("register.html", error=None)

    async def post(self):
        if self.current_user:
            self.redirect("/")
            return

        username = self.get_argument("username", "")
        email = self.get_argument("email", "")
        password1 = self.get_argument("password1", "")
        password2 = self.get_argument("password2", "")

        # Validation
        if not all([username, email, password1, password2]):
            self.render("register.html", error="Tous les champs sont requis")
            return

        if password1 != password2:
            self.render("register.html", error="Mots de passe différents")
            return

        # Handle profile image upload
        profile_image_path = None
        if "profile_image" in self.request.files:
            fileinfo = self.request.files["profile_image"][0]
            if fileinfo["filename"]:
                from pathlib import Path
                
                # Generate unique filename
                ext = Path(fileinfo["filename"]).suffix
                filename = f"{username}_{datetime.now().timestamp()}{ext}"
                
                # Save to media/profile_images/
                from ..config import get_settings
                settings = get_settings()
                media_path = Path(settings["media_path"])
                profile_dir = media_path / "profile_images"
                profile_dir.mkdir(exist_ok=True)
                
                filepath = profile_dir / filename
                with open(filepath, "wb") as f:
                    f.write(fileinfo["body"])
                
                profile_image_path = f"profile_images/{filename}"

        async with async_session_maker() as session:
            # Check if username exists
            result = await session.execute(
                select(User).where(User.username == username)
            )
            if result.scalar_one_or_none():
                self.render(
                    "register.html",
                    error="Nom d'utilisateur déjà pris",
                )
                return

            # Create user
            hashed_pwd = hash_password(password1)
            new_user = User(
                username=username,
                email=email,
                password=hashed_pwd,
                is_active=True,
                date_joined=datetime.now(),
                profile_image=profile_image_path,
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            # Log in the user
            self.set_secure_cookie("uid", str(new_user.id))
            self.set_secure_cookie("uname", new_user.username)
            self.redirect("/")


class LoginHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.redirect("/")
            return
        self.render("login.html", error=None)

    async def post(self):
        if self.current_user:
            self.redirect("/")
            return

        username = self.get_argument("username", "")
        password = self.get_argument("password", "")

        if not username or not password:
            self.render(
                "login.html",
                error="Veuillez saisir identifiant et mot de passe",
            )
            return

        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()

            if not user or not verify_password(password, user.password or ""):
                self.render("login.html", error="Identifiants incorrects")
                return

            # Log in
            self.set_secure_cookie("uid", str(user.id))
            self.set_secure_cookie("uname", user.username)
            self.redirect("/")


class LogoutHandler(BaseHandler):
    def post(self):
        self.clear_cookie("uid")
        self.clear_cookie("uname")
        self.redirect("/login")
