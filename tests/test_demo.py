"""Public demo boundaries, exercised with CSRF protection enabled."""
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
import re
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Project, Task, DemoSession
from app.demo import utcnow

ORIGIN = "https://taskflow.example.test"


@pytest.fixture
def demo_app(tmp_path):
    app = create_app({
        "TESTING": True, "SECRET_KEY": "testing-secret-that-is-at-least-32-characters",
        "DEMO_MODE": True, "PUBLIC_ORIGIN": ORIGIN,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'demo.db'}",
    })
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


def token(client, path="/"):
    response = client.get(path, base_url=ORIGIN, follow_redirects=True)
    return re.search(r'name="csrf-token" content="([^"]+)"', response.text).group(1)


def mutate(client, path, method="POST", csrf=None, **kwargs):
    if csrf is None:
        csrf = token(client)
    return client.open(path, method=method, base_url=ORIGIN,
                       headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}, **kwargs)


def start(client):
    response = mutate(client, "/demo/start")
    assert response.status_code == 302
    return int(response.location.rsplit("/", 1)[1])


def test_guest_start_seed_resume_cookie_and_no_registration(demo_app):
    client = demo_app.test_client()
    landing = client.get("/", base_url=ORIGIN)
    assert "Essayer la démo" in landing.text
    assert "Secure; HttpOnly" in landing.headers["Set-Cookie"]
    assert "SameSite=Lax" in landing.headers["Set-Cookie"]
    assert "S'inscrire" not in landing.text
    project_id = start(client)
    response = client.get(f"/api/projects/{project_id}", base_url=ORIGIN)
    assert response.status_code == 200
    assert len(response.json["data"]["tasks"]) == 3
    assert client.get("/dashboard", base_url=ORIGIN).status_code == 200
    assert mutate(client, "/demo/start").location.endswith("/dashboard")
    for path in ["/login", "/register"]:
        assert client.get(path, base_url=ORIGIN).status_code == 404
        assert mutate(client, path).status_code == 404
    with demo_app.app_context():
        assert DemoSession.query.count() == 1
        assert User.query.one().email.endswith("@demo.invalid")


def test_guest_crud_and_cross_guest_isolation(demo_app):
    alice, bob = demo_app.test_client(), demo_app.test_client()
    aid, bid = start(alice), start(bob)
    made = mutate(alice, f"/api/projects/{aid}/tasks", json={"title": "Tester le parcours"})
    assert made.status_code == 201
    tid = made.json["data"]["id"]
    path = f"/api/projects/{aid}/tasks/{tid}"
    assert mutate(alice, path, "PUT", json={"status": "doing"}).json["data"]["status"] == "doing"
    assert mutate(alice, path, "PUT", json={"status": "done"}).status_code == 200
    assert bob.get(f"/api/projects/{aid}", base_url=ORIGIN).status_code == 404
    assert bob.get(f"/projects/{aid}", base_url=ORIGIN).status_code == 404
    for method in ["PUT", "DELETE"]:
        assert mutate(bob, path, method, json={"status": "todo"}).status_code == 404
    assert mutate(bob, f"/api/projects/{bid}/tasks/{tid}", "DELETE").status_code == 404
    assert mutate(alice, path, "DELETE").status_code == 200
    project = mutate(alice, "/api/projects", json={"name": "Mon exemple"}).json["data"]
    assert mutate(alice, f"/api/projects/{project['id']}", "PUT", json={"name": "Autre exemple"}).status_code == 200
    assert mutate(alice, f"/api/projects/{project['id']}", "DELETE").status_code == 200


@pytest.mark.parametrize("csrf", ["", "invalid", "é"])
def test_guest_creation_requires_valid_csrf(demo_app, csrf):
    client = demo_app.test_client()
    token(client)
    assert mutate(client, "/demo/start", csrf=csrf).status_code == 403
    with demo_app.app_context():
        assert User.query.count() == 0


def test_foreign_origin_and_post_logout_only(demo_app):
    client = demo_app.test_client()
    pid = start(client)
    csrf = token(client)
    for headers in [
        {"Origin": "https://evil.test"}, {"Origin": "null"},
        {"Referer": "https://evil.test/path"}, {"Sec-Fetch-Site": "cross-site"},
    ]:
        headers["X-CSRF-Token"] = csrf
        response = client.post(f"/api/projects/{pid}/tasks", base_url=ORIGIN,
                               headers=headers, json={"title": "Interdit"})
        assert response.status_code == 403
    assert client.get("/logout", base_url=ORIGIN).status_code == 405
    assert mutate(client, "/logout").status_code == 302
    with demo_app.app_context():
        assert User.query.count() == Project.query.count() == Task.query.count() == 0


