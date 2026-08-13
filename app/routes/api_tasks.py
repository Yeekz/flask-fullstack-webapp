"""
REST API — Tasks resource.
All endpoints require authentication.
Base URL: /api/projects/<id>/tasks
"""
from datetime import date
from flask import Blueprint, request
from ..extensions import db
from ..models import Task, Project
from ..helpers import api_response, login_required, get_current_user

tasks_bp = Blueprint("tasks", __name__)


def _get_project_for_user(project_id: int):
    """Return the project if it belongs to the current user, else None."""
    user = get_current_user()
    return Project.query.filter_by(id=project_id, user_id=user.id).first()


def _validate_task(title: str, status: str, priority: str, due_date_str: str | None) -> str | None:
    if not title or len(title.strip()) < 2:
        return "Le titre de la tâche doit faire au moins 2 caractères."
    if status not in Task.STATUS_VALUES:
        return f"Statut invalide. Valeurs : {', '.join(Task.STATUS_VALUES)}."
    if priority not in Task.PRIORITY_VALUES:
        return f"Priorité invalide. Valeurs : {', '.join(Task.PRIORITY_VALUES)}."
    if due_date_str:
        try:
            date.fromisoformat(due_date_str)
        except ValueError:
            return "Format de date invalide (attendu : YYYY-MM-DD)."
    return None


@tasks_bp.route("/projects/<int:project_id>/tasks", methods=["GET"])
@login_required
def list_tasks(project_id: int):
    project = _get_project_for_user(project_id)
    if not project:
        return api_response(error="Projet introuvable.", status=404)

    status_filter = request.args.get("status")
    query = Task.query.filter_by(project_id=project_id)
    if status_filter and status_filter in Task.STATUS_VALUES:
        query = query.filter_by(status=status_filter)

    tasks = query.order_by(Task.created_at.asc()).all()
    return api_response(data=[t.to_dict() for t in tasks])


@tasks_bp.route("/projects/<int:project_id>/tasks", methods=["POST"])
@login_required
def create_task(project_id: int):
    project = _get_project_for_user(project_id)
    if not project:
        return api_response(error="Projet introuvable.", status=404)

    body = request.get_json(silent=True) or {}
    title = str(body.get("title", "")).strip()
    description = str(body.get("description", "")).strip()
    status = str(body.get("status", "todo")).strip()
    priority = str(body.get("priority", "medium")).strip()
    due_date_str = body.get("due_date")

    error = _validate_task(title, status, priority, due_date_str)
    if error:
        return api_response(error=error, status=400)

    due_date = date.fromisoformat(due_date_str) if due_date_str else None
    task = Task(
        title=title,
        description=description,
        status=status,
        priority=priority,
        due_date=due_date,
        project_id=project_id,
    )
    db.session.add(task)
    db.session.commit()
    return api_response(data=task.to_dict(), status=201)


@tasks_bp.route("/projects/<int:project_id>/tasks/<int:task_id>", methods=["GET"])
@login_required
def get_task(project_id: int, task_id: int):
    project = _get_project_for_user(project_id)
    if not project:
        return api_response(error="Projet introuvable.", status=404)

    task = Task.query.filter_by(id=task_id, project_id=project_id).first()
    if not task:
        return api_response(error="Tâche introuvable.", status=404)
    return api_response(data=task.to_dict())


@tasks_bp.route("/projects/<int:project_id>/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task(project_id: int, task_id: int):
    project = _get_project_for_user(project_id)
    if not project:
        return api_response(error="Projet introuvable.", status=404)

    task = Task.query.filter_by(id=task_id, project_id=project_id).first()
    if not task:
        return api_response(error="Tâche introuvable.", status=404)

    body = request.get_json(silent=True) or {}
    title = str(body.get("title", task.title)).strip()
    description = str(body.get("description", task.description)).strip()
    status = str(body.get("status", task.status)).strip()
    priority = str(body.get("priority", task.priority)).strip()
    due_date_str = body.get("due_date", str(task.due_date) if task.due_date else None)

    error = _validate_task(title, status, priority, due_date_str)
    if error:
        return api_response(error=error, status=400)

    task.title = title
    task.description = description
    task.status = status
    task.priority = priority
    task.due_date = date.fromisoformat(due_date_str) if due_date_str else None
    db.session.commit()
    return api_response(data=task.to_dict())


@tasks_bp.route("/projects/<int:project_id>/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(project_id: int, task_id: int):
    project = _get_project_for_user(project_id)
    if not project:
        return api_response(error="Projet introuvable.", status=404)

    task = Task.query.filter_by(id=task_id, project_id=project_id).first()
    if not task:
        return api_response(error="Tâche introuvable.", status=404)

    db.session.delete(task)
    db.session.commit()
    return api_response(data={"deleted_id": task_id})
