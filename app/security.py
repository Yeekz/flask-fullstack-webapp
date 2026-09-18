"""Cookie-session CSRF protection for forms and JSON requests."""
import secrets
from urllib.parse import urlsplit
from flask import current_app, request, session
from sqlalchemy import text
from .extensions import db
from .helpers import api_response


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def install_security(app):
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def protect_mutations():
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return None
        if current_app.config["CSRF_ENABLED"]:
            expected_origin = current_app.config["PUBLIC_ORIGIN"] or request.host_url.rstrip("/")
            origin = request.headers.get("Origin")
            referer = request.headers.get("Referer")
            if origin is not None:
                valid_origin = origin == expected_origin
            elif referer:
                parsed = urlsplit(referer)
                valid_origin = f"{parsed.scheme}://{parsed.netloc}" == expected_origin
            else:
                # Non-browser clients may omit Origin, but still need the session token.
                valid_origin = True
            supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
            expected = session.get("csrf_token", "")
            if (not valid_origin or request.headers.get("Sec-Fetch-Site") == "cross-site"
                    or not expected or not isinstance(supplied, str)
                    or not secrets.compare_digest(expected.encode(), supplied.encode())):
                return api_response(error="Session de sécurité expirée. Rechargez la page puis réessayez.", status=403)
        if current_app.config["DEMO_MODE"]:
            # Serialize quota check and insert across processes, not only Python threads.
            db.session.execute(text("BEGIN IMMEDIATE"))

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        if current_app.config.get("SESSION_COOKIE_SECURE"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
