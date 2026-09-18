"""Tests for the REST API — Projects resource."""
import json
import pytest
from tests.conftest import register_and_login


class TestProjectsAPI:
    def test_list_requires_auth(self, client):
        res = client.get("/api/projects")
        assert res.status_code == 401
        data = res.get_json()
        assert data["success"] is False

    def test_create_requires_auth(self, client):
        res = client.post("/api/projects",
                          data=json.dumps({"name": "Secret"}),
                          content_type="application/json")
        assert res.status_code == 401

    def test_create_project(self, client):
        register_and_login(client, "projuser1", "testpassword123")
        res = client.post("/api/projects",
                          data=json.dumps({"name": "Mon Projet", "description": "Test desc", "color": "#6366f1"}),
                          content_type="application/json")
        assert res.status_code == 201
        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "Mon Projet"
        assert data["data"]["color"] == "#6366f1"

    def test_create_project_missing_name(self, client):
        register_and_login(client, "projuser2", "testpassword123")
        res = client.post("/api/projects",
                          data=json.dumps({"name": ""}),
                          content_type="application/json")
        assert res.status_code == 400
        assert res.get_json()["success"] is False

    def test_list_projects(self, client):
        register_and_login(client, "projuser3", "testpassword123")
        client.post("/api/projects",
                    data=json.dumps({"name": "Projet A", "color": "#6366f1"}),
                    content_type="application/json")
        res = client.get("/api/projects")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

    def test_get_project(self, client):
        register_and_login(client, "projuser4", "testpassword123")
        create_res = client.post("/api/projects",
                                 data=json.dumps({"name": "Projet Detail", "color": "#6366f1"}),
                                 content_type="application/json")
        proj_id = create_res.get_json()["data"]["id"]
        res = client.get(f"/api/projects/{proj_id}")
        assert res.status_code == 200
        assert res.get_json()["data"]["id"] == proj_id

    def test_update_project(self, client):
        register_and_login(client, "projuser5", "testpassword123")
        create_res = client.post("/api/projects",
                                 data=json.dumps({"name": "Ancien Nom", "color": "#6366f1"}),
                                 content_type="application/json")
        proj_id = create_res.get_json()["data"]["id"]
        res = client.put(f"/api/projects/{proj_id}",
                         data=json.dumps({"name": "Nouveau Nom", "color": "#6366f1"}),
                         content_type="application/json")
        assert res.status_code == 200
        assert res.get_json()["data"]["name"] == "Nouveau Nom"

    def test_delete_project(self, client):
        register_and_login(client, "projuser6", "testpassword123")
        create_res = client.post("/api/projects",
                                 data=json.dumps({"name": "A Supprimer", "color": "#6366f1"}),
                                 content_type="application/json")
        proj_id = create_res.get_json()["data"]["id"]
        res = client.delete(f"/api/projects/{proj_id}")
        assert res.status_code == 200
        assert res.get_json()["data"]["deleted_id"] == proj_id

        # Verify it's gone
        res2 = client.get(f"/api/projects/{proj_id}")
        assert res2.status_code == 404

    def test_cannot_access_other_user_project(self, client):
        register_and_login(client, "owner1", "testpassword123")
        create_res = client.post("/api/projects",
                                 data=json.dumps({"name": "Private", "color": "#6366f1"}),
                                 content_type="application/json")
        proj_id = create_res.get_json()["data"]["id"]

        # Switch to another user
        client.post("/logout")
        register_and_login(client, "intruder1", "testpassword123")
        res = client.get(f"/api/projects/{proj_id}")
        assert res.status_code == 404
