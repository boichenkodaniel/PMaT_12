# Отчёт по аудиту безопасности FastAPI-приложения (Задание 7)

**Дата:** 2026-05-11  
**Проект:** Library API (FastAPI + SQLAlchemy + PostgreSQL)  
**Версия API:** 1.1.0

---

## 1. Резюме

Проведён комплексный аудит безопасности кодовой базы FastAPI-приложения для управления библиотекой. Проверены следующие категории уязвимостей:

- SQL-инъекции
- Path Traversal при работе с файлами
- Валидация входных данных
- Утечки конфиденциальной информации в логах
- Настройки CORS и заголовки безопасности

**Общий уровень риска:** 🟡 **Средний** — критических уязвимостей не обнаружено, но выявлен ряд проблем, требующих исправления.

---

## 2. Найденные уязвимости и риски

### 2.1. SQL-инъекции 🔴 КРИТИЧНО

#### Проблема №1: Прямая интерполяция в `op.execute()` миграции

**Файл:** `alembic/versions/002_create_authors_and_link_books.py`

```python
# ❌ ПЛОХО: Прямое выполнение SQL без параметров
op.execute(text("""
    INSERT INTO authors (name, bio)
    SELECT DISTINCT author, NULL FROM books
"""))
```

**Риск:** В данном конкретном случае риск минимален, так как данные берутся из существующей таблицы БД. Однако если бы в запросе использовались пользовательские данные, это могло бы привести к SQL-инъекции.

**Исправление:** Использовать параметризованные запросы для всех операций с пользовательскими данными.

---

#### Проблема №2: Потенциальная SQL-инъекция через `server_default`

**Файл:** `app/models.py`

```python
# ⚠️ ПРЕДУПРЕЖДЕНИЕ: Использование text() требует доверия к строке
created_at = Column(DateTime, server_default=text("now()"), nullable=False)
```

**Риск:** `text()` выполняет "сырой" SQL. Если строка формируется из пользовательского ввода — это уязвимость.

**Статус:** ✅ **Безопасно** в данном случае, так как `"now()"` — литерал, а не пользовательские данные.

---

### 2.2. Path Traversal 🟢 БЕЗОПАСНО

**Результат:** В коде **отсутствует** работа с файловой системой на основе пользовательского ввода. Нет эндпоинтов для загрузки/скачивания файлов, чтения конфигов и т.д.

**Рекомендация:** При добавлении функционала работы с файлами использовать:

```python
from pathlib import Path
import os

ALLOWED_DIR = Path("/app/uploads").resolve()

def safe_path(user_path: str) -> Path:
    full_path = (ALLOWED_DIR / user_path).resolve()
    if not str(full_path).startswith(str(ALLOWED_DIR)):
        raise ValueError("Path traversal detected")
    return full_path
```

---

### 2.3. Валидация входных данных 🟡 СРЕДНИЙ РИСК

#### Проблема №3: Отсутствие валидации `bio` на XSS

**Файл:** `app/schemas.py`

```python
class AuthorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    bio: Optional[str] = Field(default=None)  # ❌ Нет sanitizer
```

**Риск:** Злоумышленник может сохранить HTML/JavaScript в поле `bio`:

```json
{
  "name": "Attacker",
  "bio": "<script>alert('XSS')</script>"
}
```

**Исправление:** Добавить санитизацию HTML или экранирование при выводе.

---

#### Проблема №4: Отсутствие rate limiting

**Файл:** `app/main.py`

```python
@app.post("/authors", response_model=Author, status_code=status.HTTP_201_CREATED)
def post_author(author_data: AuthorCreate) -> Author:
    return create_author(author_data)  # ❌ Нет защиты от brute-force
```

**Риск:** Возможны DoS-атаки и перебор данных.

**Исправление:** Добавить rate limiting через middleware (например, `slowapi`).

---

#### Проблема №5: Чрезмерное раскрытие информации в ошибках

**Файл:** `app/exceptions.py`

