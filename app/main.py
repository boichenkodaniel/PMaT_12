from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .database import engine
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

# Rate limiting (отключено в тестовом режиме)
_testing_mode = os.getenv("TESTING", "false").lower() == "true"
limiter = Limiter(key_func=get_remote_address, enabled=not _testing_mode)


def _get_client_host(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    if os.getenv("TESTING", "false").lower() != "true":
        seed_books()
    logger = logging.getLogger("security")
    logger.info("Application started")
    yield
    logger.info("Application stopped")


app = FastAPI(
    title="Library API",
    description="REST API для управления книгами и авторами в библиотеке",
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — явное разрешение только доверенных origins
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)

# Security-заголовки
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path not in ("/docs", "/redoc", "/openapi.json"):
        response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    logger = logging.getLogger("security")
    logger.warning(f"Not found: {exc.detail} from {_get_client_host(request)}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail}
    )


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    logger = logging.getLogger("security")
    logger.warning(f"Conflict: {exc.detail} from {_get_client_host(request)}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger = logging.getLogger("security")
    logger.error(f"Unhandled exception: {exc} from {_get_client_host(request)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"}
    )


@app.get("/")
@limiter.limit("10/minute")
def root(request: Request) -> dict[str, str]:
    return {"message": "Library API", "version": "1.1.0", "docs": "/docs"}


@app.get("/authors", response_model=list[Author])
@limiter.limit("30/minute")
def get_authors(request: Request) -> list[Author]:
    return get_all_authors()


@app.get("/authors/{author_id}", response_model=Author)
@limiter.limit("30/minute")
def get_author(request: Request, author_id: int) -> Author:
    return get_author_by_id(author_id)


@app.post("/authors", response_model=Author, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def post_author(request: Request, author_data: AuthorCreate) -> Author:
    logger = logging.getLogger("security")
    logger.info(f"Creating author by request from {_get_client_host(request)}")
    return create_author(author_data)


@app.put("/authors/{author_id}", response_model=Author)
@limiter.limit("10/minute")
def put_author(request: Request, author_id: int, author_data: AuthorUpdate) -> Author:
    return update_author(author_id, author_data)


@app.delete("/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def remove_author(request: Request, author_id: int) -> None:
    logger = logging.getLogger("security")
    logger.info(f"Deleting author id={author_id} from {_get_client_host(request)}")
    delete_author(author_id)


@app.get("/books", response_model=list[Book])
@limiter.limit("30/minute")
def get_books(request: Request) -> list[Book]:
    return get_all_books()


@app.get("/books/{book_id}", response_model=Book)
@limiter.limit("30/minute")
def get_book(request: Request, book_id: int) -> Book:
    return get_book_by_id(book_id)


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def post_book(request: Request, book_data: BookCreate) -> Book:
    logger = logging.getLogger("security")
    logger.info(f"Creating book by author_id={book_data.author_id} from {_get_client_host(request)}")
    return create_book(book_data)


@app.put("/books/{book_id}", response_model=Book)
@limiter.limit("10/minute")
def put_book(request: Request, book_id: int, book_data: BookUpdate) -> Book:
    return update_book(book_id, book_data)


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def remove_book(request: Request, book_id: int) -> None:
    logger = logging.getLogger("security")
    logger.info(f"Deleting book id={book_id} from {_get_client_host(request)}")
    delete_book(book_id)