from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import clear_storage


@pytest.fixture
def client():
    clear_storage()
    with TestClient(app) as c:
        yield c