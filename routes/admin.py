from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from schemas.user import AdminUserOut
from schemas.task import TaskOut
from repositories import user_repo, task_repo
from core.dependencies import get_db, get_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=15, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin=Depends(get_admin_user),
):
    skip = (page - 1) * limit
    users, total = user_repo.get_all_with_task_counts(db, skip=skip, limit=limit)
    pages = max(1, -(-total // limit))
    return {"items": users, "total": total, "page": page, "pages": pages}


@router.get("/users/{user_id}/tasks", response_model=list[TaskOut])
def get_user_tasks(
    user_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_admin_user),
):
    return task_repo.get_all(db, user_id=user_id)
