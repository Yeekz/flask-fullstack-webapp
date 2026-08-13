"""Tests for authentication routes: register, login, logout."""
import pytest
from tests.conftest import register_and_login


class TestRegister:
    def test_register_page_loads(self, client):
        res = client.get("/register")
        assert res.status_code == 200
        assert b"Cr" in res.data  # "Créer"

    def test_register_success(self, client):
        res = client.post("/register", data={
            "username": "alice",
            "email": "alice@example.com",
            "password": "strongpassword",
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"Tableau de bord" in res.data or b"alice" in res.data

    def test_register_duplicate_username(self, client):
        client.post("/register", data={
            "username": "bob",
            "email": "bob@example.com",
            "password": "strongpassword",
        })
        res = client.post("/register", data={
            "username": "bob",
            "email": "bob2@example.com",
            "password": "strongpassword",
        })
        assert res.status_code == 409

    def test_register_short_password(self, client):
        res = client.post("/register", data={
            "username": "charlie",
            "email": "charlie@example.com",
            "password": "short",
        })
        assert res.status_code == 400

    def test_register_invalid_email(self, client):
        res = client.post("/register", data={
            "username": "diana",
            "email": "notanemail",
            "password": "strongpassword",
        })
        assert res.status_code == 400


class TestLogin:
    def test_login_page_loads(self, client):
        res = client.get("/login")
        assert res.status_code == 200

    def test_login_success(self, client):
        client.post("/register", data={
            "username": "eve",
            "email": "eve@example.com",
            "password": "correctpassword",
        })
        res = client.post("/login", data={
            "username": "eve",
            "password": "correctpassword",
        }, follow_redirects=True)
        assert res.status_code == 200

    def test_login_wrong_password(self, client):
        client.post("/register", data={
            "username": "frank",
            "email": "frank@example.com",
            "password": "correctpassword",
        })
        res = client.post("/login", data={
            "username": "frank",
            "password": "wrongpassword",
        })
        assert res.status_code == 401

    def test_logout_redirects(self, client):
        register_and_login(client, "logoutuser", "testpassword123")
        res = client.get("/logout", follow_redirects=False)
        assert res.status_code in (301, 302)
