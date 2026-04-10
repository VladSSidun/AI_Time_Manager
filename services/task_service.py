from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from repositories import task_repo
from schemas.task import TaskCreate, TaskUpdate
from models.task import Task


def _get_owned_task(db: Session, task_id: int, user_id: int) -> Task:
    task = task_repo.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задачу не знайдено")
    if task.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Немає доступу до цієї задачі")
    return task


def get_tasks(db: Session, user_id: int, status: str | None = None, category: str | None = None) -> list[Task]:
    return task_repo.get_all(db, user_id, status=status, category=category)


def get_task(db: Session, task_id: int, user_id: int) -> Task:
    return _get_owned_task(db, task_id, user_id)


def create_task(db: Session, user_id: int, data: TaskCreate) -> Task:
    return task_repo.create(db, user_id=user_id, **data.model_dump())


def update_task(db: Session, task_id: int, user_id: int, data: TaskUpdate) -> Task:
    task = _get_owned_task(db, task_id, user_id)
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    return task_repo.update(db, task, **updates)


def delete_task(db: Session, task_id: int, user_id: int) -> None:
    task = _get_owned_task(db, task_id, user_id)
    task_repo.delete(db, task)


def complete_task(db: Session, task_id: int, user_id: int) -> Task:
    task = _get_owned_task(db, task_id, user_id)
    if task.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Задача вже завершена")
    return task_repo.mark_completed(db, task)


def get_overdue_tasks(db: Session, user_id: int) -> list[Task]:
    # Власна пропозиція: прострочені незавершені задачі
    return task_repo.get_overdue(db, user_id)
