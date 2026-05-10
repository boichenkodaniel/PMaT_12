# Лабораторная работа № 12
## Разработка и тестирование REST API на Python

**Студент:** Бойченко Даниэль Дмитриевич  
**Группа:** 220032-11  
**Вариант:** 2

---

### Задания

| № | Формулировка |
|---|----------|
| 1 | Генерация CRUD-приложения. |

---

## Технологии

- **Язык:** Python 3.13+
- **Фреймворк:** FastAPI
- **Валидация:** Pydantic v2
- **Сервер:** Uvicorn
- **Тестирование:** pytest, httpx

---

## Структура проекта

```
app/
├── __init__.py      # Инициализация пакета
├── main.py          # Точка входа FastAPI-приложения
├── schemas.py       # Pydantic-модели (валидация данных)
└── storage.py       # In-memory хранилище книг


requirements.txt     # Зависимости проекта
```

---

## Инструкция по сборке и запуску

### Предварительные требования

- [Python](https://www.python.org/downloads/) 3.13+ установлен
- [pip](https://pip.pypa.io/en/stable/installation/) доступен

---

### Задание 1 — Генерация CRUD-приложения.

Приложение предоставляет CRUD-операции для управления книгами в библиотеке с валидацией данных через Pydantic.

#### Установка зависимостей

```bash
pip install -r requirements.txt
```

#### Запуск приложения

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Или напрямую через Python:

```bash
python app/main.py
```

Приложение будет доступно по адресу: http://127.0.0.1:8000

Интерактивная документация (Swagger UI): http://127.0.0.1:8000/docs

#### Доступные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Корневой эндпоинт (информация об API) |
| GET | `/books` | Получить список всех книг |
| GET | `/books/{book_id}` | Получить книгу по ID |
| POST | `/books` | Создать новую книгу |
| PUT | `/books/{book_id}` | Обновить книгу (полностью или частично) |
| DELETE | `/books/{book_id}` | Удалить книгу |

#### Примеры запросов

**Создание книги:**
```bash
curl -X POST "http://localhost:8000/books" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Война и мир",
    "author": "Лев Толстой",
    "isbn": "978-5-699-12014-7",
    "published_year": 1869,
    "is_available": true
  }'
```

**Получение всех книг:**
```bash
curl "http://localhost:8000/books"
```

**Получение книги по ID:**
```bash
curl "http://localhost:8000/books/1"
```

**Частичное обновление книги:**
```bash
curl -X PUT "http://localhost:8000/books/1" \
  -H "Content-Type: application/json" \
  -d '{"title": "Война и мир (новое издание)"}'
```

**Удаление книги:**
```bash
curl -X DELETE "http://localhost:8000/books/1"
```

#### Валидация данных

Pydantic-модели автоматически проверяют входные данные:

- `title`, `author` — строки от 1 до 200 символов
- `isbn` — строка от 1 до 20 символов, содержит только цифры и дефисы, после очистки 10 или 13 цифр
- `published_year` — целое число от 1450 до текущего года
- `is_available` — булево значение (по умолчанию `true`)

Пример ошибки валидации:
```bash
curl -X POST "http://localhost:8000/books" \
  -H "Content-Type: application/json" \
  -d '{"title": "", "author": "Test", "isbn": "978-0-123456-78-9", "published_year": 2020}'
```
Ответ: `422 Unprocessable Entity` с описанием ошибок.

---
