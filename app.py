from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db
from database.queries import insert_expense, get_expense_by_id, update_expense, get_recent_transactions, CATEGORIES

app = Flask(__name__)
app.secret_key = 'spendly-dev-secret'


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not all([name, email, password, confirm_password]):
        flash("All fields are required.", "error")
        return render_template("register.html")

    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return render_template("register.html")

    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("An account with that email already exists.", "error")
            return render_template("register.html")

        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
    finally:
        conn.close()

    flash("Account created! Please sign in.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not all([email, password]):
        flash("All fields are required.", "error")
        return render_template("login.html")

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password.", "error")
        return render_template("login.html")

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    name = session.get("user_name", "User")
    initials = "".join(w[0].upper() for w in name.split()[:2])

    user = {
        "name": name,
        "email": "demo@spendly.com",
        "member_since": "January 2026",
        "initials": initials,
    }
    stats = {
        "total_spent": "5,174",
        "transactions": 8,
        "top_category": "Shopping",
    }
    expenses = get_recent_transactions(session["user_id"])
    categories = [
        {"name": "Shopping",      "amount": "2,200", "pct": 43},
        {"name": "Bills",         "amount": "1,200", "pct": 23},
        {"name": "Entertainment", "amount": "599",   "pct": 12},
        {"name": "Food",          "amount": "630",   "pct": 12},
        {"name": "Health",        "amount": "350",   "pct": 7},
        {"name": "Transport",     "amount": "120",   "pct": 2},
        {"name": "Other",         "amount": "75",    "pct": 1},
    ]
    return render_template("profile.html", user=user, stats=stats, expenses=expenses, categories=categories)


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    today = datetime.today().strftime("%Y-%m-%d")

    if request.method == "GET":
        return render_template("add_expense.html", categories=CATEGORIES, form={}, today=today)

    amount_raw = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date_raw = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip() or None

    form = {
        "amount": amount_raw,
        "category": category,
        "date": date_raw,
        "description": description or "",
    }

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Amount must be a positive number greater than 0.", "error")
        return render_template("add_expense.html", categories=CATEGORIES, form=form, today=today)

    if category not in CATEGORIES:
        flash("Please select a valid category.", "error")
        return render_template("add_expense.html", categories=CATEGORIES, form=form, today=today)

    try:
        datetime.strptime(date_raw, "%Y-%m-%d")
    except ValueError:
        flash("Please enter a valid date.", "error")
        return render_template("add_expense.html", categories=CATEGORIES, form=form, today=today)

    insert_expense(session["user_id"], amount, category, date_raw, description)
    flash("Expense added!", "success")
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    if request.method == "GET":
        form = {
            "amount": expense["amount"],
            "category": expense["category"],
            "date": expense["date"],
            "description": expense["description"] or "",
        }
        return render_template("edit_expense.html", expense=expense, categories=CATEGORIES, form=form)

    amount_raw = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date_raw = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip() or None

    form = {"amount": amount_raw, "category": category, "date": date_raw, "description": description or ""}

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Amount must be a positive number greater than 0.", "error")
        return render_template("edit_expense.html", expense=expense, categories=CATEGORIES, form=form)

    if category not in CATEGORIES:
        flash("Please select a valid category.", "error")
        return render_template("edit_expense.html", expense=expense, categories=CATEGORIES, form=form)

    try:
        datetime.strptime(date_raw, "%Y-%m-%d")
    except ValueError:
        flash("Please enter a valid date.", "error")
        return render_template("edit_expense.html", expense=expense, categories=CATEGORIES, form=form)

    update_expense(id, session["user_id"], amount, category, date_raw, description)
    flash("Expense updated!", "success")
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    init_db()
    seed_db()
    app.run(debug=True, port=5001)


