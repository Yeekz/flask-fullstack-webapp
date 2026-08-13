"""
HTML view blueprint — renders Jinja2 templates for the browser UI.
"""
from flask import Blueprint, render_template, session, redirect, url_for
from ..models import Project
from ..helpers import get_current_user

views_bp = Blueprint("views", __name__)


def _require_login():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return None


@views_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("views.dashboard"))
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
