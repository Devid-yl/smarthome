"""
JWT Authentication API endpoints for SmartHome.
"""
import json
import tornado.web
from sqlalchemy import select
from ..models import User
from ..database import async_session_maker
from ..auth import hash_password, verify_password
from ..jwt_auth import generate_token
from datetime import datetime


class BaseAPIHandler(tornado.web.RequestHandler):
    """Base handler for JWT REST APIs."""

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

    def write_json(self, data, status=200):
        self.set_status(status)
        self.write(json.dumps(data, default=str))

    def write_error_json(self, message, status=400):
        self.set_status(status)
        self.write(json.dumps({"error": message}))


class LoginJWTHandler(BaseAPIHandler):
    """POST /api/auth/jwt/login - Login with JWT token response."""

    async def post(self):
        try:
            data = json.loads(self.request.body)
        except json.JSONDecodeError:
            return self.write_error_json("Invalid JSON", 400)

        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not email or not password:
            return self.write_error_json(
                "Email and password are required", 400
            )

        async with async_session_maker() as session:
            # Find user by email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            if not user or not verify_password(password, user.password):
                return self.write_error_json(
                    "Invalid email or password", 401
                )

            if not user.is_active:
                return self.write_error_json(
                    "Account is not active", 403
                )

            # Generate JWT token
            token = generate_token(user.id, user.email)

            # Return token + user info
            self.write_json({
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "profile_image": user.profile_image,
                    "is_active": user.is_active,
                    "date_joined": user.date_joined.isoformat()
                    if user.date_joined else None
                }
            }, status=200)


class RegisterJWTHandler(BaseAPIHandler):
    """POST /api/auth/jwt/register - Register with JWT token response."""

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

            # Create new user
            hashed_pw = hash_password(password)
            new_user = User(
                username=username,
                email=email,
                password=hashed_pw,
                phone_number=phone or None,
                is_active=True,
                date_joined=datetime.utcnow()
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            # Generate JWT token
            token = generate_token(new_user.id, new_user.email)

            # Return token + user info
            self.write_json({
                "token": token,
                "user": {
                    "id": new_user.id,
                    "username": new_user.username,
                    "email": new_user.email,
                    "phone_number": new_user.phone_number,
                    "profile_image": new_user.profile_image,
                    "is_active": new_user.is_active,
                    "date_joined": new_user.date_joined.isoformat()
                    if new_user.date_joined else None
                }
            }, status=201)
