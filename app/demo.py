"""Isolated, temporary guest spaces containing fictional Kanban examples only."""
from datetime import datetime, timedelta, timezone
import secrets
from flask import Blueprint, current_app, session, redirect, url_for, render_template, abort
from .extensions import db
from .models import User, Project, Task, DemoSession
from .helpers import get_current_user

demo_bp = Blueprint("demo", __name__)


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def cleanup_expired():
    """Called within the same serialized write transaction as guest creation."""
    expired = DemoSession.query.filter(DemoSession.expires_at <= utcnow()).all()
    for guest in expired:
        user = db.session.get(User, guest.user_id)
        if user:
            db.session.delete(user)
    db.session.flush()


@demo_bp.post("/demo/start")
def start():
    if not current_app.config["DEMO_MODE"]:
        abort(404)
    cleanup_expired()
    if get_current_user() is not None:
        db.session.commit()
        return redirect(url_for("views.dashboard"))
    if DemoSession.query.count() >= current_app.config["DEMO_MAX_GUESTS"]:
        db.session.commit()
        return render_template("index.html", demo_busy=True), 503
    identifier = secrets.token_hex(16)
    nonce = secrets.token_hex(32)
    user = User(username=f"demo-{identifier}", email=f"{identifier}@demo.invalid",
                password_hash="!guest-no-password")
    user.demo_session = DemoSession(expires_at=utcnow() + timedelta(
        seconds=current_app.config["DEMO_TTL_SECONDS"]), nonce=nonce)
    project = Project(name="Préparer une présentation", description="Exemple fictif : essayez les boutons Avancer et Reculer.", color="#6366f1")
    project.tasks = [
        Task(title="Choisir les trois idées à présenter", description="Ajoutez une idée, modifiez ce texte ou créez votre propre tâche.", priority="high", status="todo"),
        Task(title="Créer les diapositives", description="Un exemple de tâche en cours.", priority="medium", status="doing"),
        Task(title="Fixer la date de présentation", description="Un exemple de tâche terminée.", priority="low", status="done"),
    ]
    user.projects.append(project)
    db.session.add(user)
    db.session.commit()
    session.clear()
    session.update(user_id=user.id, username="Invité démo", demo_nonce=nonce)
    return redirect(url_for("views.project_board", project_id=project.id))
