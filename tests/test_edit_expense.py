import pytest
import database.db as db_module
from database.queries import get_expense_by_id, update_expense


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def get_demo_user_id(app):
    from database.db import get_db
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
        return row["id"]
    finally:
        conn.close()


def insert_other_user_and_expense(app):
    """Create a second user and an expense owned by them; return (user_id, expense_id)."""
    from database.db import get_db
    from werkzeug.security import generate_password_hash
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Other User", "other@spendly.com", generate_password_hash("pass")),
        )
        conn.commit()
        other_id = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("other@spendly.com",)
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            (other_id, 50.0, "Food", "2026-01-01", "Other's expense"),
        )
        conn.commit()
        exp_id = conn.execute(
            "SELECT id FROM expenses WHERE user_id = ?", (other_id,)
        ).fetchone()["id"]
        return other_id, exp_id
    finally:
        conn.close()


def get_first_demo_expense_id(app):
    from database.db import get_db
    conn = get_db()
    try:
        user_id = get_demo_user_id(app)
        row = conn.execute(
            "SELECT id FROM expenses WHERE user_id = ? LIMIT 1", (user_id,)
        ).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


# ------------------------------------------------------------------ #
# Unit tests — get_expense_by_id                                      #
# ------------------------------------------------------------------ #

class TestGetExpenseById:
    def test_valid_id_correct_user_returns_row(self, app):
        user_id = get_demo_user_id(app)
        exp_id = get_first_demo_expense_id(app)
        row = get_expense_by_id(exp_id, user_id)
        assert row is not None
        assert row["id"] == exp_id

    def test_valid_id_wrong_user_returns_none(self, app):
        exp_id = get_first_demo_expense_id(app)
        row = get_expense_by_id(exp_id, user_id=99999)
        assert row is None

    def test_nonexistent_id_returns_none(self, app):
        row = get_expense_by_id(expense_id=99999, user_id=1)
        assert row is None


# ------------------------------------------------------------------ #
# Unit tests — update_expense                                         #
# ------------------------------------------------------------------ #

class TestUpdateExpense:
    def test_correct_user_updates_row(self, app):
        from database.db import get_db
        user_id = get_demo_user_id(app)
        exp_id = get_first_demo_expense_id(app)
        update_expense(exp_id, user_id, 99.0, "Food", "2026-03-01", "Updated")
        conn = get_db()
        try:
            row = conn.execute("SELECT amount FROM expenses WHERE id = ?", (exp_id,)).fetchone()
        finally:
            conn.close()
        assert row["amount"] == 99.0

    def test_wrong_user_leaves_row_unchanged(self, app):
        from database.db import get_db
        user_id = get_demo_user_id(app)
        exp_id = get_first_demo_expense_id(app)
        conn = get_db()
        try:
            original = conn.execute("SELECT amount FROM expenses WHERE id = ?", (exp_id,)).fetchone()["amount"]
        finally:
            conn.close()
        update_expense(exp_id, user_id=99999, amount=1.0, category="Food", date="2026-01-01", description=None)
        conn = get_db()
        try:
            row = conn.execute("SELECT amount FROM expenses WHERE id = ?", (exp_id,)).fetchone()
        finally:
            conn.close()
        assert row["amount"] == original


# ------------------------------------------------------------------ #
# Route tests — GET /expenses/<id>/edit                               #
# ------------------------------------------------------------------ #

class TestGetEditExpense:
    def test_unauthenticated_redirects_to_login(self, client, app):
        exp_id = get_first_demo_expense_id(app)
        response = client.get(f"/expenses/{exp_id}/edit")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_authenticated_own_expense_returns_200(self, auth_client, app):
        exp_id = get_first_demo_expense_id(app)
        response = auth_client.get(f"/expenses/{exp_id}/edit")
        assert response.status_code == 200

    def test_authenticated_own_expense_form_prepopulated(self, auth_client, app):
        from database.db import get_db
        exp_id = get_first_demo_expense_id(app)
        conn = get_db()
        try:
            expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (exp_id,)).fetchone()
        finally:
            conn.close()
        response = auth_client.get(f"/expenses/{exp_id}/edit")
        body = response.data.decode()
        assert str(expense["amount"]) in body
        assert expense["date"] in body

    def test_authenticated_own_expense_category_preselected(self, auth_client, app):
        from database.db import get_db
        exp_id = get_first_demo_expense_id(app)
        conn = get_db()
        try:
            category = conn.execute("SELECT category FROM expenses WHERE id = ?", (exp_id,)).fetchone()["category"]
        finally:
            conn.close()
        response = auth_client.get(f"/expenses/{exp_id}/edit")
        body = response.data.decode()
        assert f'value="{category}"' in body and "selected" in body

    def test_other_users_expense_returns_404(self, auth_client, app):
        _, other_exp_id = insert_other_user_and_expense(app)
        response = auth_client.get(f"/expenses/{other_exp_id}/edit")
        assert response.status_code == 404

    def test_nonexistent_id_returns_404(self, auth_client, app):
        response = auth_client.get("/expenses/99999/edit")
        assert response.status_code == 404


