"""Тести адмін панелі: список користувачів, задачі, захист."""
import pytest
from tests.conftest import register_user, auth_headers


def make_admin(db_session, client) -> str:
    """Реєструє користувача та призначає йому is_admin=True прямо в БД."""
    token = register_user(client, email="admin@test.com", name="Admin")
    # Встановлюємо is_admin через пряме оновлення БД
    from models.user import User
    user = db_session.query(User).filter(User.email == "admin@test.com").first()
    user.is_admin = True
    db_session.commit()
    return token


class TestAdminAccess:
    def test_non_admin_gets_403(self, client, headers):
        resp = client.get("/admin/users", headers=headers)
        assert resp.status_code == 403

    def test_unauthenticated_gets_401_or_403(self, client):
        resp = client.get("/admin/users")
        assert resp.status_code in (401, 403)

    def test_admin_can_access(self, client, db_session):
        token = make_admin(db_session, client)
        resp = client.get("/admin/users", headers=auth_headers(token))
        assert resp.status_code == 200


class TestAdminUserList:
    def test_returns_all_users(self, client, db_session):
        token = make_admin(db_session, client)
        # Реєструємо ще 2 юзери
        register_user(client, email="u1@test.com")
        register_user(client, email="u2@test.com")
        resp = client.get("/admin/users", headers=auth_headers(token))
        data = resp.json()
        assert data["total"] >= 3  # admin + 2 users
        assert "items" in data
        assert "pages" in data

    def test_user_has_required_fields(self, client, db_session):
        token = make_admin(db_session, client)
        resp = client.get("/admin/users", headers=auth_headers(token))
        user = resp.json()["items"][0]
        for field in ("id", "name", "email", "is_admin", "created_at", "task_count"):
            assert field in user, f"Відсутнє поле: {field}"

    def test_task_count_correct(self, client, db_session):
        token = make_admin(db_session, client)
        user_token = register_user(client, email="worker@test.com")
        # Додаємо 2 задачі
        client.post("/tasks", json={"title": "T1"}, headers=auth_headers(user_token))
        client.post("/tasks", json={"title": "T2"}, headers=auth_headers(user_token))

        resp = client.get("/admin/users", headers=auth_headers(token))
        users = resp.json()["items"]
        worker = next((u for u in users if u["email"] == "worker@test.com"), None)
        assert worker is not None
        assert worker["task_count"] == 2

    def test_pagination_limit(self, client, db_session):
        token = make_admin(db_session, client)
        resp = client.get("/admin/users?page=1&limit=1", headers=auth_headers(token))
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["pages"] >= 1


class TestAdminUserTasks:
    def test_returns_user_tasks(self, client, db_session):
        admin_token = make_admin(db_session, client)
        user_token = register_user(client, email="taskuser@test.com")
        client.post("/tasks", json={"title": "Task A", "category": "work"}, headers=auth_headers(user_token))

        # Знаходимо ID юзера
        users = client.get("/admin/users", headers=auth_headers(admin_token)).json()["items"]
        user = next(u for u in users if u["email"] == "taskuser@test.com")

        resp = client.get(f"/admin/users/{user['id']}/tasks", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        tasks = resp.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Task A"

    def test_non_admin_cannot_see_user_tasks(self, client, headers, db_session):
        admin_token = make_admin(db_session, client)
        users = client.get("/admin/users", headers=auth_headers(admin_token)).json()["items"]
        user_id = users[0]["id"]
        resp = client.get(f"/admin/users/{user_id}/tasks", headers=headers)
        assert resp.status_code == 403
