from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from .database import Base, engine
from .exceptions import ConflictError, NotFoundError
from .schemas import Author, AuthorCreate, AuthorUpdate, Book, BookCreate, BookUpdate
from .storage import (
    create_author,
    create_book,
    delete_author,
    delete_book,
    get_all_authors,
    get_all_books,
    get_author_by_id,
    get_book_by_id,
    seed_books,
    update_author,
    update_book,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if os.getenv("TESTING", "false").lower() != "true":
        seed_books()
    yield


app = FastAPI(
    title="Library API",
    description="REST API для управления книгами и авторами в библиотеке",
    version="1.1.0",
    lifespan=lifespan,
)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.detail})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": exc.detail})


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Library API", "version": "1.1.0", "docs": "/docs"}




@app.get("/authors", response_model=list[Author])
def get_authors() -> list[Author]:
    return get_all_authors()


@app.get("/authors/{author_id}", response_model=Author)
def get_author(author_id: int) -> Author:
    return get_author_by_id(author_id)


@app.post("/authors", response_model=Author, status_code=status.HTTP_201_CREATED)
def post_author(author_data: AuthorCreate) -> Author:
    return create_author(author_data)


@app.put("/authors/{author_id}", response_model=Author)
def put_author(author_id: int, author_data: AuthorUpdate) -> Author:
    return update_author(author_id, author_data)


@app.delete("/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_author(author_id: int) -> None:
    delete_author(author_id)




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
