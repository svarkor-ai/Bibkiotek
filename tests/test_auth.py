"""Tests for auth module — JWT, password hashing, login endpoint."""

import time
from datetime import datetime, timezone

from jose import jwt as jose_jwt

from src.auth import (
    create_access_token,
    check_password,
    hash_password,
    verify_token,
)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    """bcrypt hashing round-trips and edge cases."""

    def test_hash_and_check(self):
        h = hash_password("my_secret")
        assert h.startswith("$2b$")
        assert check_password("my_secret", h) is True

    def test_wrong_password(self):
        h = hash_password("correct_pass")
        assert check_password("wrong_pass", h) is False

    def test_empty_password(self):
        h = hash_password("")
        assert check_password("", h) is True
        assert check_password("not_empty", h) is False

    def test_uniqueness(self):
        """Two hashes of the same password should differ (different salt)."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

class TestJWT:
    """Token creation, verification, and expiry."""

    def test_create_token(self):
        token = create_access_token(user_id=42, role="admin")
        assert isinstance(token, str)
        assert len(token) > 20  # non-trivial JWT

    def test_verify_token(self):
        token = create_access_token(user_id=99, role="librarian")
        payload = verify_token(token)
        assert payload is not None
        assert payload["user_id"] == 99
        assert payload["role"] == "librarian"

    def test_verify_invalid_token(self):
        assert verify_token("garbage.token.here") is None

    def test_verify_expired_token(self):
        """Create a token that already expired and verify it returns None."""
        from src.config import SECRET_KEY, JWT_ALGORITHM
        from datetime import datetime, timezone, timedelta
        past = datetime.now(timezone.utc) - timedelta(days=1)
        payload = {
            "sub": "1",
            "role": "user",
            "exp": past,  # already expired
            "iat": past,
        }
        token = jose_jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
        assert verify_token(token) is None

    def test_token_contains_user_id(self):
        for uid in [1, 100, 9999]:
            tok = create_access_token(user_id=uid, role="user")
            p = verify_token(tok)
            assert p["user_id"] == uid


# ---------------------------------------------------------------------------
# Login endpoint
# ---------------------------------------------------------------------------

class TestLoginEndpoint:
    """POST /api/auth/login via TestClient."""

    def test_login_admin_success(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["user"]["username"] == "admin"
        assert body["user"]["role"] == "admin"

    def test_login_wrong_password(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "ghost", "password": "ghost"},
        )
        assert resp.status_code == 401

    def test_login_returns_valid_jwt(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        token = resp.json()["access_token"]
        payload = verify_token(token)
        assert payload is not None
        assert payload["role"] == "admin"
