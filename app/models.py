from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship

from .database import Base


class AuthorModel(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=text("now()"), nullable=False)

    books = relationship("BookModel", back_populates="author")


class BookModel(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("authors.id", ondelete="RESTRICT"), nullable=False, index=True)
    isbn = Column(String(20), nullable=False, unique=True)
    published_year = Column(Integer, nullable=False)
    is_available = Column(Boolean, default=True)

    author = relationship("AuthorModel", back_populates="books")