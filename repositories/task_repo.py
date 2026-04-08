from datetime import datetime
from sqlalchemy.orm import Session
from models.task import Task


def get_all(
    db: Session,
    user_id: int,
    status: str | None = None,
    category: str | None = None,
) -> list[Task]:
    query = db.query(Task).filter(Task.user_id == user_id)
    if status:
        query = query.filter(Task.status == status)
    if category:
        query = query.filter(Task.category == category)
    return query.order_by(Task.created_at.desc()).all()


def get_all_paginated(
    db: Session,
    user_id: int,
    status: str | None = None,
    category: str | None = None,
    skip: int = 0,
    limit: int = 10,
) -> tuple[list[Task], int]:
    query = db.query(Task).filter(Task.user_id == user_id)
    if status:
        query = query.filter(Task.status == status)
    if category:
        query = query.filter(Task.category == category)
    total = query.count()
    items = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_by_id(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def create(db: Session, user_id: int, **kwargs) -> Task:
    task = Task(user_id=user_id, **kwargs)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update(db: Session, task: Task, **kwargs) -> Task:
    for key, value in kwargs.items():
        if value is not None:
            setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def delete(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()


def mark_completed(db: Session, task: Task) -> Task:
    task.status = "completed"
    task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


def get_overdue(db: Session, user_id: int) -> list[Task]:
    # Власна пропозиція: вибірка прострочених незавершених задач
    now = datetime.utcnow()
    return (
        db.query(Task)
        .filter(
            Task.user_id == user_id,
            Task.status == "pending",
            Task.deadline < now,
            Task.deadline.isnot(None),
        )
        .order_by(Task.deadline.asc())
        .all()
    )
