import pytest
import database.db as db_module
from app import app as flask_app


@pytest.fixture
def app(tmp_path):
    db_module.DB_PATH = str(tmp_path / "test.db")
    from database.db import init_db, seed_db
    init_db()
    seed_db()
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "password123"})
    return client
