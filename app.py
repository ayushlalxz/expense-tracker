from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db

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
    expenses = [
        {"date": "20 May 2026", "description": "Miscellaneous",      "category": "Other",         "amount": "75.00"},
        {"date": "17 May 2026", "description": "Restaurant dinner",  "category": "Food",          "amount": "180.00"},
        {"date": "14 May 2026", "description": "New shoes",          "category": "Shopping",      "amount": "2,200.00"},
        {"date": "10 May 2026", "description": "OTT subscription",   "category": "Entertainment", "amount": "599.00"},
        {"date": "08 May 2026", "description": "Pharmacy",           "category": "Health",        "amount": "350.00"},
        {"date": "05 May 2026", "description": "Electricity bill",   "category": "Bills",         "amount": "1,200.00"},
        {"date": "03 May 2026", "description": "Metro recharge",     "category": "Transport",     "amount": "120.00"},
        {"date": "01 May 2026", "description": "Grocery run",        "category": "Food",          "amount": "450.00"},
    ]
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


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    init_db()
    seed_db()
    app.run(debug=True, port=5001)
