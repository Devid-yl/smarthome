"""JWT Authentication utilities for SmartHome API."""

import jwt
import datetime
import os
from typing import Optional, Dict, Any


# Secret key for JWT - should be in environment variable
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # Token expires after 24 hours


def generate_token(user_id: int, email: str) -> str:
    """Generate JWT token for authenticated user.

    Args:
        user_id: User ID
        email: User email

    Returns:
        JWT token as string
    """
    exp_time = datetime.datetime.utcnow() + datetime.timedelta(
        hours=JWT_EXPIRATION_HOURS
    )

    payload = {
        "user_id": user_id,
        "email": email,
        "exp": exp_time,
        "iat": datetime.datetime.utcnow(),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Invalid token
        return None


def extract_token_from_header(authorization_header: Optional[str]) -> Optional[str]:
    """Extract JWT token from Authorization header.

    Args:
        authorization_header: Authorization header value
            (e.g., "Bearer token123")

    Returns:
        Token string if valid format, None otherwise
    """
    if not authorization_header:
        return None

    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]
