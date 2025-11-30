"""
Utility functions for JWT authentication.
"""

from functools import wraps


def jwt_required(method):
    """Decorator to require JWT authentication for handlers.

    Usage:
        class MyHandler(BaseAPIHandler):
            @jwt_required
            async def get(self):
                user = self.current_user
                # user is guaranteed to exist here
    """

    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        if not self.current_user:
            self.set_status(401)
            self.write({"error": "Authentication required"})
            return
        return await method(self, *args, **kwargs)

    return wrapper


def jwt_optional(method):
    """Decorator that allows JWT authentication but doesn't require it.

    Usage:
        class MyHandler(BaseAPIHandler):
            @jwt_optional
            async def get(self):
                user = self.current_user  # May be None
                if user:
                    # Authenticated logic
                else:
                    # Public logic
    """

    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        # Just call get_current_user to populate self.current_user
        _ = self.current_user
        return await method(self, *args, **kwargs)

    return wrapper
