# Spec: Registration

## Overview
This step implements user account creation for Spendly. A visitor fills in their name, email, and password on the `/register` page; the app validates the input, hashes the password, inserts the row into the `users` table, and redirects to `/login` on success. Flash messages report both success and error states. This is the second step in the roadmap and the first that touches the database from a route.

## Depends on
- Step 01 — Database Setup (`users` table and `get_db()` must be implemented)

## Routes
- `GET /register` — render the registration form — public (already exists, stub)
- `POST /register` — validate form data, insert user, redirect — public (new)

## Database changes
No database changes. The `users` table already exists from Step 01.

## Templates
- **Modify:** `templates/register.html` — add `<form method="POST" action="/register">` with fields: `name`, `email`, `password`, `confirm_password`; display flashed errors/success
- **Modify:** `templates/base.html` — add flash message rendering block (loop over `get_flashed_messages(with_categories=True)`)

## Files to change
- `app.py` — add `secret_key`; import `request`, `redirect`, `url_for`, `flash`; convert `/register` to handle both GET and POST; implement POST logic
- `templates/register.html` — add form markup and flash messages
- `templates/base.html` — add flash messages block

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never use string formatting in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `app.secret_key` must be set (use `os.urandom(24)` or a fixed dev string)
- Validate: name, email, password are non-empty; passwords match; email not already registered
- On duplicate email: flash an error and re-render the form (do not redirect)
- On success: flash a success message and `redirect(url_for('login'))`

## Definition of done
- [ ] Visiting `/register` renders a form with name, email, password, and confirm-password fields
- [ ] Submitting the form with valid unique data inserts a new row into `users` and redirects to `/login`
- [ ] The inserted password is stored as a hash (not plaintext) — verify by querying the DB
- [ ] Submitting with an already-registered email re-renders the form with an error flash message
- [ ] Submitting with mismatched passwords re-renders the form with an error flash message
- [ ] Submitting with any blank field re-renders the form with an error flash message
- [ ] Flash messages are visible in the browser on both success and error paths
