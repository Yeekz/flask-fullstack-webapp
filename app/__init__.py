"""
Gestionnaire de tâches & projets — Flask application factory.
"""
import os
from flask import Flask
from .extensions import db
from .models import User, Project, Task  # noqa: F401 — ensure models are registered


def create_app(config: dict | None = None) -> Flask:
    """Application factory pattern."""
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                template_folder=os.path.join(root, "templates"),
                static_folder=os.path.join(root, "static"),
                instance_relative_config=False)

    # --- Core configuration ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///tasks.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Override with test config if provided
    if config:
        app.config.update(config)

    # --- Extensions ---
    db.init_app(app)

    # --- Blueprints ---
    from .routes.auth import auth_bp
    from .routes.views import views_bp
    from .routes.api_projects import projects_bp
    from .routes.api_tasks import tasks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(tasks_bp, url_prefix="/api")

    # --- Database init ---
    with app.app_context():
        db.create_all()

    return app
