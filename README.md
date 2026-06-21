# Leavely

Employee Leave Management System — FastAPI backend + SQLite, Streamlit frontend.

## Quick start

From the `Leavely` project root:

```
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

(Use a virtual environment if you prefer: `python -m venv venv && venv\Scripts\activate` on Windows.)

**1. Start the backend** (so the `backend` package resolves):

```
uvicorn backend.main:app --reload --port 8000
```

The database (`backend/leavely.db`) and demo data are created automatically on first startup — no separate seed step. To wipe and reseed manually: `python -m backend.seed --reset`. If you have an old `leavely.db` from before a schema change, the backend detects the stale schema on startup and auto-reseeds — you'll lose accumulated demo data, but you won't hit a crash.

**2. Start the frontend** (in a second terminal, from the project root):

```
streamlit run frontend/app.py
```

Opens at `http://localhost:8501`. It expects the backend at `http://127.0.0.1:8000` by default; if the backend runs elsewhere, set `LEAVELY_API_URL` first:

```
set LEAVELY_API_URL=http://127.0.0.1:8000   (Windows)
streamlit run frontend/app.py
```

## Demo accounts

| Role      | Email                  | Password      |
|-----------|-------------------------|---------------|
| Superuser | admin@leavely.com       | admin123      |
| Manager   | manager@leavely.com     | manager123    |
| Employee  | rahul@leavely.com       | employee123   |
| Employee  | priya@leavely.com       | employee123   |
| Employee  | karthik@leavely.com     | employee123   |
| Employee  | divya@leavely.com       | employee123   |
| Employee  | arjun@leavely.com       | employee123   |

## How it works

Three roles, three sets of screens. Everyone signs in from the same login page; what you see next depends on your role.

