from __future__ import annotations

from fastapi import FastAPI, status

from .schemas import Book, BookCreate, BookUpdate
from .storage import create_book, delete_book, get_all_books, get_book_by_id, seed_books, update_book

app = FastAPI(
    title="Library API",
    description="REST API для управления книгами в библиотеке",
    version="1.0.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Library API", "version": "1.0.0", "docs": "/docs"}


@app.get("/books", response_model=list[Book])
def get_books() -> list[Book]:
    return get_all_books()


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int) -> Book:
    return get_book_by_id(book_id)


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def post_book(book_data: BookCreate) -> Book:
    return create_book(book_data)


@app.put("/books/{book_id}", response_model=Book)
def put_book(book_id: int, book_data: BookUpdate) -> Book:
    return update_book(book_id, book_data)


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_book(book_id: int) -> None:
    delete_book(book_id)


seed_books()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
