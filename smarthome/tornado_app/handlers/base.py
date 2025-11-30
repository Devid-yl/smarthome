"""
Base handler for all API endpoints with JWT authentication.
"""

import json
import tornado.web


class BaseAPIHandler(tornado.web.RequestHandler):
    """Base handler pour les API REST avec authentification JWT."""

    # Set to True in subclasses that don't require authentication
    # (e.g., login, register endpoints)
    SKIP_AUTH_CHECK = False

    def check_xsrf_cookie(self):
        """Disable XSRF for REST APIs."""
        pass

    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
        )
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def options(self, *args):
        self.set_status(204)
        self.finish()

    def prepare(self):
        """Called before each request - enforce authentication."""
        # Skip auth check for OPTIONS requests (CORS preflight)
        if self.request.method == "OPTIONS":
            return

        # Skip auth check if handler explicitly allows it
        if self.SKIP_AUTH_CHECK:
            return

        # Verify authentication
        user = self.get_current_user()
        if not user:
            self.set_status(401)
            self.write(json.dumps({"error": "Authentication required"}))
            self.finish()
            return

    def get_current_user(self):
        """Get current user from JWT token or cookie fallback."""
        # Try JWT authentication first
        auth_header = self.request.headers.get("Authorization")
        if auth_header:
            from ..jwt_auth import extract_token_from_header, verify_token

            token = extract_token_from_header(auth_header)
            if token:
                payload = verify_token(token)
                if payload:
                    return {"id": payload.get("user_id"), "email": payload.get("email")}

        # Fallback to cookie-based auth
        user_id = self.get_secure_cookie("uid")
        if not user_id:
            return None
        username = self.get_secure_cookie("uname")
        return {
            "id": int(user_id.decode()),
            "username": username.decode() if username else None,
        }

    def write_json(self, data, status=200):
        self.set_status(status)
        self.write(json.dumps(data, default=str))

    def write_error_json(self, message, status=400):
        self.set_status(status)
        self.write(json.dumps({"error": message}))
