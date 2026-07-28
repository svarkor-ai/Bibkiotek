"""Tests for circulation — checkout, return, overdue logic.

28-day lending period is the core business rule and is tested explicitly.
"""
import pytest

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException
from src.circulation import (
    checkout,
    return_book,
    is_overdue,
    get_user_loans,
    get_overdue_loans,
    get_book_loans,
)
from src.models import Loan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_book(session, isbn="9780061120084", title="Test Book"):
    from src.books import create_book
    return create_book(session, isbn=isbn, title=title, author="Author", year=2020)


# ---------------------------------------------------------------------------
# checkout
# ---------------------------------------------------------------------------

class TestCheckout:
    def test_checkout_success(self, session):
        book = _create_book(session)
        loan = checkout(session, book_id=book.id, user_id=1, librarian_id=2)
        assert loan.book_id == book.id
        assert loan.user_id == 1
        assert loan.librarian_id == 2

    def test_checkout_28_day_due_date(self, session):
        """Explicitly verify that due_date = checkout_date + 28 days."""
        book = _create_book(session)
        # Fake "now" so we can assert exact due_date
        now = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch("src.circulation.datetime") as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.timedelta = timedelta
            loan = checkout(session, book_id=book.id, user_id=1, librarian_id=2)
            expected_due = now + timedelta(days=28)
            # SQLite stores naive datetimes — strip tzinfo for comparison
            assert loan.due_date.replace(tzinfo=None).replace(microsecond=0) == expected_due.replace(tzinfo=None).replace(microsecond=0)

    def test_checkout_book_not_found(self, session):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            checkout(session, book_id=9999, user_id=1, librarian_id=2)
        assert exc.value.status_code == 404

    def test_checkout_user_not_found(self, session):
        book = _create_book(session)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            checkout(session, book_id=book.id, user_id=9999, librarian_id=2)
        assert exc.value.status_code == 404

    def test_checkout_book_already_out(self, session):
        book = _create_book(session)
        checkout(session, book_id=book.id, user_id=1, librarian_id=2)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            checkout(session, book_id=book.id, user_id=2, librarian_id=2)
        assert exc.value.status_code == 400
        assert "already checked out" in exc.value.detail


# ---------------------------------------------------------------------------
# return_book
# ---------------------------------------------------------------------------

class TestReturnBook:
    def test_return_success(self, session):
        book = _create_book(session)
        loan = checkout(session, book_id=book.id, user_id=1, librarian_id=2)
        returned = return_book(session, loan_id=loan.id)
        assert returned.return_date is not None

    def test_return_twice_raises(self, session):
        book = _create_book(session)
        loan = checkout(session, book_id=book.id, user_id=1, librarian_id=2)
        return_book(session, loan_id=loan.id)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            return_book(session, loan_id=loan.id)
        assert exc.value.status_code == 400
        assert "already returned" in exc.value.detail

    def test_return_missing_loan(self, session):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            return_book(session, loan_id=9999)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# is_overdue
# ---------------------------------------------------------------------------

class TestIsOverdue:
    def test_returned_book_not_overdue(self, session):
        book = _create_book(session)
        loan = checkout(session, book_id=book.id, user_id=1, librarian_id=2)
        return_book(session, loan_id=loan.id)
        assert is_overdue(loan) is False

    def test_new_loan_not_overdue(self, session):
        book = _create_book(session)
        loan = checkout(session, book_id=book.id, user_id=1, librarian_id=2)
        assert is_overdue(loan) is False

    @patch("src.circulation.datetime")
    def test_overdue_past_due_date(self, mock_dt):
        """Loan with due_date in the past should be overdue."""
        now = datetime(2025, 7, 1, tzinfo=timezone.utc)
        mock_dt.now.return_value = now
        mock_dt.timedelta = timedelta

        loan = Loan(
            book_id=1,
            user_id=1,
            librarian_id=1,
            checkout_date=now - timedelta(days=30),
            due_date=now - timedelta(days=2),  # 2 days past due
            return_date=None,
        )
        assert is_overdue(loan) is True

    @patch("src.circulation.datetime")
    def test_not_overdue_still_within_period(self, mock_dt):
        """Loan with due_date 5 days in the future should not be overdue."""
        now = datetime(2025, 7, 1, tzinfo=timezone.utc)
        mock_dt.now.return_value = now
        mock_dt.timedelta = timedelta

        loan = Loan(
            book_id=1,
            user_id=1,
            librarian_id=1,
            checkout_date=now - timedelta(days=20),
            due_date=now + timedelta(days=5),
            return_date=None,
        )
        assert is_overdue(loan) is False


# ---------------------------------------------------------------------------
# get_user_loans / get_book_loans
# ---------------------------------------------------------------------------

class TestGetUserLoans:
    def test_get_active_loans(self, session):
        book = _create_book(session)
        checkout(session, book_id=book.id, user_id=1, librarian_id=2)
        loans = get_user_loans(session, user_id=1, active_only=True)
        assert len(loans) == 1

    def test_get_all_loans_includes_returned(self, session):
        book = _create_book(session)
        loan = checkout(session, book_id=book.id, user_id=1, librarian_id=2)
        return_book(session, loan_id=loan.id)
        active = get_user_loans(session, user_id=1, active_only=True)
        all_loans = get_user_loans(session, user_id=1, active_only=False)
        assert len(active) == 0
        assert len(all_loans) == 1


class TestGetOverdueLoans:
    def test_overdue_detected(self, session):
        """Create a loan that is past due and verify it shows up."""
        _create_book(session)
        with patch("src.circulation.datetime") as mock_dt:
            now = datetime(2025, 7, 1, tzinfo=timezone.utc)
            mock_dt.now.return_value = now
            mock_dt.timedelta = timedelta

            loan = Loan(
                book_id=1,
                user_id=1,
                librarian_id=2,
                checkout_date=now - timedelta(days=30),
                due_date=now - timedelta(days=2),
                return_date=None,
            )
            session.add(loan)
            session.commit()

            overdue = get_overdue_loans(session)
            assert len(overdue) == 1
            assert overdue[0].id == loan.id

    def test_no_overdue_loans(self, session):
        _create_book(session)
        with patch("src.circulation.datetime") as mock_dt:
            now = datetime(2025, 7, 1, tzinfo=timezone.utc)
            mock_dt.now.return_value = now
            mock_dt.timedelta = timedelta

            loan = Loan(
                book_id=1,
                user_id=1,
                librarian_id=2,
                checkout_date=now - timedelta(days=10),
                due_date=now + timedelta(days=10),
                return_date=None,
            )
            session.add(loan)
            session.commit()

            overdue = get_overdue_loans(session)
            assert len(overdue) == 0


# ---------------------------------------------------------------------------
# get_book_loans
# ---------------------------------------------------------------------------

class TestGetBookLoans:
    def test_get_book_active_loans(self, session):
        book = _create_book(session)
        checkout(session, book_id=book.id, user_id=1, librarian_id=2)
        loans = get_book_loans(session, book_id=book.id, active_only=True)
        assert len(loans) == 1

    def test_book_with_returned_loan(self, session):
        book = _create_book(session)
        loan = checkout(session, book_id=book.id, user_id=1, librarian_id=2)
        return_book(session, loan_id=loan.id)
        active = get_book_loans(session, book_id=book.id, active_only=True)
        all_loans = get_book_loans(session, book_id=book.id, active_only=False)
        assert len(active) == 0
        assert len(all_loans) == 1