# ------------------------------------------------------------------ #
# Route tests — POST /expenses/<id>/edit                              #
# ------------------------------------------------------------------ #

class TestPostEditExpense:
    def test_unauthenticated_redirects_to_login(self, client, app):
        exp_id = get_first_demo_expense_id(app)
        response = client.post(f"/expenses/{exp_id}/edit", data={
            "amount": "100", "category": "Food", "date": "2026-05-01", "description": ""
        })
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_valid_data_redirects_to_profile(self, auth_client, app):
        exp_id = get_first_demo_expense_id(app)
        response = auth_client.post(f"/expenses/{exp_id}/edit", data={
            "amount": "123.45", "category": "Food", "date": "2026-05-01", "description": "Updated"
        })
        assert response.status_code == 302
        assert "/profile" in response.headers["Location"]

    def test_valid_data_updates_db(self, auth_client, app):
        from database.db import get_db
        exp_id = get_first_demo_expense_id(app)
        auth_client.post(f"/expenses/{exp_id}/edit", data={
            "amount": "777.77", "category": "Health", "date": "2026-04-10", "description": "Test update"
        })
        conn = get_db()
        try:
            row = conn.execute("SELECT * FROM expenses WHERE id = ?", (exp_id,)).fetchone()
        finally:
            conn.close()
        assert row["amount"] == 777.77
        assert row["category"] == "Health"

    def test_other_users_expense_returns_404(self, auth_client, app):
        _, other_exp_id = insert_other_user_and_expense(app)
        response = auth_client.post(f"/expenses/{other_exp_id}/edit", data={
            "amount": "100", "category": "Food", "date": "2026-05-01", "description": ""
        })
        assert response.status_code == 404

    def test_missing_amount_rerenders_form(self, auth_client, app):
        exp_id = get_first_demo_expense_id(app)
        response = auth_client.post(f"/expenses/{exp_id}/edit", data={
            "amount": "", "category": "Food", "date": "2026-05-01", "description": ""
        })
        assert response.status_code == 200
        assert b"error" in response.data.lower() or b"positive" in response.data.lower()

    def test_zero_amount_rerenders_form(self, auth_client, app):
        exp_id = get_first_demo_expense_id(app)
        response = auth_client.post(f"/expenses/{exp_id}/edit", data={
            "amount": "0", "category": "Food", "date": "2026-05-01", "description": ""
        })
        assert response.status_code == 200

    def test_nonnumeric_amount_rerenders_form(self, auth_client, app):
        exp_id = get_first_demo_expense_id(app)
        response = auth_client.post(f"/expenses/{exp_id}/edit", data={
            "amount": "abc", "category": "Food", "date": "2026-05-01", "description": ""
        })
        assert response.status_code == 200

    def test_invalid_category_rerenders_form(self, auth_client, app):
        exp_id = get_first_demo_expense_id(app)
        response = auth_client.post(f"/expenses/{exp_id}/edit", data={
            "amount": "100", "category": "InvalidCat", "date": "2026-05-01", "description": ""
        })
        assert response.status_code == 200

    def test_invalid_date_rerenders_form(self, auth_client, app):
        exp_id = get_first_demo_expense_id(app)
        response = auth_client.post(f"/expenses/{exp_id}/edit", data={
            "amount": "100", "category": "Food", "date": "not-a-date", "description": ""
        })
        assert response.status_code == 200

    def test_no_description_saves_null(self, auth_client, app):
        from database.db import get_db
        exp_id = get_first_demo_expense_id(app)
        response = auth_client.post(f"/expenses/{exp_id}/edit", data={
            "amount": "55.0", "category": "Food", "date": "2026-05-01", "description": ""
        })
        assert response.status_code == 302
        conn = get_db()
        try:
            row = conn.execute("SELECT description FROM expenses WHERE id = ?", (exp_id,)).fetchone()
        finally:
            conn.close()
        assert row["description"] is None
