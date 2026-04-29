"""Тести таймера: старт, стоп, ручний запис, Pomodoro."""
import pytest
from datetime import datetime, timedelta
from tests.conftest import register_user, auth_headers


def create_task(client, headers, title="Task"):
    resp = client.post("/tasks", json={"title": title, "category": "work"}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


class TestStartTimer:
    def test_success(self, client, headers):
        tid = create_task(client, headers)
        resp = client.post(f"/tasks/{tid}/timer/start", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == tid
        assert data["started_at"] is not None
        assert data["ended_at"] is None
        assert data["duration_seconds"] is None

    def test_duplicate_start_fails(self, client, headers):
        tid = create_task(client, headers)
        client.post(f"/tasks/{tid}/timer/start", headers=headers)
        resp = client.post(f"/tasks/{tid}/timer/start", headers=headers)
        assert resp.status_code == 400

    def test_nonexistent_task(self, client, headers):
        resp = client.post("/tasks/9999/timer/start", headers=headers)
        assert resp.status_code == 404

    def test_other_user_task(self, client):
        t1 = register_user(client, email="t1@test.com")
        t2 = register_user(client, email="t2@test.com")
        tid = create_task(client, auth_headers(t1))
        resp = client.post(f"/tasks/{tid}/timer/start", headers=auth_headers(t2))
        assert resp.status_code == 404

    def test_pomodoro_flag(self, client, headers):
        tid = create_task(client, headers)
        resp = client.post(f"/tasks/{tid}/timer/start?pomodoro=true", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["is_pomodoro"] is True


class TestStopTimer:
    def test_success(self, client, headers):
        tid = create_task(client, headers)
        client.post(f"/tasks/{tid}/timer/start", headers=headers)

        import time; time.sleep(0.05)  # мінімальна затримка щоб duration > 0

        resp = client.post(f"/tasks/{tid}/timer/stop", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ended_at"] is not None
        assert data["duration_seconds"] is not None
        assert data["duration_seconds"] >= 0

    def test_stop_without_start(self, client, headers):
        tid = create_task(client, headers)
        resp = client.post(f"/tasks/{tid}/timer/stop", headers=headers)
        assert resp.status_code == 400

    def test_stop_twice_fails(self, client, headers):
        tid = create_task(client, headers)
        client.post(f"/tasks/{tid}/timer/start", headers=headers)
        client.post(f"/tasks/{tid}/timer/stop", headers=headers)
        resp = client.post(f"/tasks/{tid}/timer/stop", headers=headers)
        assert resp.status_code == 400

    def test_independent_timers_per_task(self, client, headers):
        t1 = create_task(client, headers, "Task 1")
        t2 = create_task(client, headers, "Task 2")
        client.post(f"/tasks/{t1}/timer/start", headers=headers)
        client.post(f"/tasks/{t2}/timer/start", headers=headers)
        r1 = client.post(f"/tasks/{t1}/timer/stop", headers=headers)
        r2 = client.post(f"/tasks/{t2}/timer/stop", headers=headers)
        assert r1.status_code == 200
        assert r2.status_code == 200


class TestManualLog:
    def test_success(self, client, headers):
        tid = create_task(client, headers)
        started = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        ended = datetime.utcnow().isoformat()
        resp = client.post(f"/tasks/{tid}/timer/manual", json={
            "task_id": tid,
            "started_at": started,
            "ended_at": ended,
            "note": "Ручний запис",
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["duration_seconds"] == pytest.approx(3600, abs=5)
        assert data["note"] == "Ручний запис"

    def test_missing_ended_at(self, client, headers):
        tid = create_task(client, headers)
        resp = client.post(f"/tasks/{tid}/timer/manual", json={
            "task_id": tid,
            "started_at": datetime.utcnow().isoformat(),
        }, headers=headers)
        assert resp.status_code == 400

    def test_ended_before_started(self, client, headers):
        tid = create_task(client, headers)
        now = datetime.utcnow()
        resp = client.post(f"/tasks/{tid}/timer/manual", json={
            "task_id": tid,
            "started_at": now.isoformat(),
            "ended_at": (now - timedelta(minutes=5)).isoformat(),
        }, headers=headers)
        assert resp.status_code == 400

    def test_pomodoro_manual(self, client, headers):
        tid = create_task(client, headers)
        started = (datetime.utcnow() - timedelta(minutes=25)).isoformat()
        ended = datetime.utcnow().isoformat()
        resp = client.post(f"/tasks/{tid}/timer/manual", json={
            "task_id": tid,
            "started_at": started,
            "ended_at": ended,
            "is_pomodoro": True,
        }, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["is_pomodoro"] is True


class TestActiveTimers:
    def _make_task(self, client, headers):
        resp = client.post("/tasks", json={"title": "Timer task"}, headers=headers)
        return resp.json()["id"]

    def test_no_active_timers_initially(self, client, headers):
        resp = client.get("/tasks/active-timers", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["active_task_ids"] == []

    def test_active_timer_appears_after_start(self, client, headers):
        tid = self._make_task(client, headers)
        client.post(f"/tasks/{tid}/timer/start", headers=headers)
        resp = client.get("/tasks/active-timers", headers=headers)
        assert tid in resp.json()["active_task_ids"]

    def test_timer_removed_after_stop(self, client, headers):
        tid = self._make_task(client, headers)
        client.post(f"/tasks/{tid}/timer/start", headers=headers)
        client.post(f"/tasks/{tid}/timer/stop", headers=headers)
        resp = client.get("/tasks/active-timers", headers=headers)
        assert tid not in resp.json()["active_task_ids"]

    def test_isolation_between_users(self, client):
        from tests.conftest import register_user, auth_headers
        t1 = register_user(client, email="at1@test.com")
        t2 = register_user(client, email="at2@test.com")
        task = client.post("/tasks", json={"title": "T"}, headers=auth_headers(t1)).json()
        client.post(f"/tasks/{task['id']}/timer/start", headers=auth_headers(t1))
        # user2 бачить порожній список
        resp = client.get("/tasks/active-timers", headers=auth_headers(t2))
        assert resp.json()["active_task_ids"] == []

    def test_requires_auth(self, client):
        assert client.get("/tasks/active-timers").status_code in (401, 403)
