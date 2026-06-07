from database.db import get_db

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


def insert_expense(user_id, amount, category, date, description):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_transactions(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, amount, category, date, description"
            " FROM expenses WHERE user_id = ? ORDER BY date DESC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()


def get_expense_by_id(expense_id, user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, user_id, amount, category, date, description"
            " FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id),
        ).fetchone()
    finally:
        conn.close()


def update_expense(expense_id, user_id, amount, category, date, description):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE expenses SET amount=?, category=?, date=?, description=?"
            " WHERE id = ? AND user_id = ?",
            (amount, category, date, description, expense_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()
