# Spec: Login UI Change

## Overview
This step gives the login (and registration) page a visual refresh to bring it in line with the polished landing page aesthetic. The current single-column card is functional but plain; this spec replaces it with a two-panel split layout: a branded left panel with Spendly's tagline and a short feature list, and the auth form in the right panel. The register page receives the same treatment for visual consistency. No authentication logic changes — only the HTML structure and CSS are updated.

## Depends on
- Step 01 — Database Setup
- Step 02 — Registration (register.html must exist)
- Step 03 — Login and Logout (login form must be wired to POST /login)
- Step 04 — Profile Page Design (establishes the full CSS variable set and design language)

## Routes
No new routes.

## Database changes
No database changes.

## Templates
- **Modify:** `templates/login.html` — replace the centred single-column layout with a two-panel split (`auth-split`): left branding panel + right form panel. Keep all existing form fields, flash message blocks, and `url_for` references intact.
- **Modify:** `templates/register.html` — apply the same two-panel split layout for visual consistency. Keep all existing form fields and validation logic intact.

## Files to change
- `templates/login.html` — new two-panel HTML structure
- `templates/register.html` — new two-panel HTML structure matching login
- `static/css/style.css` — add `.auth-split`, `.auth-panel-brand`, `.auth-panel-form`, and supporting utility classes; preserve all existing `.auth-*` classes so flash messages and form elements keep their styling

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- The left brand panel must use only CSS variables for colours — no inline styles, no raw hex
- The split layout must collapse to a single column on screens ≤ 700 px (brand panel hidden, form full-width)
- Do not alter any form `name` attributes, action URLs, or flash message rendering logic
- The right form panel must retain the `.auth-card`, `.form-group`, `.form-input`, `.btn-submit`, and `.auth-switch` classes so existing CSS continues to apply
- Brand panel content: Spendly logo/name, one-line tagline, and 3–4 bullet feature highlights (static copy, no JS)

## Definition of done
- [ ] Visiting `/login` shows a two-panel layout: left branding panel visible alongside the form on desktop
- [ ] Visiting `/register` shows the same two-panel layout
- [ ] The brand panel is hidden and the form takes full width on a viewport ≤ 700 px
- [ ] Submitting valid credentials on the updated login page still logs the user in and redirects to `/profile`
- [ ] Submitting invalid credentials still shows the "Invalid email or password." flash message
- [ ] Submitting the registration form still creates an account and redirects to `/login`
- [ ] No hex colour values appear directly in `login.html` or `register.html`
- [ ] The navbar flash container still renders error/success messages correctly above the split layout
