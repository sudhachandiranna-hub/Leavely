"""Seed demo data: one manager, five employees, default balances, a handful
of demo leave requests, and the Chennai holiday calendar from holidays.json.

Run directly: `python -m backend.seed` (re-running is a no-op if users
already exist — pass --reset to wipe and reseed).
"""
import json
import os
import sys
from datetime import date, datetime, timedelta

from .database import SessionLocal, init_db, engine, Base
from .models import User, LeaveBalance, LeaveRequest, Holiday, LocationConfig
from .security import hash_password

HOLIDAYS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "holidays.json")

DEFAULT_FLOATING_DAYS = 2


def _schema_is_stale() -> bool:
    """True if an existing leavely.db predates the current models.py (i.e.
    is missing columns SQLAlchemy's create_all() would never retroactively
    add, since it only creates missing tables — it never alters an existing
    one). Covers the original casual/sick/earned/floating rename, plus the
    later maternity/paternity balance columns and the leave_requests.session
    column. Auto-detecting this lets a developer restart the app and get a
    clean reseed instead of a manual delete step."""
    from sqlalchemy import inspect
    insp = inspect(engine)
    table_names = insp.get_table_names()
    if "leave_balances" not in table_names:
        return False  # brand-new DB, nothing to migrate
    balance_cols = {c["name"] for c in insp.get_columns("leave_balances")}
    if "sick" not in balance_cols or "earned" not in balance_cols:
        return True
    if "maternity" not in balance_cols or "paternity" not in balance_cols:
        return True
    if "leave_requests" in table_names:
        request_cols = {c["name"] for c in insp.get_columns("leave_requests")}
        if "session" not in request_cols:
            return True
    if "users" in table_names:
        user_cols = {c["name"] for c in insp.get_columns("users")}
        if "is_active" not in user_cols or "must_change_password" not in user_cols or "bio" not in user_cols:
            return True
    return False


def _load_holidays(db):
    if db.query(Holiday).count() > 0:
        return
    with open(HOLIDAYS_JSON) as f:
        rows = json.load(f)
    for row in rows:
        db.add(Holiday(
            date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
            name=row["name"],
            location=row["location"],
        ))
    db.commit()


def _load_location_configs(db):
    if db.query(LocationConfig).count() > 0:
        return
    # Seed the three locations we have real holiday data for (see
    # holidays.json). A superuser adds more states/countries from the
    # Settings page — each one starts with the same default floating-day
    # count until edited.
    db.add(LocationConfig(location="Chennai", country="India", floating_days=DEFAULT_FLOATING_DAYS))
    db.add(LocationConfig(location="Bangalore", country="India", floating_days=DEFAULT_FLOATING_DAYS))
    db.add(LocationConfig(location="United States", country="United States", floating_days=DEFAULT_FLOATING_DAYS))
    db.commit()


def _floating_days_for(db, location: str) -> int:
    cfg = db.get(LocationConfig, location)
    return cfg.floating_days if cfg else DEFAULT_FLOATING_DAYS


def _create_user(db, name, email, password, role, manager_id, location="Chennai"):
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        manager_id=manager_id,
        location=location,
    )
    db.add(user)
    db.flush()  # assign id
    db.add(LeaveBalance(
        user_id=user.id,
        casual=10.0,
        sick=10.0,
        earned=10.0,
        floating=float(_floating_days_for(db, location)),
        maternity=180.0,
        paternity=30.0,
    ))
    return user


def _seed_users_and_requests(db):
    if db.query(User).count() > 0:
        return

    manager = _create_user(db, "Asha Krishnan", "manager@leavely.com", "manager123", "manager", None)
    admin = _create_user(db, "Devika", "admin@leavely.com", "admin123", "superuser", None)

    rahul = _create_user(db, "Rahul", "rahul@leavely.com", "employee123", "employee", manager.id)
    priya = _create_user(db, "Priya", "priya@leavely.com", "employee123", "employee", manager.id)
    karthik = _create_user(db, "Karthik Subramanian", "karthik@leavely.com", "employee123", "employee", manager.id)
    divya = _create_user(db, "Divya Raman", "divya@leavely.com", "employee123", "employee", manager.id)
    arjun = _create_user(db, "Arjun", "arjun@leavely.com", "employee123", "employee", manager.id)
    db.commit()

    def apply(user, d, leave_type, status, decided_by=None, applied_offset_days=3):
        req = LeaveRequest(
            user_id=user.id,
            date=d,
            type=leave_type,
            status=status,
            applied_on=datetime.utcnow() - timedelta(days=applied_offset_days),
            decided_by=decided_by,
        )
        db.add(req)
        bal = db.query(LeaveBalance).filter_by(user_id=user.id).first()
        if status in ("pending", "approved"):
            setattr(bal, leave_type, getattr(bal, leave_type) - 1)

    # A representative mix of demo leave requests around "today" (2026-06-20),
    # touching all four leave types.
    apply(rahul, date(2026, 6, 5), "casual", "approved", decided_by=manager.id, applied_offset_days=20)
    apply(rahul, date(2026, 6, 25), "earned", "pending", applied_offset_days=2)
    apply(priya, date(2026, 6, 12), "floating", "approved", decided_by=manager.id, applied_offset_days=10)
    apply(priya, date(2026, 6, 22), "casual", "pending", applied_offset_days=1)
    apply(karthik, date(2026, 6, 8), "earned", "rejected", decided_by=manager.id, applied_offset_days=15)
    apply(karthik, date(2026, 7, 3), "casual", "approved", decided_by=manager.id, applied_offset_days=5)
    apply(divya, date(2026, 6, 30), "floating", "pending", applied_offset_days=1)
    apply(arjun, date(2026, 6, 15), "sick", "approved", decided_by=manager.id, applied_offset_days=6)
    apply(manager, date(2026, 6, 19), "casual", "approved", decided_by=manager.id, applied_offset_days=8)

    db.commit()


def run_seed_if_empty():
    init_db()
    db = SessionLocal()
    try:
        if _schema_is_stale():
            db.close()
            reset_and_seed()
            return
        _load_location_configs(db)
        _load_holidays(db)
        _seed_users_and_requests(db)
    finally:
        db.close()


def reset_and_seed():
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()
    try:
        _load_location_configs(db)
        _load_holidays(db)
        _seed_users_and_requests(db)
    finally:
        db.close()


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset_and_seed()
        print("Database reset and reseeded.")
    else:
        run_seed_if_empty()
        print("Seed complete (no-op if data already existed).")
