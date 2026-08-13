"""
SQLAlchemy models: User, Project, Task.
All relationships use lazy loading; cascades ensure orphan cleanup.
"""
from datetime import date
from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    projects = db.relationship("Project", backref="owner", lazy=True, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": str(self.created_at),
        }

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, default="")
    color = db.Column(db.String(7), default="#6366f1")  # hex color for UI
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    tasks = db.relationship("Task", backref="project", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_tasks: bool = False) -> dict:
        data: dict = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": str(self.created_at),
            "task_count": len(self.tasks),
        }
        if include_tasks:
            data["tasks"] = [t.to_dict() for t in self.tasks]
        return data

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class Task(db.Model):
    __tablename__ = "tasks"

    STATUS_VALUES = ("todo", "doing", "done")
    PRIORITY_VALUES = ("low", "medium", "high")

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(10), default="todo", nullable=False)
    priority = db.Column(db.String(10), default="medium", nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": str(self.due_date) if self.due_date else None,
            "created_at": str(self.created_at),
            "project_id": self.project_id,
        }

    def __repr__(self) -> str:
        return f"<Task {self.title} [{self.status}]>"
