from __future__ import annotations

from datetime import datetime

import pytest


VALID_BOOK = {
    "title": "Тестовая книга",
    "author": "Тестовый автор",
    "isbn": "978-0-123456-78-9",
    "published_year": 2020,
    "is_available": True,
}


@pytest.fixture
def created_book(client):
    payload = {**VALID_BOOK, "isbn": "978-0-000001-00-0"}
    response = client.post("/books", json=payload)
    assert response.status_code == 201
    return response.json()


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Library API"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"


def test_get_books_empty(client):
    response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == []


def test_create_book_success(client):
    response = client.post("/books", json=VALID_BOOK)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["title"] == VALID_BOOK["title"]
    assert data["author"] == VALID_BOOK["author"]
    assert data["isbn"] == VALID_BOOK["isbn"]
    assert data["published_year"] == VALID_BOOK["published_year"]
    assert data["is_available"] == VALID_BOOK["is_available"]


def test_create_book_isbn_without_dashes(client):
    payload = {**VALID_BOOK, "isbn": "9780123456789"}
    response = client.post("/books", json=payload)
    assert response.status_code == 201
    assert response.json()["isbn"] == "9780123456789"


def test_create_book_default_is_available(client):
    payload = {k: v for k, v in VALID_BOOK.items() if k != "is_available"}
    response = client.post("/books", json=payload)
    assert response.status_code == 201
    assert response.json()["is_available"] is True


@pytest.mark.parametrize("field, invalid_value, expected_detail", [
    ("title", "", "String should have at least 1 character"),
    ("author", "", "String should have at least 1 character"),
    ("isbn", "", "String should have at least 1 character"),
])
def test_create_book_empty_string(client, field, invalid_value, expected_detail):
    payload = {**VALID_BOOK, field: invalid_value}
    response = client.post("/books", json=payload)
    assert response.status_code == 422
    assert expected_detail in str(response.json())


def test_create_book_invalid_year_future(client):
    future_year = datetime.now().year + 1
    payload = {**VALID_BOOK, "published_year": future_year}
    response = client.post("/books", json=payload)
    assert response.status_code == 422
    assert "Год издания не может быть больше текущего" in str(response.json())


def test_create_book_invalid_year_too_old(client):
    payload = {**VALID_BOOK, "published_year": 1449}
    response = client.post("/books", json=payload)
    assert response.status_code == 422
    assert "greater than or equal to 1450" in str(response.json())


def test_create_book_invalid_isbn_letters(client):
    payload = {**VALID_BOOK, "isbn": "978-abc"}
    response = client.post("/books", json=payload)
    assert response.status_code == 422
    assert "ISBN должен содержать только цифры и дефисы" in str(response.json())


def test_create_book_invalid_isbn_wrong_length(client):
    payload = {**VALID_BOOK, "isbn": "978-123"}
    response = client.post("/books", json=payload)
    assert response.status_code == 422
    assert "ISBN должен содержать 10 или 13 цифр" in str(response.json())


def test_get_book_by_id_success(client, created_book):
    response = client.get(f"/books/{created_book['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_book["id"]
    assert data["title"] == created_book["title"]


def test_get_book_by_id_not_found(client):
    response = client.get("/books/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Книга с id=999 не найдена"


def test_get_books_with_data(client):
    client.post("/books", json={**VALID_BOOK, "isbn": "978-0-999999-99-9"})
    response = client.get("/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_update_book_success(client, created_book):
    update_payload = {
        "title": "Обновлённое название",
        "author": "Обновлённый автор",
        "isbn": "978-1-234567-89-0",
        "published_year": 2021,
        "is_available": False,
    }
    response = client.put(f"/books/{created_book['id']}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_book["id"]
    assert data["title"] == update_payload["title"]
    assert data["author"] == update_payload["author"]
    assert data["isbn"] == update_payload["isbn"]
    assert data["published_year"] == update_payload["published_year"]
    assert data["is_available"] == update_payload["is_available"]


def test_update_book_partial(client, created_book):
    response = client.put(
        f"/books/{created_book['id']}", json={"title": "Только заголовок"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Только заголовок"
    assert data["author"] == created_book["author"]
    assert data["isbn"] == created_book["isbn"]
    assert data["published_year"] == created_book["published_year"]
    assert data["is_available"] == created_book["is_available"]


def test_update_book_not_found(client):
    response = client.put("/books/999", json={"title": "Несуществующая"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Книга с id=999 не найдена"


def test_update_book_invalid_year(client, created_book):
    future_year = datetime.now().year + 1
    response = client.put(
        f"/books/{created_book['id']}", json={"published_year": future_year}
    )
    assert response.status_code == 422
    assert "Год издания не может быть больше текущего" in str(response.json())


def test_update_book_invalid_isbn(client, created_book):
    response = client.put(
        f"/books/{created_book['id']}", json={"isbn": "bad-isbn"}
    )
    assert response.status_code == 422
    assert "ISBN должен содержать только цифры и дефисы" in str(response.json())


def test_delete_book_success(client, created_book):
    response = client.delete(f"/books/{created_book['id']}")
    assert response.status_code == 204
    assert response.content == b""
    get_response = client.get(f"/books/{created_book['id']}")
    assert get_response.status_code == 404


def test_delete_book_not_found(client):
    response = client.delete("/books/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Книга с id=999 не найдена"


def test_create_book_response_structure(client):
    response = client.post("/books", json={**VALID_BOOK, "isbn": "978-0-000002-00-0"})
    assert response.status_code == 201
    data = response.json()
    expected_keys = {"id", "title", "author", "isbn", "published_year", "is_available"}
    assert set(data.keys()) == expected_keys
    assert isinstance(data["id"], int)
    assert isinstance(data["title"], str)
    assert isinstance(data["author"], str)
    assert isinstance(data["isbn"], str)
    assert isinstance(data["published_year"], int)
    assert isinstance(data["is_available"], bool)


def test_multiple_books_increment_ids(client):
    ids = []
    for i in range(3):
        payload = {**VALID_BOOK, "title": f"Книга {i}", "isbn": f"978-0-123456-78-{i}"}
        response = client.post("/books", json=payload)
        assert response.status_code == 201
        ids.append(response.json()["id"])

    assert ids == sorted(ids)
    assert len(set(ids)) == 3

    response = client.get("/books")
    assert len(response.json()) == 3


def test_seed_books_populates_database(client):
    from app.storage import seed_books, get_all_books

    seed_books()
    books = get_all_books()
    assert len(books) >= 3


def test_clear_storage_removes_all_books(client):
    from app.storage import clear_storage, get_all_books

    client.post("/books", json={**VALID_BOOK, "isbn": "978-0-clear-00-0"})
    clear_storage()
    assert get_all_books() == []
