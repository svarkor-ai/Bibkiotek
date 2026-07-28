"""Database session, engine, and initialisation for Bibliotek."""

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from src.config import DATABASE_URL
from src.models import Base

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_engine = None  # lazily created


def get_engine() -> "engine":
    """Return a shared SQLAlchemy engine (SQLite with WAL mode).

    WAL (Write-Ahead Logging) lets readers not block writers and vice versa,
    which is important for a FastAPI app that handles concurrent HTTP requests.
    """
    global _engine
    if _engine is None:
        if not DATABASE_URL.startswith("sqlite"):
            raise RuntimeError(
                f"Unsupported database URL scheme: {DATABASE_URL!r}. "
                "Bibliotek requires SQLite."
            )

        # Extract path from sqlite:///./bibliotek.db → ./bibliotek.db
        db_path = DATABASE_URL.replace("sqlite:///", "")
        # Resolve relative paths against the project root
        db_file = Path(db_path)
        if not db_file.is_absolute():
            db_file = Path(__file__).resolve().parent.parent / db_file

        # Ensure parent directory exists
        db_file.parent.mkdir(parents=True, exist_ok=True)

        connect_args = {}
        if db_path.startswith(":memory:"):
            connect_args = {"check_same_thread": False}

        _engine = create_engine(
            DATABASE_URL,
            connect_args=connect_args,
            pool_pre_ping=True,
            echo=False,
        )

        # --- Enable WAL mode on first connect ---
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _conn_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            # Faster writes, single-writer lock
            cursor.execute("PRAGMA synchronous=NORMAL")
            # Optimise memory for the cache
            cursor.execute("PRAGMA cache_size=-64000")  # 64 MB
            cursor.close()

    return _engine


# Re-export engine type for type-checkers
from sqlalchemy import Engine  # noqa: E402, F401
# Keep a clean reference
# Type hint is set via docstring + the Engine import above


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a SQLAlchemy session; auto-commits on success, rollback on error."""
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables defined in models."""
    Base.metadata.create_all(get_engine())


def drop_all() -> None:
    """Drop all tables (dev / seed only)."""
    Base.metadata.drop_all(get_engine())
