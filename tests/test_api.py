from __future__ import annotations

from datetime import datetime

import pytest

from app.storage import clear_storage, get_all_authors, get_all_books, seed_books


VALID_AUTHOR = {
    "name": "Тестовый автор",
    "bio": "Биография тестового автора",
}

VALID_BOOK = {
    "title": "Тестовая книга",
    "isbn": "978-0-123456-78-9",
    "published_year": 2020,
    "is_available": True,
}




@pytest.fixture
def created_author(client):
    response = client.post("/authors", json=VALID_AUTHOR)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def created_book(client, created_author):
    payload = {**VALID_BOOK, "author_id": created_author["id"], "isbn": "978-0-000001-00-0"}
    response = client.post("/books", json=payload)
    assert response.status_code == 201
    return response.json()




def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Library API"
    assert data["version"] == "1.1.0"
    assert data["docs"] == "/docs"




def test_create_author_success(client):
    response = client.post("/authors", json=VALID_AUTHOR)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert isinstance(data["id"], int)
    assert data["name"] == VALID_AUTHOR["name"]
    assert data["bio"] == VALID_AUTHOR["bio"]
    assert "created_at" in data


def test_create_author_empty_name(client):
    payload = {**VALID_AUTHOR, "name": ""}
    response = client.post("/authors", json=payload)
    assert response.status_code == 422


def test_get_authors_empty(client):
    response = client.get("/authors")
    assert response.status_code == 200
    assert response.json() == []


