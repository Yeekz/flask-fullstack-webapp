"""Tests for the REST API — Tasks resource."""
import json
import pytest
from tests.conftest import register_and_login


def create_project_for(client, name="Test Project"):
    """Helper: create a project and return its id."""
    res = client.post("/api/projects",
                      data=json.dumps({"name": name, "color": "#6366f1"}),
                      content_type="application/json")
    return res.get_json()["data"]["id"]


class TestTasksAPI:
    def test_list_tasks_requires_auth(self, client):
        res = client.get("/api/projects/999/tasks")
        assert res.status_code == 401

    def test_create_task_requires_auth(self, client):
        res = client.post("/api/projects/999/tasks",
                          data=json.dumps({"title": "Task"}),
                          content_type="application/json")
        assert res.status_code == 401

    def test_create_task(self, client):
        register_and_login(client, "taskuser1", "testpassword123")
        proj_id = create_project_for(client, "Project T1")
        res = client.post(f"/api/projects/{proj_id}/tasks",
                          data=json.dumps({
                              "title": "Ma première tâche",
                              "description": "Description test",
                              "status": "todo",
                              "priority": "high",
                              "due_date": "2025-12-31",
                          }),
                          content_type="application/json")
        assert res.status_code == 201
        data = res.get_json()
        assert data["success"] is True
        task = data["data"]
        assert task["title"] == "Ma première tâche"
        assert task["status"] == "todo"
        assert task["priority"] == "high"
        assert task["due_date"] == "2025-12-31"
        assert task["project_id"] == proj_id

    def test_create_task_missing_title(self, client):
        register_and_login(client, "taskuser2", "testpassword123")
        proj_id = create_project_for(client, "Project T2")
        res = client.post(f"/api/projects/{proj_id}/tasks",
                          data=json.dumps({"title": ""}),
                          content_type="application/json")
        assert res.status_code == 400

    def test_create_task_invalid_status(self, client):
        register_and_login(client, "taskuser3", "testpassword123")
        proj_id = create_project_for(client, "Project T3")
        res = client.post(f"/api/projects/{proj_id}/tasks",
                          data=json.dumps({"title": "Task", "status": "invalid"}),
                          content_type="application/json")
        assert res.status_code == 400

    def test_list_tasks(self, client):
        register_and_login(client, "taskuser4", "testpassword123")
        proj_id = create_project_for(client, "Project T4")
        client.post(f"/api/projects/{proj_id}/tasks",
                    data=json.dumps({"title": "Tâche 1", "status": "todo", "priority": "low"}),
                    content_type="application/json")
        res = client.get(f"/api/projects/{proj_id}/tasks")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_list_tasks_with_status_filter(self, client):
        register_and_login(client, "taskuser5", "testpassword123")
        proj_id = create_project_for(client, "Project T5")
        client.post(f"/api/projects/{proj_id}/tasks",
                    data=json.dumps({"title": "Todo Task", "status": "todo", "priority": "low"}),
                    content_type="application/json")
        client.post(f"/api/projects/{proj_id}/tasks",
                    data=json.dumps({"title": "Done Task", "status": "done", "priority": "low"}),
                    content_type="application/json")
        res = client.get(f"/api/projects/{proj_id}/tasks?status=done")
        data = res.get_json()
        assert all(t["status"] == "done" for t in data["data"])

    def test_update_task_status(self, client):
        register_and_login(client, "taskuser6", "testpassword123")
        proj_id = create_project_for(client, "Project T6")
        create_res = client.post(f"/api/projects/{proj_id}/tasks",
                                 data=json.dumps({"title": "Move me", "status": "todo", "priority": "medium"}),
                                 content_type="application/json")
        task_id = create_res.get_json()["data"]["id"]
        res = client.put(f"/api/projects/{proj_id}/tasks/{task_id}",
                         data=json.dumps({"status": "doing"}),
                         content_type="application/json")
        assert res.status_code == 200
        assert res.get_json()["data"]["status"] == "doing"

    def test_delete_task(self, client):
        register_and_login(client, "taskuser7", "testpassword123")
        proj_id = create_project_for(client, "Project T7")
        create_res = client.post(f"/api/projects/{proj_id}/tasks",
                                 data=json.dumps({"title": "Delete me", "status": "todo", "priority": "low"}),
                                 content_type="application/json")
        task_id = create_res.get_json()["data"]["id"]
        res = client.delete(f"/api/projects/{proj_id}/tasks/{task_id}")
        assert res.status_code == 200
        assert res.get_json()["data"]["deleted_id"] == task_id

        # Verify gone
        res2 = client.get(f"/api/projects/{proj_id}/tasks/{task_id}")
        assert res2.status_code == 404

    def test_invalid_due_date_format(self, client):
        register_and_login(client, "taskuser8", "testpassword123")
        proj_id = create_project_for(client, "Project T8")
        res = client.post(f"/api/projects/{proj_id}/tasks",
                          data=json.dumps({"title": "Bad date", "status": "todo",
                                           "priority": "low", "due_date": "not-a-date"}),
                          content_type="application/json")
        assert res.status_code == 400

    def test_task_not_found(self, client):
        register_and_login(client, "taskuser9", "testpassword123")
        proj_id = create_project_for(client, "Project T9")
        res = client.get(f"/api/projects/{proj_id}/tasks/99999")
        assert res.status_code == 404
