from __future__ import annotations

import logging
from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import SessionLocal
from .exceptions import ConflictError, NotFoundError
from .models import AuthorModel, BookModel
from .schemas import Author, AuthorCreate, AuthorUpdate, Book, BookCreate, BookUpdate

logger = logging.getLogger(__name__)


@contextmanager
def _db_session():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        logger.error("Database transaction failed")
        raise
    finally:
        db.close()


# ── Authors ──────────────────────────────────────────────────────────


def _author_model_to_schema(author: AuthorModel) -> Author:
    return Author(
        id=author.id,
        name=author.name,
        bio=author.bio,
        created_at=author.created_at,
    )


def get_all_authors() -> list[Author]:
    with _db_session() as db:
        authors = db.query(AuthorModel).all()
        return [_author_model_to_schema(a) for a in authors]


def get_author_by_id(author_id: int) -> Author:
    with _db_session() as db:
        author = db.query(AuthorModel).filter(AuthorModel.id == author_id).first()
        if author is None:
            logger.warning(f"Author not found: id={author_id}")
            raise NotFoundError(f"Автор с id={author_id} не найден")
        return _author_model_to_schema(author)


def create_author(data: AuthorCreate) -> Author:
    with _db_session() as db:
        author = AuthorModel(**data.model_dump())
        db.add(author)
        try:
            db.commit()
            logger.info(f"Author created: id={author.id}, name={author.name}")
        except IntegrityError:
            logger.warning(f"Duplicate author name: {data.name}")
            raise ConflictError(f"Автор с именем '{data.name}' уже существует")
        db.refresh(author)
        return _author_model_to_schema(author)


def update_author(author_id: int, data: AuthorUpdate) -> Author:
    with _db_session() as db:
        author = db.query(AuthorModel).filter(AuthorModel.id == author_id).first()
        if author is None:
            logger.warning(f"Author not found for update: id={author_id}")
            raise NotFoundError(f"Автор с id={author_id} не найден")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(author, field, value)

        db.commit()
        logger.info(f"Author updated: id={author_id}")
        db.refresh(author)
        return _author_model_to_schema(author)


def delete_author(author_id: int) -> None:
    with _db_session() as db:
        author = db.query(AuthorModel).filter(AuthorModel.id == author_id).first()
        if author is None:
            logger.warning(f"Author not found for delete: id={author_id}")
            raise NotFoundError(f"Автор с id={author_id} не найден")
        if author.books:
            logger.warning(f"Cannot delete author with books: id={author_id}")
            raise ConflictError(f"Нельзя удалить автора с id={author_id}: у него есть книги")
        db.delete(author)
        db.commit()
        logger.info(f"Author deleted: id={author_id}")


# ── Books ────────────────────────────────────────────────────────────


def _book_model_to_schema(book: BookModel) -> Book:
    return Book(
        id=book.id,
        title=book.title,
        author_id=book.author_id,
        isbn=book.isbn,
        published_year=book.published_year,
        is_available=book.is_available,
    )


def get_all_books() -> list[Book]:
    with _db_session() as db:
        books = db.query(BookModel).all()
        return [_book_model_to_schema(b) for b in books]


def get_book_by_id(book_id: int) -> Book:
    with _db_session() as db:
        book = db.query(BookModel).filter(BookModel.id == book_id).first()
        if book is None:
            logger.warning(f"Book not found: id={book_id}")
            raise NotFoundError(f"Книга с id={book_id} не найдена")
        return _book_model_to_schema(book)


def create_book(book_data: BookCreate) -> Book:
    with _db_session() as db:
        author = db.query(AuthorModel).filter(AuthorModel.id == book_data.author_id).first()
        if author is None:
            logger.warning(f"Author not found for book: author_id={book_data.author_id}")
            raise NotFoundError(f"Автор с id={book_data.author_id} не найден")

        book = BookModel(**book_data.model_dump())
        db.add(book)
        try:
            db.commit()
            logger.info(f"Book created: id={book.id}, title={book.title}")
        except IntegrityError:
            logger.warning(f"Duplicate book ISBN: {book_data.isbn}")
            raise ConflictError(f"Книга с ISBN '{book_data.isbn}' уже существует")
        db.refresh(book)
        return _book_model_to_schema(book)


def update_book(book_id: int, book_data: BookUpdate) -> Book:
    with _db_session() as db:
        book = db.query(BookModel).filter(BookModel.id == book_id).first()
        if book is None:
            logger.warning(f"Book not found for update: id={book_id}")
            raise NotFoundError(f"Книга с id={book_id} не найдена")

        update_fields = book_data.model_dump(exclude_unset=True)

        if "author_id" in update_fields:
            new_author_id = update_fields["author_id"]
            author = db.query(AuthorModel).filter(AuthorModel.id == new_author_id).first()
            if author is None:
                logger.warning(f"New author not found: author_id={new_author_id}")
                raise NotFoundError(f"Автор с id={new_author_id} не найден")

        for field, value in update_fields.items():
            setattr(book, field, value)

        db.commit()
        logger.info(f"Book updated: id={book_id}")
        db.refresh(book)
        return _book_model_to_schema(book)


def delete_book(book_id: int) -> None:
    with _db_session() as db:
        book = db.query(BookModel).filter(BookModel.id == book_id).first()
        if book is None:
            logger.warning(f"Book not found for delete: id={book_id}")
            raise NotFoundError(f"Книга с id={book_id} не найдена")
        db.delete(book)
        db.commit()
        logger.info(f"Book deleted: id={book_id}")


def clear_storage() -> None:
    with _db_session() as db:
        db.query(BookModel).delete()
        db.query(AuthorModel).delete()
        db.commit()
        logger.info("Storage cleared")


def seed_books() -> None:
    with _db_session() as db:
        book_count = db.query(BookModel).count()
        if book_count > 0:
            return

        authors_data = [
            {"name": "Лев Толстой", "bio": "Русский писатель, автор «Войны и мира»."},
            {"name": "Джордж Оруэлл", "bio": "Английский писатель, автор «1984»."},
            {"name": "Фёдор Достоевский", "bio": "Русский писатель, автор «Преступления и наказания»."},
        ]
        authors = []
        for data in authors_data:
            author = AuthorModel(**data)
            db.add(author)
            authors.append(author)
        db.commit()

        books_data = [
            {
                "title": "Война и мир",
                "author_id": authors[0].id,
                "isbn": "978-5-699-12014-7",
                "published_year": 1869,
                "is_available": True,
            },
            {
                "title": "1984",
                "author_id": authors[1].id,
                "isbn": "978-0-452-28423-4",
                "published_year": 1949,
                "is_available": False,
            },
            {
                "title": "Преступление и наказание",
                "author_id": authors[2].id,
                "isbn": "978-5-17-090436-6",
                "published_year": 1866,
                "is_available": True,
            },
        ]
        for data in books_data:
            book = BookModel(**data)
            db.add(book)
        db.commit()
        logger.info("Seed data created")