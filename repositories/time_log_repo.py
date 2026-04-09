from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.time_log import TimeLog


def create(
    db: Session,
    task_id: int,
    user_id: int,
    started_at: datetime,
    is_pomodoro: bool = False,
) -> TimeLog:
    log = TimeLog(
        task_id=task_id,
        user_id=user_id,
        started_at=started_at,
        is_pomodoro=is_pomodoro,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_active(db: Session, task_id: int, user_id: int) -> TimeLog | None:
    # ended_at IS NULL означає що таймер ще запущений
    return (
        db.query(TimeLog)
        .filter(
            TimeLog.task_id == task_id,
            TimeLog.user_id == user_id,
            TimeLog.ended_at.is_(None),
        )
        .first()
    )


def stop(db: Session, log: TimeLog) -> TimeLog:
    log.ended_at = datetime.utcnow()
    log.duration_seconds = int((log.ended_at - log.started_at).total_seconds())
    db.commit()
    db.refresh(log)
    return log


def get_all_active(db: Session, user_id: int) -> list[TimeLog]:
    return (
        db.query(TimeLog)
        .filter(TimeLog.user_id == user_id, TimeLog.ended_at.is_(None))
        .all()
    )


def get_last_n_days(db: Session, user_id: int, days: int = 30) -> list[TimeLog]:
    since = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(TimeLog)
        .filter(
            TimeLog.user_id == user_id,
            TimeLog.started_at >= since,
            TimeLog.ended_at.isnot(None),  # лише завершені сесії
        )
        .order_by(TimeLog.started_at.desc())
        .all()
    )


def create_manual(
    db: Session,
    task_id: int,
    user_id: int,
    started_at: datetime,
    ended_at: datetime,
    note: str | None = None,
    is_pomodoro: bool = False,
) -> TimeLog:
    duration = int((ended_at - started_at).total_seconds())
    log = TimeLog(
        task_id=task_id,
        user_id=user_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        note=note,
        is_pomodoro=is_pomodoro,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
