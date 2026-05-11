from __future__ import annotations

import os

os.environ["TESTING"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_engine):
    with TestClient(app) as c:
        yield c
    db = SessionLocal()
    db.execute(text("TRUNCATE TABLE books, authors RESTART IDENTITY CASCADE"))
    db.commit()
    db.close()