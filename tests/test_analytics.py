"""Тести аналітики: статистика, AI-аналіз (з mock), експорт."""
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from tests.conftest import register_user, auth_headers


def create_task_and_log(client, headers, minutes_ago=60, category="work"):
    """Створює задачу і додає ручний time log."""
    task = client.post("/tasks", json={"title": "T", "category": category}, headers=headers).json()
    tid = task["id"]
    ended = datetime.utcnow()
    started = ended - timedelta(minutes=minutes_ago)
    client.post(f"/tasks/{tid}/timer/manual", json={
        "task_id": tid,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
    }, headers=headers)
    return tid


class TestStats:
    def test_empty_stats(self, client, headers):
        resp = client.get("/analytics/stats", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 0
        assert data["total_hours"] == 0
        assert data["productivity_score"] == 0

    def test_stats_with_sessions(self, client, headers):
        create_task_and_log(client, headers, minutes_ago=30, category="work")
        create_task_and_log(client, headers, minutes_ago=45, category="study")

        resp = client.get("/analytics/stats", headers=headers)
        data = resp.json()
        assert data["total_sessions"] == 2
        assert data["total_hours"] > 0
        assert data["avg_session_min"] > 0
        assert data["top_category"] in ("work", "study")

    def test_stats_isolation_between_users(self, client):
        t1 = register_user(client, email="s1@test.com")
        t2 = register_user(client, email="s2@test.com")
        create_task_and_log(client, auth_headers(t1))
        resp = client.get("/analytics/stats", headers=auth_headers(t2))
        assert resp.json()["total_sessions"] == 0

    def test_stats_custom_days_param(self, client, headers):
        create_task_and_log(client, headers)
        resp = client.get("/analytics/stats?days=7", headers=headers)
        assert resp.status_code == 200

    def test_productivity_score_in_range(self, client, headers):
        create_task_and_log(client, headers)
        data = client.get("/analytics/stats", headers=headers).json()
        assert 0 <= data["productivity_score"] <= 100

    def test_pomodoro_count_in_stats(self, client, headers):
        task = client.post("/tasks", json={"title": "P"}, headers=headers).json()
        tid = task["id"]
        ended = datetime.utcnow()
        started = ended - timedelta(minutes=25)
        client.post(f"/tasks/{tid}/timer/manual", json={
            "task_id": tid,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "is_pomodoro": True,
        }, headers=headers)
        data = client.get("/analytics/stats", headers=headers).json()
        assert data["pomodoro_sessions"] == 1

    def test_requires_auth(self, client):
        assert client.get("/analytics/stats").status_code in (401, 403)


class TestAIAnalysis:
    def _mock_anthropic(self):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="1. Рада перша.\n2. Рада друга.")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg
        return mock_client

    def test_ai_analysis_success(self, client, headers):
        create_task_and_log(client, headers)
        with patch("services.ai_service.anthropic.Anthropic", return_value=self._mock_anthropic()):
            resp = client.post("/analytics/ai-analysis", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendation" in data
        assert "Рада" in data["recommendation"]
        assert "stats_snapshot" in data
        assert data["user_id"] > 0

    def test_stats_snapshot_is_valid_json(self, client, headers):
        create_task_and_log(client, headers)
        with patch("services.ai_service.anthropic.Anthropic", return_value=self._mock_anthropic()):
            resp = client.post("/analytics/ai-analysis", headers=headers)
        snapshot = resp.json()["stats_snapshot"]
        parsed = json.loads(snapshot)
        assert "total_sessions" in parsed

    def test_ai_history_empty(self, client, headers):
        resp = client.get("/analytics/ai-analysis", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_ai_history_populated(self, client, headers):
        create_task_and_log(client, headers)
        with patch("services.ai_service.anthropic.Anthropic", return_value=self._mock_anthropic()):
            client.post("/analytics/ai-analysis", headers=headers)
            client.post("/analytics/ai-analysis", headers=headers)
        history = client.get("/analytics/ai-analysis", headers=headers).json()
        assert len(history) == 2
        # Новіші — першими
        assert history[0]["id"] > history[1]["id"]

    def test_ai_requires_auth(self, client):
        assert client.post("/analytics/ai-analysis").status_code in (401, 403)


class TestExport:
    def test_export_json(self, client, headers):
        create_task_and_log(client, headers)
        resp = client.get("/analytics/export", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert "total_sessions" in data
        assert "productivity_score" in data

    def test_export_requires_auth(self, client):
        assert client.get("/analytics/export").status_code in (401, 403)

    def test_export_empty_stats(self, client, headers):
        # Без даних — всі поля мають бути нулями
        resp = client.get("/analytics/export", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 0
        assert data["total_hours"] == 0
        assert data["productivity_score"] == 0

    def test_export_json_structure(self, client, headers):
        create_task_and_log(client, headers)
        resp = client.get("/analytics/export", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        required_keys = [
            "total_sessions", "total_hours", "avg_session_min",
            "morning_pct", "afternoon_pct", "evening_pct",
            "best_day", "completion_rate", "overdue_pct",
            "top_category", "productivity_score", "pomodoro_sessions",
        ]
        for key in required_keys:
            assert key in data, f"Відсутній ключ: {key}"

    def test_export_utf8_content(self, client, headers):
        # Кирилиця в назві задачі — перевіряємо кодування
        task = client.post("/tasks", json={"title": "Тест кирилиці", "category": "study"}, headers=headers).json()
        ended = datetime.utcnow()
        started = ended - timedelta(minutes=20)
        client.post(f"/tasks/{task['id']}/timer/manual", json={
            "task_id": task["id"],
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
        }, headers=headers)

        resp = client.get("/analytics/export", headers=headers)
        assert resp.status_code == 200
        # Перевіряємо що відповідь є валідним JSON з кириличними рядками
        data = resp.json()
        assert data["top_category"] == "study"
        # Content-Disposition заголовок для завантаження
        content_disp = resp.headers.get("content-disposition", "")
        assert "attachment" in content_disp
