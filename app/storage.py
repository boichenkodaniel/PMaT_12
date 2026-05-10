from __future__ import annotations

from fastapi import HTTPException, status

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import BookModel
from .schemas import Book, BookCreate, BookUpdate


def _get_db() -> Session:
    return SessionLocal()


def _book_model_to_schema(book: BookModel) -> Book:
    return Book(
        id=book.id,
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        published_year=book.published_year,
        is_available=book.is_available,
    )


def get_all_books() -> list[Book]:
    db = _get_db()
    books = db.query(BookModel).all()
    db.close()
    return [_book_model_to_schema(b) for b in books]


def get_book_by_id(book_id: int) -> Book:
    db = _get_db()
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    db.close()
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с id={book_id} не найдена",
        )
    return _book_model_to_schema(book)


def create_book(book_data: BookCreate) -> Book:
    db = _get_db()
    book = BookModel(**book_data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    db.close()
    return _book_model_to_schema(book)


def update_book(book_id: int, book_data: BookUpdate) -> Book:
    db = _get_db()
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if book is None:
        db.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с id={book_id} не найдена",
        )

    update_fields = book_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)
    db.close()
    return _book_model_to_schema(book)


def delete_book(book_id: int) -> None:
    db = _get_db()
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if book is None:
        db.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с id={book_id} не найдена",
        )
    db.delete(book)
    db.commit()
    db.close()


def clear_storage() -> None:
    db = _get_db()
    db.query(BookModel).delete()
    db.commit()
    db.close()


def seed_books() -> None:
    db = _get_db()
    count = db.query(BookModel).count()
    if count > 0:
        db.close()
        return

    samples = [
        BookCreate(
            title="Война и мир",
            author="Лев Толстой",
            isbn="978-5-699-12014-7",
            published_year=1869,
            is_available=True,
        ),
        BookCreate(
            title="1984",
            author="Джордж Оруэлл",
            isbn="978-0-452-28423-4",
            published_year=1949,
            is_available=False,
        ),
        BookCreate(
            title="Преступление и наказание",
            author="Фёдор Достоевский",
            isbn="978-5-17-090436-6",
            published_year=1866,
            is_available=True,
        ),
    ]
    for data in samples:
        book = BookModel(**data.model_dump())
        db.add(book)
    db.commit()
    db.close()