# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the development server (http://localhost:5001)
python app.py

# Run all tests
pytest

# Run a single test file
pytest tests/test_auth.py

# Install dependencies
pip install -r requirements.txt
```

## Architecture

**Spendly** is a Flask web app for personal expense tracking, targeting Indian users (₹ currency). The app is structured as a student learning project with intentional stubs to be implemented.

### Key files

- `app.py` — All Flask routes are defined here. Routes for landing, register, login, logout, profile, and expense CRUD (add/edit/delete) exist but most are stubs awaiting implementation.
- `database/db.py` — Three functions to implement: `get_db()` (SQLite connection with `row_factory` and foreign keys), `init_db()` (CREATE TABLE IF NOT EXISTS), `seed_db()` (sample data). Database file is `expense_tracker.db` (gitignored).
- `templates/` — Jinja2 templates. `base.html` is the shared layout with navbar/footer. Other templates extend it.
- `static/css/style.css` — CSS variables define the full design system (colors, spacing, typography). Modifying variables propagates changes globally.

### Implementation pattern

Routes follow a 9-step progression: database init → user registration → login/session → profile → add expense → edit expense → delete expense → expense listing → filtering. Each step builds on the previous.

### Tech stack

- Flask 3.1.3 + Werkzeug 3.1.6
- SQLite via Python's `sqlite3` module (no ORM)
- Jinja2 templates with vanilla JS
- pytest + pytest-flask for testing
- Fonts: DM Serif Display (headings), DM Sans (body) via Google Fonts
