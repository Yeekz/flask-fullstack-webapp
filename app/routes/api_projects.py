"""
REST API — Projects resource.
All endpoints require authentication.
Base URL: /api/projects
"""
from flask import Blueprint, request
from ..extensions import db
from ..models import Project
from ..helpers import api_response, login_required, get_current_user, json_fields

projects_bp = Blueprint("projects", __name__)

ALLOWED_COLORS = {
    "#6366f1", "#ec4899", "#f59e0b", "#10b981",
    "#3b82f6", "#ef4444", "#8b5cf6", "#14b8a6",
}


def _validate_project(name: str, color: str) -> str | None:
    if not name or len(name.strip()) < 2:
        return "Le nom du projet doit faire au moins 2 caractères."
    if color and color not in ALLOWED_COLORS:
        return f"Couleur invalide. Valeurs autorisées : {', '.join(ALLOWED_COLORS)}."
    return None


@projects_bp.route("/projects", methods=["GET"])
@login_required
def list_projects():
    user = get_current_user()
    projects = Project.query.filter_by(user_id=user.id).order_by(Project.created_at.desc()).all()
    return api_response(data=[p.to_dict() for p in projects])


@projects_bp.route("/projects/<int:project_id>", methods=["GET"])
@login_required
def get_project(project_id: int):
    user = get_current_user()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return api_response(error="Projet introuvable.", status=404)
    return api_response(data=project.to_dict(include_tasks=True))


@projects_bp.route("/projects", methods=["POST"])
@login_required
@json_fields({"name": 128, "description": 10000, "color": 7})
def create_project():
    user = get_current_user()
    body = request.get_json(silent=True) or {}

    name = str(body.get("name", "")).strip()
    description = str(body.get("description", "")).strip()
    color = str(body.get("color", "#6366f1")).strip()

    error = _validate_project(name, color)
    if error:
        return api_response(error=error, status=400)

    project = Project(name=name, description=description, color=color, user_id=user.id)
    db.session.add(project)
    db.session.commit()
    return api_response(data=project.to_dict(), status=201)


@projects_bp.route("/projects/<int:project_id>", methods=["PUT"])
@login_required
@json_fields({"name": 128, "description": 10000, "color": 7})
def update_project(project_id: int):
    user = get_current_user()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return api_response(error="Projet introuvable.", status=404)

    body = request.get_json(silent=True) or {}
    name = str(body.get("name", project.name)).strip()
    color = str(body.get("color", project.color)).strip()
    description = str(body.get("description", project.description)).strip()

    error = _validate_project(name, color)
    if error:
        return api_response(error=error, status=400)

    project.name = name
    project.description = description
    project.color = color
    db.session.commit()
    return api_response(data=project.to_dict())


@projects_bp.route("/projects/<int:project_id>", methods=["DELETE"])
@login_required
def delete_project(project_id: int):
    user = get_current_user()
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return api_response(error="Projet introuvable.", status=404)

    db.session.delete(project)
    db.session.commit()
    return api_response(data={"deleted_id": project_id})
