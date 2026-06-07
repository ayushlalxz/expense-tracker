"""
tests/test_07-add-expense.py

Tests for Step 7: Add Expense feature.
All test logic is derived from .claude/specs/07-add-expense.md — NOT from the implementation.
"""

import pytest
import database.db as db_module
from database.queries import insert_expense

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_CATEGORIES = [
    "Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"
]


def _get_test_user_id(app):
    """Return the id of the seeded demo user."""
    conn = db_module.get_db()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
        ).fetchone()
        return row["id"]
    finally:
        conn.close()


def _fetch_expenses_for_user(user_id):
    """Return all expense rows for *user_id* ordered by id descending."""
    conn = db_module.get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Unit tests — insert_expense
# ---------------------------------------------------------------------------


class TestInsertExpense:
    """Unit tests for the insert_expense query helper."""

    def test_insert_expense_with_description_creates_row(self, app):
        """insert_expense with a description stores the row in the DB."""
        user_id = _get_test_user_id(app)
        before = _fetch_expenses_for_user(user_id)
        before_count = len(before)

        insert_expense(user_id, 50.0, "Food", "2026-03-20", "Lunch")

        after = _fetch_expenses_for_user(user_id)
        assert len(after) == before_count + 1

    def test_insert_expense_with_description_stores_correct_values(self, app):
        """insert_expense stores amount, category, date, and description correctly."""
        user_id = _get_test_user_id(app)

        insert_expense(user_id, 50.0, "Food", "2026-03-20", "Lunch")

        rows = _fetch_expenses_for_user(user_id)
        newest = rows[0]  # ordered DESC
        assert newest["user_id"] == user_id
        assert newest["amount"] == 50.0
        assert newest["category"] == "Food"
        assert newest["date"] == "2026-03-20"
        assert newest["description"] == "Lunch"

    def test_insert_expense_with_none_description_stores_null(self, app):
        """insert_expense with description=None stores NULL in the DB."""
        user_id = _get_test_user_id(app)

        insert_expense(user_id, 50.0, "Food", "2026-03-20", None)

        rows = _fetch_expenses_for_user(user_id)
        newest = rows[0]
        assert newest["description"] is None


# ---------------------------------------------------------------------------
# Route tests — GET /expenses/add
# ---------------------------------------------------------------------------


