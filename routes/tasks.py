from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from schemas.task import TaskCreate, TaskUpdate, TaskOut
from services import task_service
from core.dependencies import get_db, get_current_user
from models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
def get_tasks(
    task_status: Optional[str] = None,
    category: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from repositories.task_repo import get_all_paginated
    skip = (page - 1) * limit
    items, total = get_all_paginated(db, current_user.id, status=task_status, category=category, skip=skip, limit=limit)
    pages = max(1, -(-total // limit))
    return {"items": [TaskOut.model_validate(t) for t in items], "total": total, "page": page, "pages": pages}


@router.get("/active-timers")
def get_active_timers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from services import time_log_service
    return {"active_task_ids": time_log_service.get_active_timers(db, current_user.id)}


@router.get("/overdue", response_model=list[TaskOut])
def get_overdue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Власна пропозиція: прострочені незавершені задачі
    return task_service.get_overdue_tasks(db, current_user.id)


@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.create_task(db, current_user.id, data)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.get_task(db, task_id, current_user.id)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.update_task(db, task_id, current_user.id, data)


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_service.delete_task(db, task_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{task_id}/complete", response_model=TaskOut)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return task_service.complete_task(db, task_id, current_user.id)
