from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from schemas.time_log import TimeLogCreate, TimeLogOut
from services import time_log_service
from core.dependencies import get_db, get_current_user
from models.user import User

router = APIRouter(prefix="/tasks", tags=["timer"])


@router.post("/{task_id}/timer/start", response_model=TimeLogOut)
def start_timer(
    task_id: int,
    pomodoro: bool = Query(default=False, description="Запустити в режимі Pomodoro"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return time_log_service.start_timer(db, task_id, current_user.id, is_pomodoro=pomodoro)


@router.post("/{task_id}/timer/stop", response_model=TimeLogOut)
def stop_timer(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return time_log_service.stop_timer(db, task_id, current_user.id)


@router.post("/{task_id}/timer/manual", response_model=TimeLogOut, status_code=201)
def manual_log(
    task_id: int,
    data: TimeLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return time_log_service.add_manual_log(db, current_user.id, data)
