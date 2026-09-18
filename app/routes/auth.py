"""
Authentication blueprint — register, login, logout.
Passwords are hashed with werkzeug.security (pbkdf2:sha256).
"""
from flask import Blueprint, request, session, redirect, url_for, render_template, flash, current_app, abort
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import User
from ..helpers import get_current_user

auth_bp = Blueprint("auth", __name__)

MIN_PASSWORD_LEN = 8


def _validate_register(username: str, email: str, password: str) -> str | None:
    """Return an error string if validation fails, else None."""
    if not username or len(username) < 3:
        return "Le nom d'utilisateur doit faire au moins 3 caractères."
    if not email or "@" not in email:
        return "Adresse e-mail invalide."
    if len(password) < MIN_PASSWORD_LEN:
        return f"Le mot de passe doit faire au moins {MIN_PASSWORD_LEN} caractères."
    return None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_app.config["DEMO_MODE"]:
        abort(404)
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = _validate_register(username, email, password)
    if error:
        flash(error, "danger")
        return render_template("register.html"), 400

    if User.query.filter_by(username=username).first():
        flash("Ce nom d'utilisateur est déjà pris.", "danger")
        return render_template("register.html"), 409

    if User.query.filter_by(email=email).first():
        flash("Cet e-mail est déjà utilisé.", "danger")
        return render_template("register.html"), 409

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()

    session.clear()
    session["user_id"] = user.id
    session["username"] = user.username
    flash(f"Bienvenue, {user.username} !", "success")
    return redirect(url_for("views.dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_app.config["DEMO_MODE"]:
        abort(404)
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Identifiant et mot de passe requis.", "danger")
        return render_template("login.html"), 400

    user = User.query.filter_by(username=username).first()
    if not user or user.demo_session or not check_password_hash(user.password_hash, password):
        flash("Identifiant ou mot de passe incorrect.", "danger")
        return render_template("login.html"), 401

    session.clear()
    session["user_id"] = user.id
    session["username"] = user.username
    return redirect(url_for("views.dashboard"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    if current_app.config["DEMO_MODE"]:
        user = get_current_user()
        if user is not None:
            db.session.delete(user)
            db.session.commit()
    session.clear()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("views.index" if current_app.config["DEMO_MODE"] else "auth.login"))
