import database.db as db_module
from database.queries import insert_expense, CATEGORIES


def get_demo_user_id():
    conn = db_module.get_db()
    user = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
    conn.close()
    return user["id"]


# ------------------------------------------------------------------ #
# Unit tests — insert_expense                                         #
# ------------------------------------------------------------------ #

def test_insert_expense_with_description(app):
    user_id = get_demo_user_id()
    insert_expense(user_id, 50.0, "Food", "2026-03-20", "Lunch")
    conn = db_module.get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND description = ?",
        (user_id, "Lunch"),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["amount"] == 50.0
    assert row["category"] == "Food"
    assert row["date"] == "2026-03-20"
    assert row["description"] == "Lunch"


def test_insert_expense_none_description(app):
    user_id = get_demo_user_id()
    insert_expense(user_id, 30.0, "Transport", "2026-03-21", None)
    conn = db_module.get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND amount = ? AND date = ?",
        (user_id, 30.0, "2026-03-21"),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["description"] is None


# ------------------------------------------------------------------ #
# Route: GET /expenses/add                                            #
# ------------------------------------------------------------------ #

def test_get_unauthenticated_redirects_to_login(client):
    resp = client.get("/expenses/add")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_get_authenticated_returns_form(auth_client):
    resp = auth_client.get("/expenses/add")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "<form" in body
    assert 'method="POST"' in body
    for cat in CATEGORIES:
        assert cat in body


# ------------------------------------------------------------------ #
# Route: POST /expenses/add                                           #
# ------------------------------------------------------------------ #

def test_post_unauthenticated_redirects_to_login(client):
    resp = client.post("/expenses/add", data={
        "amount": "50.0", "category": "Food", "date": "2026-03-20", "description": "Lunch",
    })
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_post_valid_redirects_to_profile_and_inserts_row(auth_client):
    user_id = get_demo_user_id()
    resp = auth_client.post("/expenses/add", data={
        "amount": "50.0", "category": "Food", "date": "2026-03-20", "description": "Lunch",
    })
    assert resp.status_code == 302
    assert "/profile" in resp.headers["Location"]
    conn = db_module.get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND description = ?",
        (user_id, "Lunch"),
    ).fetchone()
    conn.close()
    assert row is not None


def test_post_missing_amount_rerenders_with_error(auth_client):
    resp = auth_client.post("/expenses/add", data={
        "amount": "", "category": "Food", "date": "2026-03-20",
    })
    assert resp.status_code == 200
    assert b"error" in resp.data.lower() or b"positive" in resp.data.lower()


def test_post_zero_amount_rerenders_with_error(auth_client):
    resp = auth_client.post("/expenses/add", data={
        "amount": "0", "category": "Food", "date": "2026-03-20",
    })
    assert resp.status_code == 200


def test_post_nonnumeric_amount_rerenders_with_error(auth_client):
    resp = auth_client.post("/expenses/add", data={
        "amount": "abc", "category": "Food", "date": "2026-03-20",
    })
    assert resp.status_code == 200


def test_post_invalid_category_rerenders_with_error(auth_client):
    resp = auth_client.post("/expenses/add", data={
        "amount": "50.0", "category": "InvalidCat", "date": "2026-03-20",
    })
    assert resp.status_code == 200


def test_post_invalid_date_rerenders_with_error(auth_client):
    resp = auth_client.post("/expenses/add", data={
        "amount": "50.0", "category": "Food", "date": "not-a-date",
    })
    assert resp.status_code == 200


def test_post_no_description_inserts_null(auth_client):
    user_id = get_demo_user_id()
    resp = auth_client.post("/expenses/add", data={
        "amount": "75.0", "category": "Transport", "date": "2026-03-22", "description": "",
    })
    assert resp.status_code == 302
    assert "/profile" in resp.headers["Location"]
    conn = db_module.get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND amount = ? AND date = ?",
        (user_id, 75.0, "2026-03-22"),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["description"] is None
