"""
API REST pour la gestion des utilisateurs
"""
import json
import tornado.web
from sqlalchemy import select
from ..models import User
from ..database import async_session_maker
from ..auth import hash_password, verify_password
from datetime import datetime
import os


class BaseAPIHandler(tornado.web.RequestHandler):
    """Base handler pour les API REST."""

    def check_xsrf_cookie(self):
        """Disable XSRF for REST APIs."""
        pass

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods",
                        "GET, POST, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers",
                        "Content-Type, Authorization")

    def options(self, *args):
        self.set_status(204)
        self.finish()

    def get_current_user(self):
        user_id = self.get_secure_cookie("uid")
        if not user_id:
            return None
        username = self.get_secure_cookie("uname")
        return {
            "id": int(user_id.decode()),
            "username": username.decode() if username else None
        }

    def write_json(self, data, status=200):
        self.set_status(status)
        self.write(json.dumps(data, default=str))

    def write_error_json(self, message, status=400):
        self.set_status(status)
        self.write(json.dumps({"error": message}))


class RegisterAPIHandler(BaseAPIHandler):
    """POST /api/auth/register - Inscription d'un utilisateur"""

    async def post(self):
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            return self.write_error_json("Invalid JSON", 400)

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        phone = data.get("phone", "").strip()

        if not username or not email or not password:
            return self.write_error_json(
                "Username, email and password are required", 400
            )

        async with async_session_maker() as session:
            # Check if user already exists
            result = await session.execute(
                select(User).where(
                    (User.username == username) | (User.email == email)
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                return self.write_error_json(
                    "Username or email already exists", 409
                )

            # Create le nouvel utilisateur
            hashed_pw = hash_password(password)
            new_user = User(
                username=username,
                email=email,
                password=hashed_pw,
                phone_number=phone or None,
                is_active=True,
                date_joined=datetime.utcnow()
            )

            # Handle profile photo upload if present
            profile_image = data.get("profile_image")
            if profile_image:
                # TODO: handle base64 or URL upload
                new_user.profile_image = profile_image

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            # Auto-login after registration
            self.set_secure_cookie("uid", str(new_user.id))
            self.set_secure_cookie("uname", new_user.username)

            self.write_json({
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "message": "User created successfully"
            }, 201)


class LoginAPIHandler(BaseAPIHandler):
    """POST /api/auth/login - Connexion d'un utilisateur"""

    async def post(self):
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            return self.write_error_json("Invalid JSON", 400)

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return self.write_error_json(
                "Username and password are required", 400
            )

        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()

            if not user or not verify_password(password, user.password):
                return self.write_error_json(
                    "Invalid username or password", 401
                )

            if not user.is_active:
                return self.write_error_json("Account is deactivated", 403)

            # Create la session
            self.set_secure_cookie("uid", str(user.id))
            self.set_secure_cookie("uname", user.username)

            self.write_json({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "profile_image": user.profile_image,
                "message": "Login successful"
            })


class LogoutAPIHandler(BaseAPIHandler):
    """POST /api/auth/logout - Déconnexion"""

    async def post(self):
        self.clear_cookie("uid")
        self.clear_cookie("uname")
        self.write_json({"message": "Logged out successfully"})


class CurrentUserAPIHandler(BaseAPIHandler):
    """GET /api/auth/me - Récupérer l'utilisateur connecté"""

    async def get(self):
        user = self.get_current_user()
        if not user:
            return self.write_error_json("Not authenticated", 401)

        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user["id"])
            )
            db_user = result.scalar_one_or_none()

            if not db_user:
                return self.write_error_json("User not found", 404)

            self.write_json({
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "phone_number": db_user.phone_number,
                "profile_image": db_user.profile_image,
                "is_active": db_user.is_active,
                "date_joined": db_user.date_joined.isoformat()
                if db_user.date_joined else None
            })


class UserProfileAPIHandler(BaseAPIHandler):
    """
    GET /api/users/{id} - Récupérer le profil d'un utilisateur
    PUT /api/users/{id} - Modifier le profil
    DELETE /api/users/{id} - Supprimer le compte
    """

    async def get(self, user_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == int(user_id))
            )
            user = result.scalar_one_or_none()

            if not user:
                return self.write_error_json("User not found", 404)

            # Seul l'utilisateur lui-même peut voir son profil complet
            if current_user["id"] != user.id:
                return self.write_json({
                    "id": user.id,
                    "username": user.username,
                    "profile_image": user.profile_image
                })

            self.write_json({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "profile_image": user.profile_image,
                "is_active": user.is_active,
                "date_joined": user.date_joined.isoformat()
                if user.date_joined else None
            })

    async def put(self, user_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        if current_user["id"] != int(user_id):
            return self.write_error_json("Unauthorized", 403)

        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            return self.write_error_json("Invalid JSON", 400)

        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == int(user_id))
            )
            user = result.scalar_one_or_none()

            if not user:
                return self.write_error_json("User not found", 404)

            # Mettre à jour les champs autorisés
            if "email" in data:
                user.email = data["email"].strip()
            if "phone_number" in data:
                user.phone_number = data["phone_number"].strip() or None
            if "profile_image" in data:
                user.profile_image = data["profile_image"]

            # Changer le mot de passe si fourni
            if "password" in data and data["password"].strip():
                user.password = hash_password(data["password"].strip())

            await session.commit()
            await session.refresh(user)

            self.write_json({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "profile_image": user.profile_image,
                "message": "Profile updated successfully"
            })

    async def delete(self, user_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        if current_user["id"] != int(user_id):
            return self.write_error_json("Unauthorized", 403)

        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == int(user_id))
            )
            user = result.scalar_one_or_none()

            if not user:
                return self.write_error_json("User not found", 404)

            await session.delete(user)
            await session.commit()

            # Delete la session
            self.clear_cookie("uid")
            self.clear_cookie("uname")

            self.write_json({
                "message": "User account deleted successfully"
            })


class UploadProfileImageHandler(BaseAPIHandler):
    """POST /api/users/{id}/upload-image - Upload photo de profil"""

    async def post(self, user_id):
        current_user = self.get_current_user()
        if not current_user:
            return self.write_error_json("Not authenticated", 401)

        if current_user["id"] != int(user_id):
            return self.write_error_json("Unauthorized", 403)

        # Retrieve le fichier uploadé
        if "image" not in self.request.files:
            return self.write_error_json("No file uploaded", 400)

        file_info = self.request.files["image"][0]
        filename = file_info["filename"]
        content = file_info["body"]
        
        # Vérifier la taille (max 5 Mo)
        if len(content) > 5 * 1024 * 1024:
            return self.write_error_json("File too large (max 5MB)", 400)

        # Sauvegarder le fichier
        from pathlib import Path
        media_dir = Path(__file__).resolve().parents[3] / "media" / \
            "profile_images"
        media_dir.mkdir(parents=True, exist_ok=True)

        # Nom unique avec timestamp
        ext = filename.split(".")[-1] if "." in filename else "jpg"
        unique_filename = f"user_{user_id}_{int(datetime.utcnow(
        ).timestamp())}.{ext}"
        filepath = media_dir / unique_filename

        with open(filepath, "wb") as f:
            f.write(content)

        # Mettre à jour la DB
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == int(user_id))
            )
            user = result.scalar_one_or_none()

            if user:
                user.profile_image = f"/media/profile_images/{unique_filename}"
                await session.commit()

        self.write_json({
            "profile_image": f"/media/profile_images/{unique_filename}",
            "message": "Profile image uploaded successfully"
        }, 201)