class TestGetAddExpense:
    """Route tests for GET /expenses/add."""

    def test_get_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated GET /expenses/add redirects to /login with 302."""
        response = client.get("/expenses/add")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_get_authenticated_returns_200(self, auth_client):
        """Authenticated GET /expenses/add returns HTTP 200."""
        response = auth_client.get("/expenses/add")
        assert response.status_code == 200

    def test_get_authenticated_response_contains_form_tag_with_post_method(self, auth_client):
        """Authenticated GET /expenses/add includes a <form with POST method."""
        response = auth_client.get("/expenses/add")
        body = response.data.decode()
        assert "<form" in body
        assert "POST" in body.upper() or "post" in body

    def test_get_authenticated_response_contains_all_seven_categories(self, auth_client):
        """Authenticated GET /expenses/add includes all 7 category options."""
        response = auth_client.get("/expenses/add")
        body = response.data.decode()
        for category in VALID_CATEGORIES:
            assert category in body, f"Category '{category}' not found in response"


# ---------------------------------------------------------------------------
# Route tests — POST /expenses/add
# ---------------------------------------------------------------------------


class TestPostAddExpense:
    """Route tests for POST /expenses/add."""

    # --- authentication guard ---

    def test_post_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated POST /expenses/add redirects to /login with 302."""
        response = client.post(
            "/expenses/add",
            data={
                "amount": "50.0",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    # --- valid submission ---

    def test_post_valid_data_redirects_to_profile(self, auth_client):
        """Authenticated POST with valid data redirects to /profile (302)."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "50.0",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )
        assert response.status_code == 302
        assert "/profile" in response.headers["Location"]

    def test_post_valid_data_inserts_row_in_db(self, app, auth_client):
        """Authenticated POST with valid data inserts a new expense row for the user."""
        user_id = _get_test_user_id(app)
        before_count = len(_fetch_expenses_for_user(user_id))

        auth_client.post(
            "/expenses/add",
            data={
                "amount": "50.0",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )

        after = _fetch_expenses_for_user(user_id)
        assert len(after) == before_count + 1
        newest = after[0]
        assert newest["amount"] == 50.0
        assert newest["category"] == "Food"
        assert newest["date"] == "2026-03-20"
        assert newest["description"] == "Lunch"

    # --- missing amount ---

    def test_post_missing_amount_returns_200(self, auth_client):
        """POST with missing amount re-renders the form (200)."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )
        assert response.status_code == 200

    def test_post_missing_amount_shows_error_message(self, auth_client):
        """POST with missing amount includes an error message in the response."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )
        body = response.data.decode()
        assert any(
            word in body.lower()
            for word in ["error", "amount", "positive", "required", "invalid"]
        ), "Expected an error message about amount in the response"

    # --- amount = 0 ---

    def test_post_zero_amount_returns_200(self, auth_client):
        """POST with amount=0 re-renders the form (200)."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "0",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )
        assert response.status_code == 200

    def test_post_zero_amount_shows_error_message(self, auth_client):
        """POST with amount=0 includes an error message in the response."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "0",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )
        body = response.data.decode()
        assert any(
            word in body.lower()
            for word in ["error", "amount", "positive", "greater", "invalid"]
        ), "Expected an error message about a non-positive amount"

    # --- non-numeric amount ---

    def test_post_non_numeric_amount_returns_200(self, auth_client):
        """POST with a non-numeric amount re-renders the form (200)."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "abc",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )
        assert response.status_code == 200

    def test_post_non_numeric_amount_shows_error_message(self, auth_client):
        """POST with a non-numeric amount includes an error message in the response."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "abc",
                "category": "Food",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )
        body = response.data.decode()
        assert any(
            word in body.lower()
            for word in ["error", "amount", "positive", "number", "invalid"]
        ), "Expected an error message about a non-numeric amount"

    # --- invalid category ---

    def test_post_invalid_category_returns_200(self, auth_client):
        """POST with a category not in the fixed list re-renders the form (200)."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "50.0",
                "category": "InvalidCategory",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )
        assert response.status_code == 200

    def test_post_invalid_category_shows_error_message(self, auth_client):
        """POST with an invalid category includes an error message in the response."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "50.0",
                "category": "InvalidCategory",
                "date": "2026-03-20",
                "description": "Lunch",
            },
        )
        body = response.data.decode()
        assert any(
            word in body.lower()
            for word in ["error", "category", "valid", "invalid"]
        ), "Expected an error message about an invalid category"

    # --- invalid date ---

    def test_post_invalid_date_returns_200(self, auth_client):
        """POST with an invalid date string re-renders the form (200)."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "50.0",
                "category": "Food",
                "date": "not-a-date",
                "description": "Lunch",
            },
        )
        assert response.status_code == 200

    def test_post_invalid_date_shows_error_message(self, auth_client):
        """POST with an invalid date string includes an error message in the response."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "50.0",
                "category": "Food",
                "date": "not-a-date",
                "description": "Lunch",
            },
        )
        body = response.data.decode()
        assert any(
            word in body.lower()
            for word in ["error", "date", "valid", "invalid"]
        ), "Expected an error message about an invalid date"

    # --- no description (optional field) ---

    def test_post_no_description_redirects_to_profile(self, auth_client):
        """POST with no description (optional field) still succeeds and redirects to /profile."""
        response = auth_client.post(
            "/expenses/add",
            data={
                "amount": "50.0",
                "category": "Food",
                "date": "2026-03-20",
                "description": "",
            },
        )
        assert response.status_code == 302
        assert "/profile" in response.headers["Location"]

    def test_post_no_description_stores_null_in_db(self, app, auth_client):
        """POST with no description inserts the row with description = NULL."""
        user_id = _get_test_user_id(app)
        before_count = len(_fetch_expenses_for_user(user_id))

        auth_client.post(
            "/expenses/add",
            data={
                "amount": "50.0",
                "category": "Food",
                "date": "2026-03-20",
                "description": "",
            },
        )

        after = _fetch_expenses_for_user(user_id)
        assert len(after) == before_count + 1
        newest = after[0]
        assert newest["description"] is None
