# Spec: Login and Logout

## Overview
This step wires up session-based authentication for Spendly. A registered user submits their email and password at `/login`; the app verifies the credentials against the database, stores the user's id and name in Flask's signed session cookie, and redirects to the profile page. The `/logout` route clears the session and redirects to the landing page. The navbar in `base.html` is made context-aware — showing "Sign in / Get started" to guests and a personalised greeting with a logout link to authenticated users.

## Depends on
- Step 01 — Database Setup (`users` table and `get_db()` must be implemented)
- Step 02 — Registration (users must exist in the DB to log in)

## Routes
- `GET /login` — render the login form — public (already exists, stub)
- `POST /login` — validate credentials, set session, redirect — public (new)
- `GET /logout` — clear session, redirect to landing — public (already exists, stub)

## Database changes
No database changes.

## Templates
- **Modify:** `templates/login.html` — remove the `{% if error %}` / `.auth-error` block; flash messages in `base.html` already handle errors
- **Modify:** `templates/base.html` — make the navbar conditional: guests see "Sign in" + "Get started"; logged-in users see their name and a "Sign out" link

## Files to change
- `app.py` — import `session` and `check_password_hash`; implement POST `/login` logic; implement `/logout`
- `templates/login.html` — remove `{% if error %}` block
- `templates/base.html` — conditional navbar using `session`

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords verified with `werkzeug.security.check_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Session keys: `session['user_id']` (integer), `session['user_name']` (string)
- On invalid credentials: flash a single generic error `"Invalid email or password."` — do not distinguish between unknown email and wrong password
- On successful login: `redirect(url_for('profile'))`
- On logout: `session.clear()`, then `redirect(url_for('landing'))`
- Navbar condition: use `{% if session.user_id %}` in `base.html`

## Definition of done
- [ ] Visiting `/login` renders a form with email and password fields
- [ ] Submitting valid credentials sets the session and redirects to `/profile`
- [ ] Submitting an unknown email shows the error flash "Invalid email or password."
- [ ] Submitting a wrong password shows the error flash "Invalid email or password."
- [ ] Submitting blank fields shows the error flash "All fields are required."
- [ ] Visiting `/logout` clears the session and redirects to the landing page (`/`)
- [ ] After logout, visiting `/login` shows no session data
- [ ] Navbar shows "Sign in" and "Get started" when logged out
- [ ] Navbar shows the user's name and a "Sign out" link when logged in
