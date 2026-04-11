from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from repositories import time_log_repo, task_repo
from schemas.time_log import TimeLogCreate
from models.time_log import TimeLog

POMODORO_MINUTES = 25  # стандартна тривалість Pomodoro-сесії


def start_timer(db: Session, task_id: int, user_id: int, is_pomodoro: bool = False) -> TimeLog:
    task = task_repo.get_by_id(db, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задачу не знайдено")

    if time_log_repo.get_active(db, task_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Таймер вже запущено для цієї задачі",
        )

    return time_log_repo.create(
        db,
        task_id=task_id,
        user_id=user_id,
        started_at=datetime.utcnow(),
        is_pomodoro=is_pomodoro,
    )


def stop_timer(db: Session, task_id: int, user_id: int) -> TimeLog:
    log = time_log_repo.get_active(db, task_id, user_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Немає активного таймера для цієї задачі",
        )
    return time_log_repo.stop(db, log)


def get_active_timers(db: Session, user_id: int) -> list[int]:
    logs = time_log_repo.get_all_active(db, user_id)
    return [log.task_id for log in logs]


def add_manual_log(db: Session, user_id: int, data: TimeLogCreate) -> TimeLog:
    task = task_repo.get_by_id(db, data.task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задачу не знайдено")

    if not data.ended_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для ручного запису потрібно вказати ended_at",
        )
    if data.ended_at <= data.started_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ended_at має бути після started_at",
        )

    return time_log_repo.create_manual(
        db,
        task_id=data.task_id,
        user_id=user_id,
        started_at=data.started_at,
        ended_at=data.ended_at,
        note=data.note,
        is_pomodoro=data.is_pomodoro,
    )
