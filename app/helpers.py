"""Shared utility helpers used across route blueprints."""
from functools import wraps
from flask import jsonify, session
from .models import User
from .extensions import db


def api_response(data=None, error: str | None = None, status: int = 200):
    """Consistent JSON envelope: {success, data, error}."""
    return jsonify({
        "success": error is None,
        "data": data,
        "error": error,
    }), status


def login_required(f):
    """Decorator: block unauthenticated requests with 401."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return api_response(error="Authentification requise.", status=401)
        return f(*args, **kwargs)
    return decorated


def get_current_user() -> User | None:
    """Return the logged-in User ORM object, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)
