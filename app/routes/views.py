"""
HTML view blueprint — renders Jinja2 templates for the browser UI.
"""
from flask import Blueprint, render_template, session, redirect, url_for, current_app
from ..models import Project
from ..helpers import get_current_user

views_bp = Blueprint("views", __name__)


def _require_login():
    if get_current_user() is None:
        session.clear()
        return redirect(url_for("views.index" if current_app.config["DEMO_MODE"] else "auth.login"))
    return None


@views_bp.route("/")
def index():
    if get_current_user() is not None:
        return redirect(url_for("views.dashboard"))
    if session.get("user_id"):
        session.clear()
    return render_template("index.html")


@views_bp.route("/dashboard")
def dashboard():
    redir = _require_login()
    if redir:
        return redir
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).all()
    return render_template("dashboard.html", user=user, projects=projects)


@views_bp.route("/projects/<int:project_id>")
def project_board(project_id: int):
    redir = _require_login()
    if redir:
        return redir
    user = get_current_user()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first_or_404()
    tasks = project.tasks
    return render_template("board.html", user=user, project=project, tasks=tasks)
