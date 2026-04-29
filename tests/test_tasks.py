"""Тести CRUD задач, фільтрів та прострочених задач."""
import pytest
from datetime import datetime, timedelta
from tests.conftest import register_user, auth_headers


def make_task(client, headers, title="Задача", category="work", **extra):
    payload = {"title": title, "category": category, **extra}
    resp = client.post("/tasks", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestCreateTask:
    def test_success(self, client, headers):
        task = make_task(client, headers, title="Моя задача", category="study")
        assert task["title"] == "Моя задача"
        assert task["category"] == "study"
        assert task["status"] == "pending"
        assert task["id"] > 0

    def test_default_category_other(self, client, headers):
        resp = client.post("/tasks", json={"title": "Без категорії"}, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["category"] == "other"

    def test_with_deadline(self, client, headers):
        deadline = (datetime.utcnow() + timedelta(days=3)).isoformat()
        task = make_task(client, headers, deadline=deadline)
        assert task["deadline"] is not None

    def test_missing_title(self, client, headers):
        resp = client.post("/tasks", json={"category": "work"}, headers=headers)
        assert resp.status_code == 422

    def test_requires_auth(self, client):
        resp = client.post("/tasks", json={"title": "X"})
        assert resp.status_code in (401, 403)


class TestGetTasks:
    def test_empty_list(self, client, headers):
        resp = client.get("/tasks", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_returns_own_tasks(self, client, headers):
        make_task(client, headers, title="А")
        make_task(client, headers, title="Б")
        resp = client.get("/tasks", headers=headers)
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_isolation_between_users(self, client):
        t1 = register_user(client, email="u1@test.com")
        t2 = register_user(client, email="u2@test.com")
        client.post("/tasks", json={"title": "u1 task"}, headers=auth_headers(t1))
        resp = client.get("/tasks", headers=auth_headers(t2))
        assert resp.json()["items"] == []

    def test_filter_by_status(self, client, headers):
        t = make_task(client, headers, title="Т1")
        client.post(f"/tasks/{t['id']}/complete", headers=headers)
        make_task(client, headers, title="Т2")

        completed = client.get("/tasks?task_status=completed", headers=headers).json()["items"]
        pending = client.get("/tasks?task_status=pending", headers=headers).json()["items"]
        assert len(completed) == 1
        assert len(pending) == 1

    def test_filter_by_category(self, client, headers):
        make_task(client, headers, category="work")
        make_task(client, headers, category="study")
        resp = client.get("/tasks?category=work", headers=headers)
        data = resp.json()["items"]
        assert len(data) == 1
        assert data[0]["category"] == "work"

    def test_pagination_page_and_pages(self, client, headers):
        for i in range(12):
            make_task(client, headers, title=f"Задача {i}")
        resp = client.get("/tasks?page=1&limit=10", headers=headers)
        data = resp.json()
        assert data["total"] == 12
        assert data["pages"] == 2
        assert len(data["items"]) == 10

    def test_pagination_second_page(self, client, headers):
        for i in range(12):
            make_task(client, headers, title=f"Задача {i}")
        resp = client.get("/tasks?page=2&limit=10", headers=headers)
        data = resp.json()
        assert len(data["items"]) == 2


class TestGetTaskById:
    def test_success(self, client, headers):
        task = make_task(client, headers)
        resp = client.get(f"/tasks/{task['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == task["id"]

    def test_not_found(self, client, headers):
        resp = client.get("/tasks/9999", headers=headers)
        assert resp.status_code == 404

    def test_other_user_forbidden(self, client):
        t1 = register_user(client, email="o1@test.com")
        t2 = register_user(client, email="o2@test.com")
        task = make_task(client, auth_headers(t1))
        resp = client.get(f"/tasks/{task['id']}", headers=auth_headers(t2))
        assert resp.status_code == 403


class TestUpdateTask:
    def test_success(self, client, headers):
        task = make_task(client, headers, title="Старий")
        resp = client.put(f"/tasks/{task['id']}", json={"title": "Новий"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Новий"

    def test_partial_update(self, client, headers):
        task = make_task(client, headers, title="T", category="work")
        resp = client.put(f"/tasks/{task['id']}", json={"category": "study"}, headers=headers)
        assert resp.json()["category"] == "study"
        assert resp.json()["title"] == "T"

    def test_other_user_forbidden(self, client):
        t1 = register_user(client, email="p1@test.com")
        t2 = register_user(client, email="p2@test.com")
        task = make_task(client, auth_headers(t1))
        resp = client.put(f"/tasks/{task['id']}", json={"title": "Hack"}, headers=auth_headers(t2))
        assert resp.status_code == 403


class TestDeleteTask:
    def test_success(self, client, headers):
        task = make_task(client, headers)
        resp = client.delete(f"/tasks/{task['id']}", headers=headers)
        assert resp.status_code == 204
        assert client.get(f"/tasks/{task['id']}", headers=headers).status_code == 404

    def test_not_found(self, client, headers):
        resp = client.delete("/tasks/9999", headers=headers)
        assert resp.status_code == 404


class TestCompleteTask:
    def test_success(self, client, headers):
        task = make_task(client, headers)
        resp = client.post(f"/tasks/{task['id']}/complete", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_already_completed(self, client, headers):
        task = make_task(client, headers)
        client.post(f"/tasks/{task['id']}/complete", headers=headers)
        resp = client.post(f"/tasks/{task['id']}/complete", headers=headers)
        assert resp.status_code == 400


class TestOverdueTasks:
    def test_returns_overdue(self, client, headers):
        past = (datetime.utcnow() - timedelta(days=1)).isoformat()
        future = (datetime.utcnow() + timedelta(days=1)).isoformat()
        make_task(client, headers, title="Протермінована", deadline=past)
        make_task(client, headers, title="Актуальна", deadline=future)

        resp = client.get("/tasks/overdue", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Протермінована"

    def test_completed_not_in_overdue(self, client, headers):
        past = (datetime.utcnow() - timedelta(days=1)).isoformat()
        task = make_task(client, headers, deadline=past)
        client.post(f"/tasks/{task['id']}/complete", headers=headers)

        resp = client.get("/tasks/overdue", headers=headers)
        assert resp.json() == []
