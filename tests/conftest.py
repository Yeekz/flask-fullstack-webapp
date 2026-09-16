"""
Pytest fixtures shared across all test modules.
Uses an in-memory SQLite database so tests are fully isolated.
"""
import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="function")
def app():
    """Create an isolated application and in-memory DB for each test."""
    test_config = {
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    }
    application = create_app(config=test_config)
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Return a test client. Each test gets a fresh client."""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Provide the DB and rollback after each test to keep isolation."""
    with app.app_context():
        yield _db
        _db.session.rollback()


def register_and_login(client, username="testuser", password="testpassword123"):
    """Helper: register + login, return the client with active session."""
    client.post("/register", data={
        "username": username,
        "email": f"{username}@example.com",
        "password": password,
    }, follow_redirects=True)
    client.post("/login", data={
        "username": username,
        "password": password,
    }, follow_redirects=True)
    return client
