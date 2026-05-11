from __future__ import annotations

import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url is None:
        raise RuntimeError(
            "DATABASE_URL environment variable is required. "
            "Example: postgresql+psycopg://user:password@host:5432/dbname"
        )
    return url


engine = create_engine(
    _get_database_url(),
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=10,
    max_overflow=20,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()