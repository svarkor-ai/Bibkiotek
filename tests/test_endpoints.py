"""Integration tests for all FastAPI endpoints via TestClient."""

from unittest.mock import patch

from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

class TestAuthEndpoints:
    def test_login_success(self, client):
        resp = client.post(
            "/api/auth/login",
            params={"username": "admin", "password": "admin"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["user"]["role"] == "admin"

    def test_login_wrong_password(self, client):
        resp = client.post(
            "/api/auth/login",
            params={"username": "admin", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_token_works_for_protected_route(self, client):
        """Obtain a token and use it to access a protected route."""
        login_resp = client.post(
            "/api/auth/login",
            params={"username": "admin", "password": "admin"},
        )
        token = login_resp.json()["access_token"]

        books_resp = client.get(
            "/api/books",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert books_resp.status_code == 200


# ---------------------------------------------------------------------------
# Books endpoints
# ---------------------------------------------------------------------------

class TestBooksEndpoints:
    def test_list_books_empty(self, client, admin_token):
        resp = client.get("/api/books", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_list_books_with_items(self, client, admin_token, sample_book):
        resp = client.get("/api/books", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_books_pagination(self, client, admin_token):
        from src.books import create_book
        from src.database import get_session
        # Use the client's patched engine directly
        from src.database import get_engine
        from sqlalchemy.orm import Session as SA_Session
        with SA_Session(get_engine()) as db:
            for i in range(5):
                create_book(db, isbn=f"pag{i}", title=f"Book {i}")
                db.commit()

        resp = client.get(
            "/api/books?limit=2&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["total"] == 5

    def test_list_books_filter_hcf(self, client, admin_token):
        from src.books import create_book
        from src.database import get_engine
        from sqlalchemy.orm import Session as SA_Session
        with SA_Session(get_engine()) as db:
            create_book(db, isbn="hcf1", title="Barn Bok", hcf_category="hcf")
            create_book(db, isbn="hcf2", title="Vuxen Bok", hcf_category="adult")
            db.commit()

        resp = client.get(
            "/api/books?hcf_category=hcf",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_search_books(self, client, admin_token):
        from src.books import create_book
        from src.database import get_engine
        from sqlalchemy.orm import Session as SA_Session
        with SA_Session(get_engine()) as db:
            create_book(db, isbn="srch1", title="Python Programming")
            create_book(db, isbn="srch2", title="Java Basics")
            db.commit()

        resp = client.get(
            "/api/books/search?q=Python",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        titles = [b["title"] for b in body["items"]]
        assert "Python Programming" in titles

    def test_search_books_no_match(self, client, admin_token):
        from src.books import create_book
        from src.database import get_engine
        from sqlalchemy.orm import Session as SA_Session
        with SA_Session(get_engine()) as db:
            create_book(db, isbn="nomatch1", title="Something Else")
            db.commit()

        resp = client.get(
            "/api/books/search?q=xyznotfound123",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# Loans endpoints
# ---------------------------------------------------------------------------

class TestLoansEndpoints:
    def test_checkout(self, client, admin_token, sample_book):
        """Admin can check out a book."""
        resp = client.post(
            "/api/loans/checkout",
            json={
                "book_id": sample_book["id"],
                "user_id": 1,
                "librarian_id": 2,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["book_id"] == sample_book["id"]
        assert body["overdue"] is False

    def test_checkout_28_day_period(self, client, sample_book):
        """Verify checkout creates a loan with a 28-day due date."""
        from src.database import get_engine
        from sqlalchemy.orm import Session as SA_Session
        from src.circulation import checkout as _checkout
        with SA_Session(get_engine()) as db:
            now = datetime(2025, 6, 1, tzinfo=timezone.utc)
            with patch("src.circulation.datetime") as mock_dt:
                mock_dt.now.return_value = now
                mock_dt.timedelta = timedelta
                loan = _checkout(db, book_id=sample_book["id"], user_id=1, librarian_id=2)
                expected = now + timedelta(days=28)
                assert loan.due_date.replace(tzinfo=None, microsecond=0) == expected.replace(microsecond=0, tzinfo=None)

    def test_checkout_already_out(self, client, admin_token, sample_book):
        """Trying to checkout a book that's already out should fail."""
        client.post(
            "/api/loans/checkout",
            json={"book_id": sample_book["id"], "user_id": 1, "librarian_id": 2},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.post(
            "/api/loans/checkout",
            json={"book_id": sample_book["id"], "user_id": 2, "librarian_id": 2},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    def test_return_book(self, client, admin_token, sample_book):
        """Admin can return a book."""
        # First check out
        loan_resp = client.post(
            "/api/loans/checkout",
            json={"book_id": sample_book["id"], "user_id": 1, "librarian_id": 2},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        loan_id = loan_resp.json()["id"]

        resp = client.post(
            "/api/loans/return",
            json={"loan_id": loan_id},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["return_date"] is not None

    def test_active_loans(self, client, admin_token, sample_book):
        """List active loans."""
        client.post(
            "/api/loans/checkout",
            json={"book_id": sample_book["id"], "user_id": 1, "librarian_id": 2},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.get(
            "/api/loans/active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_overdue_endpoint(self, client, admin_token):
        """Admin can view overdue loans."""
        from src.database import get_engine
        from src.models import Loan
        from sqlalchemy.orm import Session as SA_Session
        with SA_Session(get_engine()) as db:
            now = datetime(2025, 7, 1, tzinfo=timezone.utc)
            loan = Loan(
                book_id=1,
                user_id=1,
                librarian_id=2,
                checkout_date=now - timedelta(days=30),
                due_date=now - timedelta(days=2),
                return_date=None,
            )
            db.add(loan)
            db.commit()

        resp = client.get(
            "/api/loans/overdue",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_user_loans(self, client, user_token):
        """Regular user can view their own loans."""
        resp = client.get(
            "/api/loans/user/3",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_user_cannot_view_other_user_loans(self, client, user_token):
        """Regular user cannot view another user's loans."""
        resp = client.get(
            "/api/loans/user/1",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_checkout_requires_auth(self, client):
        """Checkout without auth token is rejected."""
        resp = client.post(
            "/api/loans/checkout",
            json={"book_id": 1, "user_id": 1, "librarian_id": 2},
        )
        assert resp.status_code in (401, 403)

    def test_return_requires_auth(self, client):
        """Return without auth token is rejected."""
        resp = client.post(
            "/api/loans/return",
            json={"loan_id": 1},
        )
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Users endpoints
# ---------------------------------------------------------------------------

class TestUsersEndpoints:
    def test_register(self, client):
        resp = client.post(
            "/api/users/register",
            params={"username": "reguser", "password": "regpass", "role": "user"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == "reguser"
        assert body["role"] == "user"

    def test_list_users_admin_only(self, client, admin_token):
        resp = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "users" in body
        assert body["total"] >= 3

    def test_get_user(self, client, admin_token):
        resp = client.get(
            "/api/users/1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "admin"

    def test_update_user(self, client, admin_token):
        resp = client.put(
            "/api/users/3",
            params={"email": "updated@test.com"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "updated@test.com"

    def test_list_users_requires_admin(self, client, librarian_token):
        """Only admin can list all users."""
        resp = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {librarian_token}"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Cross-module integration
# ---------------------------------------------------------------------------

class TestFullWorkflow:
    """End-to-end workflow: register → login → create book → checkout → return."""

    def test_checkout_and_return_flow(self, client, admin_token, sample_book):
        """Complete checkout/return cycle."""
        # 1. Checkout
        co_resp = client.post(
            "/api/loans/checkout",
            json={
                "book_id": sample_book["id"],
                "user_id": 1,
                "librarian_id": 2,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert co_resp.status_code == 200
        loan_id = co_resp.json()["id"]

        # 2. Return
        ret_resp = client.post(
            "/api/loans/return",
            json={"loan_id": loan_id},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert ret_resp.status_code == 200
        assert ret_resp.json()["return_date"] is not None

        # 3. Book should be checkable out again
        co_resp2 = client.post(
            "/api/loans/checkout",
            json={
                "book_id": sample_book["id"],
                "user_id": 1,
                "librarian_id": 2,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert co_resp2.status_code == 200

    def test_register_then_login(self, client):
        """Register a user then authenticate."""
        # Register
        reg_resp = client.post(
            "/api/users/register",
            params={
                "username": "flowuser",
                "password": "flowpass",
                "role": "user",
            },
        )
        assert reg_resp.status_code == 200

        # Login
        login_resp = client.post(
            "/api/auth/login",
            params={"username": "flowuser", "password": "flowpass"},
        )
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()

    def test_unauthenticated_access_all_endpoints(self, client):
        """Authenticated-only endpoints should reject unauthenticated requests."""
        auth_endpoints = [
            "/api/loans/active",
            "/api/loans/overdue",
            "/api/users",
        ]
        for path in auth_endpoints:
            resp = client.get(path)
            assert resp.status_code in (401, 403), f"{path} returned {resp.status_code}"