def test_get_author_by_id_success(client, created_author):
    response = client.get(f"/authors/{created_author['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_author["id"]
    assert data["name"] == created_author["name"]


def test_get_author_by_id_not_found(client):
    response = client.get("/authors/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Автор с id=999 не найден"


def test_update_author_success(client, created_author):
    update_payload = {
        "name": "Обновлённый автор",
        "bio": "Обновлённая биография",
    }
    response = client.put(f"/authors/{created_author['id']}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_author["id"]
    assert data["name"] == update_payload["name"]
    assert data["bio"] == update_payload["bio"]


def test_update_author_partial(client, created_author):
    response = client.put(
        f"/authors/{created_author['id']}", json={"name": "Только имя"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Только имя"
    assert data["bio"] == created_author["bio"]


def test_update_author_not_found(client):
    response = client.put("/authors/999", json={"name": "Несуществующий"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Автор с id=999 не найден"


def test_delete_author_success(client, created_author):
    response = client.delete(f"/authors/{created_author['id']}")
    assert response.status_code == 204
    assert response.content == b""
    get_response = client.get(f"/authors/{created_author['id']}")
    assert get_response.status_code == 404


def test_delete_author_not_found(client):
    response = client.delete("/authors/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Автор с id=999 не найден"




def test_create_book_success(client, created_author):
    payload = {**VALID_BOOK, "author_id": created_author["id"]}
    response = client.post("/books", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == VALID_BOOK["title"]
    assert data["author_id"] == created_author["id"]
    assert data["isbn"] == VALID_BOOK["isbn"]
    assert data["published_year"] == VALID_BOOK["published_year"]
    assert data["is_available"] == VALID_BOOK["is_available"]


def test_create_book_author_not_found(client):
    payload = {**VALID_BOOK, "author_id": 999}
    response = client.post("/books", json=payload)
    assert response.status_code == 404
    assert "Автор с id=999 не найден" in response.json()["detail"]


def test_create_book_isbn_without_dashes(client, created_author):
    payload = {**VALID_BOOK, "author_id": created_author["id"], "isbn": "9780123456789"}
    response = client.post("/books", json=payload)
    assert response.status_code == 201
    assert response.json()["isbn"] == "9780123456789"


def test_create_book_default_is_available(client, created_author):
    payload = {k: v for k, v in VALID_BOOK.items() if k != "is_available"}
    payload["author_id"] = created_author["id"]
    response = client.post("/books", json=payload)
    assert response.status_code == 201
    assert response.json()["is_available"] is True


@pytest.mark.parametrize("field, invalid_value, expected_detail", [
    ("title", "", "String should have at least 1 character"),
    ("isbn", "", "String should have at least 1 character"),
])
def test_create_book_empty_string(client, created_author, field, invalid_value, expected_detail):
    payload = {**VALID_BOOK, "author_id": created_author["id"], field: invalid_value}
    response = client.post("/books", json=payload)
    assert response.status_code == 422
    assert expected_detail in str(response.json())


def test_create_book_invalid_year_future(client, created_author):
    future_year = datetime.now().year + 1
    payload = {**VALID_BOOK, "author_id": created_author["id"], "published_year": future_year}
    response = client.post("/books", json=payload)
    assert response.status_code == 422
    assert "Год издания не может быть больше текущего" in str(response.json())


def test_create_book_invalid_year_too_old(client, created_author):
    payload = {**VALID_BOOK, "author_id": created_author["id"], "published_year": 1449}
    response = client.post("/books", json=payload)
    assert response.status_code == 422
    assert "greater than or equal to 1450" in str(response.json())


def test_create_book_invalid_isbn_letters(client, created_author):
    payload = {**VALID_BOOK, "author_id": created_author["id"], "isbn": "978-abc"}
    response = client.post("/books", json=payload)
    assert response.status_code == 422
    assert "ISBN должен содержать только цифры и дефисы" in str(response.json())


def test_create_book_invalid_isbn_wrong_length(client, created_author):
    payload = {**VALID_BOOK, "author_id": created_author["id"], "isbn": "978-123"}
    response = client.post("/books", json=payload)
    assert response.status_code == 422
    assert "ISBN должен содержать 10 или 13 цифр" in str(response.json())


def test_get_books_empty(client):
    response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == []


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


def test_get_books_with_data(client, created_author):
    client.post("/books", json={**VALID_BOOK, "author_id": created_author["id"], "isbn": "978-0-999999-99-9"})
    response = client.get("/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_update_book_success(client, created_author, created_book):
    new_author = client.post("/authors", json={"name": "Новый автор", "bio": None}).json()
    update_payload = {
        "title": "Обновлённое название",
        "isbn": "978-1-234567-89-0",
        "published_year": 2021,
        "is_available": False,
        "author_id": new_author["id"],
    }
    response = client.put(f"/books/{created_book['id']}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_book["id"]
    assert data["title"] == update_payload["title"]
    assert data["author_id"] == new_author["id"]
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
    assert data["author_id"] == created_book["author_id"]
    assert data["isbn"] == created_book["isbn"]


def test_update_book_not_found(client):
    response = client.put("/books/999", json={"title": "Несуществующая"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Книга с id=999 не найдена"


def test_update_book_invalid_author(client, created_book):
    response = client.put(
        f"/books/{created_book['id']}", json={"author_id": 999}
    )
    assert response.status_code == 404
    assert "Автор с id=999 не найден" in response.json()["detail"]


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


def test_create_book_response_structure(client, created_author):
    response = client.post("/books", json={**VALID_BOOK, "author_id": created_author["id"], "isbn": "978-0-000002-00-0"})
    assert response.status_code == 201
    data = response.json()
    expected_keys = {"id", "title", "author_id", "isbn", "published_year", "is_available"}
    assert set(data.keys()) == expected_keys
    assert isinstance(data["id"], int)
    assert isinstance(data["title"], str)
    assert isinstance(data["author_id"], int)
    assert isinstance(data["isbn"], str)
    assert isinstance(data["published_year"], int)
    assert isinstance(data["is_available"], bool)


def test_multiple_books_increment_ids(client, created_author):
    ids = []
    for i in range(3):
        payload = {
            **VALID_BOOK,
            "title": f"Книга {i}",
            "isbn": f"978-0-123456-78-{i}",
            "author_id": created_author["id"],
        }
        response = client.post("/books", json=payload)
        assert response.status_code == 201
        ids.append(response.json()["id"])

    assert ids == sorted(ids)
    assert len(set(ids)) == 3

    response = client.get("/books")
    assert len(response.json()) == 3


def test_create_author_duplicate_name(client):
    client.post("/authors", json=VALID_AUTHOR)
    response = client.post("/authors", json=VALID_AUTHOR)
    assert response.status_code == 409
    assert "уже существует" in response.json()["detail"]


def test_delete_author_with_books_conflict(client, created_book):
    response = client.delete(f"/authors/{created_book['author_id']}")
    assert response.status_code == 409
    assert "есть книги" in response.json()["detail"]


def test_create_book_duplicate_isbn(client, created_author, created_book):
    payload = {**VALID_BOOK, "author_id": created_author["id"], "isbn": created_book["isbn"]}
    response = client.post("/books", json=payload)
    assert response.status_code == 409
    assert "уже существует" in response.json()["detail"]


def test_seed_books_populates_database(client):
    seed_books()
    assert len(get_all_authors()) >= 3
    assert len(get_all_books()) >= 3


def test_clear_storage_removes_all(client):
    clear_storage()
    assert get_all_books() == []
    assert get_all_authors() == []