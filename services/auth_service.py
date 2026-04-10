from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from repositories import user_repo
from core.security import hash_password, verify_password, create_token


def register(db: Session, name: str, email: str, password: str) -> dict:
    if user_repo.get_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email вже використовується",
        )
    hashed = hash_password(password)
    user = user_repo.create(db, name=name, email=email, hashed_password=hashed)
    token = create_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


def update_profile(db: Session, user_id: int, name: str):
    from models.user import User
    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувача не знайдено")
    return user_repo.update_name(db, user, name)


def login(db: Session, email: str, password: str) -> dict:
    user = user_repo.get_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний email або пароль",
        )
    token = create_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
