import os
from unittest.mock import patch

import pytest
from dotenv import load_dotenv
from starlette.testclient import TestClient

os.environ["TESTING"] = "True"

from settings import DATABASE_URL
from database import Base, SessionLocal, engine
from main import app

load_dotenv()


@pytest.fixture(scope="session")
def setup_db():
    """Создание Базы Данных для тестов."""
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        yield DATABASE_URL
    except Exception as error:
        print("clear test database ", error)
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def client(setup_db):
    """Создание тестового клиента"""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def db_session():
    """Создание сессии базы данных"""
    SessionLocal.configure(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_get_current_user():
    """Создание мок-объекта для get_current_user"""
    with patch("main.get_current_user") as mock:
        yield mock