**First login for a new hire.** When an admin adds an employee, the system generates a temporary password and shows it to the admin once (it isn't emailed — copy it and hand it over directly). The new hire logs in with that temp password and is dropped straight into a forced "change your password" screen with no way to skip it; only after setting a real password do they reach their normal home screen. The same flow applies to anyone an admin re-adds or whose password is reset.

**Employee flow.** Calendar (apply for leave by clicking a date, or click-drag a range for multi-day requests; pick the leave type and, for a single day, or multiple days, My Requests (every request they've ever filed, with status), and Holiday Calendar (public holidays for their location). Leave balance — casual, sick, earned, floating, maternity, paternity — shows alongside the calendar and is reserved the moment a request is filed, restored if it's rejected or cancelled, and stays spent once approved.

**Manager flow.** Everything an employee gets, plus:
- *Approve Leave* — every pending request from their direct reports, grouped into one row per continuous date range (a 3-day request is one row with Approve/Reject, not three).
- *Notifications* — a feed of who just asked for what, newest first, with a one-click jump into Approve Leave to act on it.
- *Analytics* — team size, who's out today, a month-long capacity bar chart, and a per-person breakdown of remaining balance by leave type.
- *Employees* — the manager's own direct reports only. A manager can edit a report's name and bio; anything else (role, manager, location) is locked down — that's an admin-only change, enforced by the backend itself (a manager hitting the API directly to change a restricted field gets a 403, not just a hidden button).

**Admin (superuser) flow.** Calendar / My Requests / Holiday Calendar like everyone else (an admin has no manager and isn't anyone's direct report, so no Approve Leave / Notifications / Analytics — those are a people-manager's job), plus the two screens only an admin sees:
- *Employees* — the full company directory, every role, with filters by manager/location/role/active status. Add a new employee (name, bio, role, manager, location — any role, including another manager or admin), edit any field on anyone, and deactivate/reactivate. Deactivating is always a soft action: the record stays, `is_active` flips to false, and the person can no longer log in. There is no hard delete anywhere in the system, including the `DELETE` endpoint — it performs the same soft deactivation.
- *Settings* — manage locations (states/countries) and each one's floating-day allotment, and manage the holiday list per location. "Add location" and "Add holiday" are buttons above their tables that open a small form; "Copy holidays from another location" lets you pick a source location and copy its entire holiday list into the current one in one click, skipping any date that's already covered so you never end up with duplicates.

## Leave types & balances

Every user starts with: casual 10, sick 10, earned 10, and floating days per their location's configuration (2 by default, editable per location from Settings). Maternity (180 days) and paternity (30 days) are separate statutory pools, not part of the day-to-day mix.

## Notes

- Status colors (pending/approved/cancelled/rejected/holiday) are reserved exclusively for leave-status indicators throughout the UI; leave *type* (casual/sick/earned/floating) has its own separate color set so the two are never confused at a glance.
- Every admin-only and manager-only action is enforced server-side (403 if you're not allowed), not just hidden in the UI — the screens reflect what the backend will actually let you do.
- If the SQLite file's default location ever causes locking issues on your machine, point it elsewhere with `LEAVELY_DB_PATH=C:\path\to\leavely.db` before starting the backend. Likewise, if you're running the frontend against a backend on a non-default port, set `LEAVELY_API_URL` before starting Streamlit.


# SMTP Email Setup Guide

## Overview

Leavely sends emails for:

* Temporary passwords
* Employee onboarding

If SMTP is not configured, the application will display:

```text
WARNING:root:SMTP config missing; skipping temporary password email
```

This means the application is running correctly, but email delivery is disabled.

---

# Prerequisites

Install required Python packages:

```bash
pip install python-dotenv
```

---

# SMTP Configuration

The application reads SMTP settings from environment variables.

## Required Variables

| Variable              | Description          |
| --------------------- | -------------------- |
| LEAVELY_SMTP_HOST     | SMTP server hostname |
| LEAVELY_SMTP_PORT     | SMTP server port     |
| LEAVELY_SMTP_USER     | SMTP username        |
| LEAVELY_SMTP_PASSWORD | SMTP password        |

## Optional Variables

| Variable             | Description             |
| -------------------- | ----------------------- |
| LEAVELY_EMAIL_FROM   | Sender email address    |
| LEAVELY_SMTP_TIMEOUT | SMTP timeout in seconds |

Default timeout:

```text
10
```

---

# Gmail SMTP Configuration

## SMTP Settings

```env
LEAVELY_SMTP_HOST=smtp.gmail.com
LEAVELY_SMTP_PORT=587
LEAVELY_SMTP_USER=your-email@gmail.com
LEAVELY_SMTP_PASSWORD=your-app-password
LEAVELY_EMAIL_FROM=your-email@gmail.com
```

## Important

Google no longer allows standard Gmail passwords for SMTP authentication.

You must:

1. Enable Two-Factor Authentication (2FA)
2. Generate an App Password
3. Use the App Password as LEAVELY_SMTP_PASSWORD

If App Passwords are unavailable for your account, use an alternative SMTP provider such as Brevo or SendGrid.

---

# Brevo SMTP Configuration (Recommended)

Brevo offers a free SMTP service suitable for development and MVP deployments.

## SMTP Settings

```env
LEAVELY_SMTP_HOST=smtp-relay.brevo.com
LEAVELY_SMTP_PORT=587
LEAVELY_SMTP_USER=your-brevo-login
LEAVELY_SMTP_PASSWORD=your-brevo-smtp-key
LEAVELY_EMAIL_FROM=no-reply@yourdomain.com
```

---

# Create a .env File

Create a file named:

```text
.env
```

Add the SMTP configuration:

```env
LEAVELY_SMTP_HOST=smtp.gmail.com
LEAVELY_SMTP_PORT=587
LEAVELY_SMTP_USER=your-email@gmail.com
LEAVELY_SMTP_PASSWORD=your-password
LEAVELY_EMAIL_FROM=your-email@gmail.com
```

---

# Load Environment Variables

Add the following code during application startup:

```python
from dotenv import load_dotenv

load_dotenv()
```

Example:

```python
from dotenv import load_dotenv
import os

load_dotenv()

smtp_host = os.getenv("LEAVELY_SMTP_HOST")
smtp_port = os.getenv("LEAVELY_SMTP_PORT")
smtp_user = os.getenv("LEAVELY_SMTP_USER")
smtp_password = os.getenv("LEAVELY_SMTP_PASSWORD")
```

---

# Verify Configuration

Run:

```python
import os

print(os.getenv("LEAVELY_SMTP_HOST"))
print(os.getenv("LEAVELY_SMTP_USER"))
```

Expected output:

```text
smtp.gmail.com
your-email@gmail.com
```

---

# Local Development

Start the application after setting environment variables:

```bash
streamlit run app.py
```

or

```bash
python app.py
```

depending on your startup command.

---

# Streamlit Cloud Deployment

Add SMTP credentials under:

Settings → Secrets

Example:

```toml
LEAVELY_SMTP_HOST="smtp.gmail.com"
LEAVELY_SMTP_PORT="587"
LEAVELY_SMTP_USER="your-email@gmail.com"
LEAVELY_SMTP_PASSWORD="your-app-password"
LEAVELY_EMAIL_FROM="your-email@gmail.com"
```

Do not commit passwords or SMTP credentials to GitHub.

---

# Troubleshooting

## SMTP Config Missing

Error:

```text
WARNING:root:SMTP config missing
```

Resolution:

* Verify environment variables exist
* Verify .env file is loaded
* Restart the application

---

## Authentication Failed

Error:

```text
SMTPAuthenticationError
```

Resolution:

* Verify SMTP username
* Verify SMTP password
* Use App Password for Gmail
* Check SMTP provider credentials

---

## Emails Not Received

Check:

* Spam folder
* SMTP logs
* Sender address configuration
* SMTP provider dashboard

---

# Security Best Practices

* Never hardcode SMTP passwords.
* Store credentials in environment variables.
* Use a dedicated sender account.
* Rotate SMTP credentials periodically.
* Do not commit .env files to source control.

Add the following to .gitignore:

```gitignore
.env
```
