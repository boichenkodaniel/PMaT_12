from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, status

from .database import Base, engine
from .schemas import Book, BookCreate, BookUpdate
from .storage import create_book, delete_book, get_all_books, get_book_by_id, seed_books, update_book


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if os.getenv("TESTING", "false").lower() != "true":
        seed_books()
    yield


app = FastAPI(
    title="Library API",
    description="REST API для управления книгами в библиотеке",
    version="1.0.0",
    lifespan=lifespan,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)