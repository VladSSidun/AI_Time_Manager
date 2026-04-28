"""
Загальні фікстури для всіх тестів.
Використовує in-memory SQLite — кожен тест отримує чисту БД.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from core.dependencies import get_db
from main import app

# StaticPool гарантує що всі з'єднання до :memory: використовують один спільний стейт
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# --- Допоміжні функції ---

def register_user(client, name="Тест", email="test@test.com", password="password123"):
    resp = client.post("/auth/register", json={"name": name, "email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def token(client):
    return register_user(client)


@pytest.fixture
def headers(token):
    return auth_headers(token)
