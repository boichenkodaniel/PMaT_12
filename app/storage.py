from fastapi import HTTPException, status

from .schemas import Book, BookCreate, BookUpdate

_books_db: list[Book] = []
_next_id: int = 1


def _find_book_index(book_id: int) -> int:
    for idx, book in enumerate(_books_db):
        if book.id == book_id:
            return idx
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Книга с id={book_id} не найдена",
    )


def get_all_books() -> list[Book]:
    return _books_db


def get_book_by_id(book_id: int) -> Book:
    idx = _find_book_index(book_id)
    return _books_db[idx]


def create_book(book_data: BookCreate) -> Book:
    global _next_id
    new_book = Book(id=_next_id, **book_data.model_dump())
    _books_db.append(new_book)
    _next_id += 1
    return new_book


def update_book(book_id: int, book_data: BookUpdate) -> Book:
    idx = _find_book_index(book_id)
    existing_book = _books_db[idx]

    update_fields = book_data.model_dump(exclude_unset=True)
    merged_data = existing_book.model_dump()
    merged_data.update(update_fields)

    updated_book = Book(**merged_data)
    _books_db[idx] = updated_book
    return updated_book


def delete_book(book_id: int) -> None:
    idx = _find_book_index(book_id)
    _books_db.pop(idx)


def clear_storage() -> None:
    global _next_id
    _books_db.clear()
    _next_id = 1


def seed_books() -> None:
    global _next_id
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
        _books_db.append(Book(id=_next_id, **data.model_dump()))
        _next_id += 1
