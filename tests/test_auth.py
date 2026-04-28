"""Тести авторизації: реєстрація та вхід."""
import pytest
from tests.conftest import register_user, auth_headers


class TestRegister:
    def test_success(self, client):
        resp = client.post("/auth/register", json={
            "name": "Влад", "email": "vlad@test.com", "password": "secret123"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 10

    def test_duplicate_email(self, client):
        client.post("/auth/register", json={
            "name": "А", "email": "dup@test.com", "password": "pass"
        })
        resp = client.post("/auth/register", json={
            "name": "Б", "email": "dup@test.com", "password": "pass"
        })
        assert resp.status_code == 400
        assert "Email" in resp.json()["detail"]

    def test_invalid_email_format(self, client):
        resp = client.post("/auth/register", json={
            "name": "Х", "email": "не_email", "password": "pass"
        })
        assert resp.status_code == 422

    def test_missing_fields(self, client):
        resp = client.post("/auth/register", json={"name": "Х"})
        assert resp.status_code == 422


class TestLogin:
    def test_success(self, client):
        client.post("/auth/register", json={
            "name": "User", "email": "u@test.com", "password": "mypass"
        })
        resp = client.post("/auth/login", json={
            "email": "u@test.com", "password": "mypass"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_wrong_password(self, client):
        client.post("/auth/register", json={
            "name": "U", "email": "u2@test.com", "password": "correct"
        })
        resp = client.post("/auth/login", json={
            "email": "u2@test.com", "password": "wrong"
        })
        assert resp.status_code == 401

    def test_unknown_email(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@test.com", "password": "pass"
        })
        assert resp.status_code == 401

    def test_protected_endpoint_without_token(self, client):
        resp = client.get("/tasks")
        assert resp.status_code in (401, 403)  # HTTPBearer залежно від версії Starlette

    def test_protected_endpoint_with_bad_token(self, client):
        resp = client.get("/tasks", headers={"Authorization": "Bearer bad.token.here"})
        assert resp.status_code == 401


class TestUpdateName:
    def test_success(self, client, headers):
        resp = client.patch("/auth/me", json={"name": "Нове Ім'я"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Нове Ім'я"

    def test_name_too_short(self, client, headers):
        resp = client.patch("/auth/me", json={"name": "А"}, headers=headers)
        assert resp.status_code == 422

    def test_name_too_long(self, client, headers):
        resp = client.patch("/auth/me", json={"name": "А" * 51}, headers=headers)
        assert resp.status_code == 422

    def test_name_strips_whitespace(self, client, headers):
        resp = client.patch("/auth/me", json={"name": "  Влад  "}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Влад"

    def test_requires_auth(self, client):
        resp = client.patch("/auth/me", json={"name": "NoAuth"})
        assert resp.status_code in (401, 403)

    def test_get_me_returns_updated_name(self, client, headers):
        client.patch("/auth/me", json={"name": "Оновлений"}, headers=headers)
        resp = client.get("/auth/me", headers=headers)
        assert resp.json()["name"] == "Оновлений"
