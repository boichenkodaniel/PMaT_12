from __future__ import annotations

from sqlalchemy import Boolean, Column, Integer, String

from .database import Base


class BookModel(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    author = Column(String(200), nullable=False)
    isbn = Column(String(20), nullable=False, unique=True)
    published_year = Column(Integer, nullable=False)
    is_available = Column(Boolean, default=True)
