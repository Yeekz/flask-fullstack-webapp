"""Shared utility helpers used across route blueprints."""
from functools import wraps
from flask import jsonify, session, request
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
        if get_current_user() is None:
            session.clear()
            return api_response(error="Authentification requise.", status=401)
        return f(*args, **kwargs)
    return decorated


def json_fields(fields: dict[str, int], nullable=()):
    """Validate the API boundary before any ORM mutation; no implicit str coercion."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            body = request.get_json(silent=True)
            if not isinstance(body, dict):
                return api_response(error="Un objet JSON valide est requis.", status=400)
            for name, max_length in fields.items():
                if name not in body or (name in nullable and body[name] is None):
                    continue
                if not isinstance(body[name], str) or len(body[name]) > max_length:
                    return api_response(error=f"Champ '{name}' invalide : texte de {max_length} caractères maximum attendu.", status=400)
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user() -> User | None:
    """Return the logged-in User ORM object, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)
