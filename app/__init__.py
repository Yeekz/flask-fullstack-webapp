"""
Gestionnaire de tâches & projets — Flask application factory.
"""
import os
import secrets
from urllib.parse import urlsplit
from flask import Flask, jsonify
from .extensions import db
from .models import User, Project, Task  # noqa: F401 — ensure models are registered


def create_app(config: dict | None = None) -> Flask:
    """Application factory pattern."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                template_folder=os.path.join(root, "templates"),
                static_folder=os.path.join(root, "static"),
                instance_relative_config=False)

    # --- Core configuration ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    app.config["DEMO_MODE"] = os.environ.get("DEMO_MODE") == "1"
    app.config["APP_ENV"] = os.environ.get("APP_ENV", "development")
    app.config["PUBLIC_ORIGIN"] = os.environ.get("PUBLIC_ORIGIN", "").rstrip("/")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///tasks.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config.update(CSRF_ENABLED=True, MAX_CONTENT_LENGTH=24 * 1024,
                      MAX_FORM_MEMORY_SIZE=24 * 1024, MAX_FORM_PARTS=15,
                      DEMO_MAX_GUESTS=40, DEMO_MAX_PROJECTS=3,
                      DEMO_MAX_TASKS=20, DEMO_TTL_SECONDS=7200,
                      SESSION_COOKIE_NAME="taskflow_session")

    # Override with test config if provided
    if config:
        app.config.update(config)

    public = app.config["DEMO_MODE"] or app.config["APP_ENV"] == "production"
    if public:
        if not app.testing and (not os.environ.get("SECRET_KEY") or
                               len(app.config["SECRET_KEY"]) < 32):
            raise RuntimeError("Une SECRET_KEY aléatoire de 32 caractères minimum est requise.")
        origin = urlsplit(app.config["PUBLIC_ORIGIN"])
        if origin.scheme != "https" or not origin.netloc or origin.path or origin.query or origin.fragment or origin.username:
            raise RuntimeError("PUBLIC_ORIGIN doit être une origine HTTPS sans chemin.")
        app.config["TRUSTED_HOSTS"] = [origin.netloc]
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["DEBUG"] = False
        if not app.testing and not app.config["CSRF_ENABLED"]:
            raise RuntimeError("CSRF doit rester activé en production.")
    if app.config["DEMO_MODE"] and not app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        raise RuntimeError("Le mode démo utilise SQLite et ses transactions immédiates.")

    # --- Extensions ---
    db.init_app(app)

    # --- Blueprints ---
    from .routes.auth import auth_bp
    from .routes.views import views_bp
    from .routes.api_projects import projects_bp
    from .routes.api_tasks import tasks_bp
    from .demo import demo_bp
    from .security import install_security

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(tasks_bp, url_prefix="/api")
    app.register_blueprint(demo_bp)
    install_security(app)

    @app.get("/healthz")
    def healthz():
        db.session.execute(db.text("SELECT 1"))
        return jsonify(status="ok")

    # --- Database init ---
    with app.app_context():
        db.create_all()

    return app
