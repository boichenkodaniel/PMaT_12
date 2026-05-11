from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, overload

from pydantic import BaseModel, ConfigDict, Field, field_validator


@overload
def _validate_isbn_value(value: str) -> str: ...
@overload
def _validate_isbn_value(value: Optional[str]) -> Optional[str]: ...
def _validate_isbn_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    cleaned = value.replace("-", "").replace(" ", "")
    if not re.fullmatch(r"\d+", cleaned):
        raise ValueError("ISBN должен содержать только цифры и дефисы")
    if len(cleaned) not in (10, 13):
        raise ValueError("ISBN должен содержать 10 или 13 цифр")
    return value


@overload
def _validate_published_year_value(value: int) -> int: ...
@overload
def _validate_published_year_value(value: Optional[int]) -> Optional[int]: ...
def _validate_published_year_value(value: Optional[int]) -> Optional[int]:
    if value is None:
        return value
    current_year = datetime.now().year
    if value > current_year:
        raise ValueError(f"Год издания не может быть больше текущего ({current_year})")
    return value


class AuthorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    bio: Optional[str] = Field(default=None)


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    bio: Optional[str] = None


class Author(AuthorBase):
    id: int = Field(...)
    created_at: datetime = Field(...)

    model_config = ConfigDict(from_attributes=True)


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    isbn: str = Field(..., min_length=1, max_length=20)
    published_year: int = Field(..., ge=1450, le=9999)
    is_available: bool = Field(default=True)

    @field_validator("isbn")
    @classmethod
    def _validate_isbn(cls, value: str) -> str:
        return _validate_isbn_value(value)

    @field_validator("published_year")
    @classmethod
    def _validate_published_year(cls, value: int) -> int:
        return _validate_published_year_value(value)


class BookCreate(BookBase):
    author_id: int = Field(..., ge=1)


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    isbn: Optional[str] = Field(default=None, min_length=1, max_length=20)
    published_year: Optional[int] = Field(default=None, ge=1450, le=9999)
    is_available: Optional[bool] = None
    author_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("isbn")
    @classmethod
    def _validate_isbn(cls, value: Optional[str]) -> Optional[str]:
        return _validate_isbn_value(value)

    @field_validator("published_year")
    @classmethod
    def _validate_published_year(cls, value: Optional[int]) -> Optional[int]:
        return _validate_published_year_value(value)


class Book(BookBase):
    id: int = Field(...)
    author_id: int = Field(...)

    model_config = ConfigDict(from_attributes=True)