```python
class NotFoundError(Exception):
    def __init__(self, detail: str):
        self.detail = detail  # ❌ Может утечь структура БД
```

**Пример утечки:**
```json
{
  "detail": "Автор с id=999 не найден"
}
```

**Риск:** Раскрытие имён таблиц, полей, структуры данных.

**Исправление:** Использовать общие сообщения об ошибках в production.

---

### 2.4. Утечки конфиденциальной информации 🟡 СРЕДНИЙ РИСК

#### Проблема №6: Пароль БД в коде

**Файл:** `app/database.py`

```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://library_user:library_pass@localhost:5432/library_db"  # ❌ Хардкод
)
```

**Риск:** Учётные данные в коде могут попасть в репозиторий.

**Исправление:** Требовать переменную окружения, не использовать значение по умолчанию с паролем.

---

#### Проблема №7: Отсутствие логирования security-событий

**Файл:** `app/storage.py`

```python
def create_author(data: AuthorCreate) -> Author:
    with _db_session() as db:
        author = AuthorModel(**data.model_dump())
        db.add(author)
        db.commit()  # ❌ Нет лога создания
```

**Риск:** Невозможно отследить подозрительную активность.

**Исправление:** Добавить аудит-логирование критических операций.

---

### 2.5. CORS и заголовки безопасности 🔴 КРИТИЧНО

#### Проблема №8: Отсутствие настройки CORS

**Файл:** `app/main.py`

```python
app = FastAPI(
    title="Library API",
    description="REST API для управления книгами и авторами в библиотеке",
    version="1.1.0",
    lifespan=lifespan,
)  # ❌ Нет CORSMiddleware
```

**Риск:** Любой сайт может делать запросы к API от имени пользователя.

**Исправление:** Настроить CORS с явным списком разрешённых origins.

---

#### Проблема №9: Отсутствие security-заголовков

**Файл:** `app/main.py`

```python
# ❌ Нет заголовков:
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - Content-Security-Policy
# - Strict-Transport-Security
```

**Риск:** Clickjacking, MIME-sniffing атаки.

**Исправление:** Добавить middleware для security-заголовков.

---

## 3. Исправленная версия кода

### 3.1. `app/main.py` — Добавлены CORS и security-заголовки

```python
from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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

# Настройка логирования
logger = logging.getLogger("security")
logger.setLevel(logging.INFO)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    if os.getenv("TESTING", "false").lower() != "true":
        seed_books()
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
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

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
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    logger.warning(f"Not found: {exc.detail} from {request.client.host}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Ресурс не найден"}  # ✅ Общее сообщение
    )


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    logger.warning(f"Conflict: {exc.detail} from {request.client.host}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Конфликт данных"}  # ✅ Общее сообщение
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning(f"Rate limit exceeded: {request.client.host}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Слишком много запросов"}
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
    logger.info(f"Creating author: {author_data.name}")
    return create_author(author_data)


@app.put("/authors/{author_id}", response_model=Author)
@limiter.limit("10/minute")
def put_author(request: Request, author_id: int, author_data: AuthorUpdate) -> Author:
    return update_author(author_id, author_data)


@app.delete("/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def remove_author(request: Request, author_id: int) -> None:
    logger.info(f"Deleting author id={author_id}")
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
    logger.info(f"Creating book: {book_data.title} by author_id={book_data.author_id}")
    return create_book(book_data)


@app.put("/books/{book_id}", response_model=Book)
@limiter.limit("10/minute")
def put_book(request: Request, book_id: int, book_data: BookUpdate) -> Book:
    return update_book(book_id, book_data)


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def remove_book(request: Request, book_id: int) -> None:
    logger.info(f"Deleting book id={book_id}")
    delete_book(book_id)
```

---

### 3.2. `app/schemas.py` — Добавлена санитизация HTML

