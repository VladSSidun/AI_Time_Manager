import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    is_admin: bool = False
    created_at: datetime


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    is_admin: bool
    created_at: datetime
    task_count: int = 0


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserUpdateName(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 50:
            raise ValueError("Ім'я має містити від 2 до 50 символів")
        if not re.match(r"^[\w\s'\-а-яА-ЯіІїЇєЄёЁ]+$", v, re.UNICODE):
            raise ValueError("Ім'я містить неприпустимі символи")
        return v
