import pytest
from backend.app import create_app
from backend.config import TestingConfig
from backend.app.utils.db import get_connection, init_sqlite_db

@pytest.fixture(scope="session")
def persistent_test_db():
    conn = get_connection(TestingConfig)
    init_sqlite_db(conn)
    yield conn
    conn.close()

@pytest.fixture
def app(persistent_test_db):
    app = create_app(TestingConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_conn(persistent_test_db):
    conn = get_connection(TestingConfig)
    yield conn
    conn.close()