```python
from __future__ import annotations

import re
import html
from datetime import datetime
from typing import Optional, overload

from pydantic import BaseModel, ConfigDict, Field, field_validator


def sanitize_html(value: str) -> str:
    """Экранирует HTML-символы для предотвращения XSS."""
    return html.escape(value)


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
    bio: Optional[str] = Field(default=None, max_length=1000)
    
    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return sanitize_html(value.strip())
    
    @field_validator("bio")
    @classmethod
    def sanitize_bio(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return sanitize_html(value.strip())


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    bio: Optional[str] = None
    
    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return sanitize_html(value.strip())
    
    @field_validator("bio")
    @classmethod
    def sanitize_bio(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return sanitize_html(value.strip())


class Author(AuthorBase):
    id: int = Field(...)
    created_at: datetime = Field(...)

    model_config = ConfigDict(from_attributes=True)


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    isbn: str = Field(..., min_length=1, max_length=20)
    published_year: int = Field(..., ge=1450, le=9999)
    is_available: bool = Field(default=True)

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, value: str) -> str:
        return sanitize_html(value.strip())

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

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return sanitize_html(value.strip())

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
```

---

### 3.3. `app/database.py` — Убран хардкод пароля

```python
from __future__ import annotations

import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# Требуем переменную окружения — никаких паролей по умолчанию
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Example: postgresql+psycopg://user:password@host:5432/dbname"
    )

# Валидация URL (простая проверка)
if "@" not in DATABASE_URL:
    logger.warning("DATABASE_URL does not contain credentials. Using peer auth?")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=10,
    max_overflow=20,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### 3.4. `app/storage.py` — Добавлено логирование

```python
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
        logger.exception("Database transaction failed")
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
```

---

### 3.5. `requirements.txt` — Добавлены зависимости безопасности

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg[binary]==3.1.18
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
slowapi==0.1.9  # Rate limiting
```

---

## 4. Сводная таблица исправлений

| Уязвимость | Уровень | Статус | Исправление |
|------------|---------|--------|-------------|
| SQL-инъекции (прямые) | 🔴 Критично | ✅ Не найдено | Использованы параметризованные запросы SQLAlchemy |
| Path Traversal | 🟢 Низкий | ✅ Не применимо | Нет работы с файлами |
| XSS через bio/name | 🟡 Средний | ✅ Исправлено | Добавлена санитизация HTML в Pydantic-валидаторах |
| Rate Limiting | 🟡 Средний | ✅ Исправлено | Добавлен slowapi с лимитами на эндпоинты |
| Раскрытие информации в ошибках | 🟡 Средний | ✅ Исправлено | Общие сообщения об ошибках в production |
| Хардкод пароля БД | 🔴 Критично | ✅ Исправлено | Требуется переменная окружения DATABASE_URL |
| Отсутствие security-заголовков | 🔴 Критично | ✅ Исправлено | Добавлен middleware для заголовков |
| Отсутствие CORS | 🔴 Критично | ✅ Исправлено | Настроен CORSMiddleware с явными origins |
| Отсутствие логирования | 🟡 Средний | ✅ Исправлено | Добавлено логирование security-событий |

---

## 5. Рекомендации по дальнейшему улучшению

1. **Аутентификация и авторизация** — добавить JWT/OAuth2 для защиты эндпоинтов.
2. **Валидация контента** — использовать библиотеку `bleach` для санитизации HTML вместо простого экранирования.
3. **Аудит-логи** — вынести логи в отдельную систему (ELK Stack, Splunk).
4. **Secrets Management** — использовать HashiCorp Vault или AWS Secrets Manager.
5. **Dependency Scanning** — интегрировать `safety` или `pip-audit` в CI/CD.
6. **SAST/DAST** — добавить статический и динамический анализ безопасности.

---

## 6. Заключение

После применения исправлений уровень безопасности приложения повышен с 🟡 **Среднего** до 🟢 **Высокого**. Все критические уязвимости устранены, внедрены лучшие практики безопасности для FastAPI-приложений.
