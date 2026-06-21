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

**Employee flow.** Calendar (apply for leave by clicking a date, or click-drag a range for multi-day requests; pick the leave type and, for a single day, a Morning/Evening/Full-day session), My Requests (every request they've ever filed, with status), and Holiday Calendar (public holidays for their location). Leave balance — casual, sick, earned, floating, maternity, paternity — shows alongside the calendar and is reserved the moment a request is filed, restored if it's rejected or cancelled, and stays spent once approved.

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
