"""Shared pytest fixtures for Bibliotek tests."""

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SA_Session

TEST_DB_PATH = Path(tempfile.mkdtemp()) / "bibliotek_test.db"


@pytest.fixture(autouse=True, scope="session")
def _clear_env():
    """Ensure DATABASE_URL points to our temp file."""
    os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
    yield
    try:
        TEST_DB_PATH.unlink()
    except FileNotFoundError:
        pass


@pytest.fixture(scope="session")
def engine():
    """Shared SQLAlchemy engine for the test DB."""
    from src.database import get_engine
    return get_engine()


def _create_test_tables(engine):
    """Create all tables in the test DB."""
    from src.models import Base
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def _seed_users(session: SA_Session):
    """Create admin, librarian, and regular user."""
    from src.users import register_user
    register_user(session, "admin", "admin", role="admin")
    register_user(session, "librarian", "librarian", role="librarian")
    register_user(session, "testuser", "password123", role="user")


@pytest.fixture()
def session(engine) -> Generator[SA_Session, None, None]:
    """Fresh Session per test with tables created and users seeded."""
    _create_test_tables(engine)
    with SA_Session(engine) as sess:
        _seed_users(sess)
        yield sess


@pytest.fixture()
def client(engine) -> Generator[TestClient, None, None]:
    """FastAPI TestClient backed by the test DB with users seeded."""
    _create_test_tables(engine)
    with SA_Session(engine) as s:
        _seed_users(s)
        s.commit()

    import src.database as db_mod
    import src.books as books_mod
    import src.circulation as circ_mod

    orig_db_get_engine = db_mod.get_engine
    orig_db_get_session = db_mod.get_session
    orig_db_get_session_cm = db_mod.get_session_cm
    orig_books_get_engine = books_mod.get_engine
    orig_books_get_db = books_mod.get_db
    orig_books_get_iter = books_mod._iter_session
    orig_circ_get_session = circ_mod.get_session

    def patched_engine():
        return engine

    db_mod.get_engine = patched_engine

    # Patch get_session (NOT @contextmanager) — FastAPI Depends() expects a plain generator,
    # not a contextmanager. get_session_cm is used in the startup hook via `with`,
    # so that one can be @contextmanager.
    def patched_get_session():
        s = SA_Session(engine)
        try:
            yield s
            s.commit()
        finally:
            s.close()

    @contextmanager
    def patched_get_session_cm():
        s = SA_Session(engine)
        try:
            yield s
            s.commit()
        finally:
            s.close()

    db_mod.get_session = patched_get_session
    db_mod.get_session_cm = patched_get_session_cm

    # Patch books.py's own session iterator — must be a plain generator, NOT
    # @contextmanager, because books.py's get_db() does `yield from _iter_session()`
    # and yield-from on a GeneratorContextManager fails.
    def patched_iter_session():
        s = SA_Session(engine)
        try:
            yield s
            s.commit()
        finally:
            s.close()

    books_mod.get_db = patched_iter_session
    books_mod._iter_session = patched_iter_session

    # Patch circulation.py's session import too — it imports `from src.database import get_session`
    # at module level, so patching src.database isn't enough; we must patch the reference in circulation
    circ_mod.get_session = patched_get_session

    from src.app import app
    with TestClient(app) as c:
        yield c

    db_mod.get_engine = orig_db_get_engine
    books_mod.get_engine = orig_books_get_engine
    circ_mod.get_session = orig_circ_get_session


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, username: str, password: str) -> str:
    """Login and return the JWT token string."""
    resp = client.post(
        "/api/auth/login",
        params={"username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_token(client) -> str:
    return _login(client, "admin", "admin")


@pytest.fixture()
def librarian_token(client) -> str:
    return _login(client, "librarian", "librarian")


@pytest.fixture()
def user_token(client) -> str:
    return _login(client, "testuser", "password123")


@pytest.fixture()
def admin_user(session) -> dict:
    return {"username": "admin", "password": "admin", "role": "admin"}


@pytest.fixture()
def librarian_user(session) -> dict:
    return {"username": "librarian", "password": "librarian", "role": "librarian"}


@pytest.fixture()
def regular_user(session) -> dict:
    return {"username": "testuser", "password": "password123", "role": "user"}


@pytest.fixture()
def sample_book(session) -> dict:
    """Create and return a sample book."""
    from src.books import create_book
    book = create_book(
        session,
        isbn="9780061120084",
        title="To Kill a Mockingbird",
        author="Harper Lee",
        publisher="HarperCollins",
        year=1960,
    )
    session.commit()  # persist the book so the client can see it
    return book.to_dict()
