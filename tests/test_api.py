from __future__ import annotations

import pytest


VALID_BOOK = {
    "title": "Тестовая книга",
    "author": "Тестовый автор",
    "isbn": "978-0-123456-78-9",
    "published_year": 2020,
    "is_available": True,
}


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
    assert data["id"] == 1
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
    from datetime import datetime
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


def test_get_book_by_id_success(client):
    client.post("/books", json=VALID_BOOK)
    response = client.get("/books/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == VALID_BOOK["title"]


def test_get_book_by_id_not_found(client):
    response = client.get("/books/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Книга с id=999 не найдена"


def test_get_books_with_data(client):
    client.post("/books", json=VALID_BOOK)
    response = client.get("/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == VALID_BOOK["title"]


def test_update_book_success(client):
    client.post("/books", json=VALID_BOOK)
    update_payload = {
        "title": "Обновлённое название",
        "author": "Обновлённый автор",
        "isbn": "978-1-234567-89-0",
        "published_year": 2021,
        "is_available": False,
    }
    response = client.put("/books/1", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == update_payload["title"]
    assert data["author"] == update_payload["author"]
    assert data["isbn"] == update_payload["isbn"]
    assert data["published_year"] == update_payload["published_year"]
    assert data["is_available"] == update_payload["is_available"]


def test_update_book_partial(client):
    client.post("/books", json=VALID_BOOK)
    response = client.put("/books/1", json={"title": "Только заголовок"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Только заголовок"
    assert data["author"] == VALID_BOOK["author"]
    assert data["isbn"] == VALID_BOOK["isbn"]
    assert data["published_year"] == VALID_BOOK["published_year"]
    assert data["is_available"] == VALID_BOOK["is_available"]


def test_update_book_not_found(client):
    response = client.put("/books/999", json={"title": "Несуществующая"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Книга с id=999 не найдена"


def test_update_book_invalid_year(client):
    client.post("/books", json=VALID_BOOK)
    from datetime import datetime
    future_year = datetime.now().year + 1
    response = client.put("/books/1", json={"published_year": future_year})
    assert response.status_code == 422
    assert "Год издания не может быть больше текущего" in str(response.json())


def test_update_book_invalid_isbn(client):
    client.post("/books", json=VALID_BOOK)
    response = client.put("/books/1", json={"isbn": "bad-isbn"})
    assert response.status_code == 422
    assert "ISBN должен содержать только цифры и дефисы" in str(response.json())


def test_delete_book_success(client):
    client.post("/books", json=VALID_BOOK)
    response = client.delete("/books/1")
    assert response.status_code == 204
    assert response.content == b""
    get_response = client.get("/books/1")
    assert get_response.status_code == 404


def test_delete_book_not_found(client):
    response = client.delete("/books/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Книга с id=999 не найдена"


def test_create_book_response_structure(client):
    response = client.post("/books", json=VALID_BOOK)
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
    for i in range(3):
        payload = {**VALID_BOOK, "title": f"Книга {i}"}
        response = client.post("/books", json=payload)
        assert response.status_code == 201
        assert response.json()["id"] == i + 1

    response = client.get("/books")
    assert len(response.json()) == 3