def test_resource_caps_expiration_and_cleanup(demo_app):
    demo_app.config.update(DEMO_MAX_GUESTS=2, DEMO_MAX_PROJECTS=2, DEMO_MAX_TASKS=4)
    client, other, blocked = [demo_app.test_client() for _ in range(3)]
    pid = start(client)
    start(other)
    assert mutate(blocked, "/demo/start").status_code == 503
    assert mutate(client, "/api/projects", json={"name": "Deuxième"}).status_code == 201
    assert mutate(client, "/api/projects", json={"name": "Trop"}).status_code == 409
    path = f"/api/projects/{pid}/tasks"
    assert mutate(client, path, json={"title": "Quatrième"}).status_code == 201
    assert mutate(client, path, json={"title": "Trop"}).status_code == 409
    with client.session_transaction(base_url=ORIGIN) as session:
        old_user_id = session["user_id"]
    with demo_app.app_context():
        db.session.get(DemoSession, old_user_id).expires_at = utcnow() - timedelta(seconds=1)
        db.session.commit()
    assert client.get("/api/projects", base_url=ORIGIN).status_code == 401
    start(blocked)
    with demo_app.app_context():
        assert db.session.get(User, old_user_id) is None
        assert db.session.get(Project, pid) is None
        assert Task.query.filter_by(project_id=pid).count() == 0
        assert DemoSession.query.count() == 2


def test_demo_session_nonce_blocks_stale_or_normal_sessions(demo_app):
    client = demo_app.test_client()
    start(client)
    with client.session_transaction(base_url=ORIGIN) as session:
        session["demo_nonce"] = "wrong-nonce"
    assert client.get("/api/projects", base_url=ORIGIN).status_code == 401


def test_concurrent_guest_requests_cannot_exceed_global_cap(demo_app):
    demo_app.config["DEMO_MAX_GUESTS"] = 3

    def create_guest(_):
        client = demo_app.test_client()
        return mutate(client, "/demo/start").status_code

    with ThreadPoolExecutor(max_workers=6) as executor:
        statuses = list(executor.map(create_guest, range(8)))
    assert statuses.count(302) == 3
    assert statuses.count(503) == 5
    with demo_app.app_context():
        assert User.query.count() == DemoSession.query.count() == 3


def test_headers_health_body_limit_and_xss_escaping(demo_app):
    client = demo_app.test_client()
    assert client.get("/healthz", base_url=ORIGIN).json == {"status": "ok"}
    assert client.get("/healthz", base_url="https://wrong.test").status_code == 400
    pid = start(client)
    response = mutate(client, f"/api/projects/{pid}/tasks", json={"title": "<script>alert(1)</script>"})
    assert response.status_code == 201
    page = client.get(f"/projects/{pid}", base_url=ORIGIN)
    assert "<script>alert(1)</script>" not in page.text
    assert "&lt;script&gt;" in page.text
    assert "script-src 'self';" in page.headers["Content-Security-Policy"]
    assert page.headers["Cache-Control"] == "no-store"
    assert page.headers["X-Frame-Options"] == "DENY"
    response = mutate(client, f"/api/projects/{pid}/tasks", json={"title": "x" * 30000})
    assert response.status_code == 413


def test_normal_auth_keeps_csrf_protection(tmp_path):
    app = create_app({"TESTING": True, "DEMO_MODE": False, "APP_ENV": "development", "PUBLIC_ORIGIN": "",
                      "SECRET_KEY": "normal-test", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'normal.db'}"})
    client = app.test_client()
    payload = {"username": "testuser", "email": "test@example.invalid", "password": "valid-password"}
    assert client.post("/register", data=payload).status_code == 403
    page = client.get("/register")
    csrf = re.search(r'name="csrf-token" content="([^"]+)"', page.text).group(1)
    assert client.post("/register", data={**payload, "csrf_token": csrf}).status_code == 302
    assert client.get("/api/projects").status_code == 200
    assert client.post("/api/projects", json={"name": "Sans CSRF"}).status_code == 403
