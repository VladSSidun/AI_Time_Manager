from sqlalchemy import func
from sqlalchemy.orm import Session
from models.user import User
from models.task import Task


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_all_with_task_counts(
    db: Session,
    skip: int = 0,
    limit: int = 15,
) -> tuple[list[dict], int]:
    # Кількість задач на юзера — через outerjoin
    subq = (
        db.query(Task.user_id, func.count(Task.id).label("task_count"))
        .group_by(Task.user_id)
        .subquery()
    )
    query = (
        db.query(User, func.coalesce(subq.c.task_count, 0).label("task_count"))
        .outerjoin(subq, User.id == subq.c.user_id)
        .order_by(User.created_at.desc())
    )
    total = query.count()
    rows = query.offset(skip).limit(limit).all()
    result = []
    for user, task_count in rows:
        result.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "task_count": task_count,
        })
    return result, total


def update_name(db: Session, user: User, name: str) -> User:
    user.name = name
    db.commit()
    db.refresh(user)
    return user


def create(db: Session, name: str, email: str, hashed_password: str) -> User:
    user = User(name=name, email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
