"""Leavely backend — FastAPI + SQLite.

Run: uvicorn backend.main:app --reload --port 8000   (from the project root)
"""
import calendar as cal
import logging
import os
import secrets
import smtplib
from datetime import date as date_cls, datetime
from email.message import EmailMessage
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# Load backend/../.env (project root) before anything below reads os.environ —
# this must run before the `.database` import, since database.py reads
# LEAVELY_DB_PATH at module load time. Without this, LEAVELY_SMTP_* and
# friends only exist if they were `set` manually in the exact terminal that
# launched uvicorn, which is the bug that made SMTP silently never send.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import get_db
from .models import Holiday, LeaveBalance, LeaveRequest, LocationConfig, User
from .schemas import (
    BalanceOut,
    CalendarDayOut,
    CapacityDayOut,
    ChangePasswordRequest,
    EmployeeCreate,
    EmployeeCreateOut,
    EmployeeUpdate,
    HolidayCreate,
    HolidayOut,
    LeaveActionRequest,
    LeaveApplyRequest,
    LeaveRequestOut,
    LocationConfigCreate,
    LocationConfigOut,
    LocationConfigUpdate,
    LoginRequest,
    NotificationOut,
    TeamMemberBalanceOut,
    UserOut,
)
from .security import hash_password, verify_password
from .seed import run_seed_if_empty

VALID_LEAVE_TYPES = ("casual", "sick", "earned", "floating", "maternity", "paternity")
VALID_SESSIONS = ("full", "morning", "evening")
VALID_ROLES = ("employee", "manager", "superuser")


def _leave_units(session: str) -> float:
    """Half a day for morning/evening, a full day otherwise."""
    return 0.5 if session in ("morning", "evening") else 1.0

app = FastAPI(title="Leavely API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    run_seed_if_empty()


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


def _get_request_or_404(db: Session, request_id: int) -> LeaveRequest:
    req = db.get(LeaveRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found.")
    return req


def _team_ids(db: Session, manager_id: int) -> List[int]:
    return [u.id for u in db.query(User).filter(User.manager_id == manager_id).all()]


def _require_superuser(db: Session, user_id: int) -> User:
    """Real server-side enforcement (not just a hidden nav item) for the
    holiday/location config endpoints — anyone who isn't a superuser gets a
    403 even if they call the API directly."""
    user = _get_user_or_404(db, user_id)
    if user.role != "superuser":
        raise HTTPException(status_code=403, detail="Only a superuser can do this.")
    return user


def _floating_days_for(db: Session, location: str) -> int:
    """Mirrors seed.py's _floating_days_for — a new employee's starting
    floating balance comes from their location's configured allotment, or
    the global default of 2 if that location has no LocationConfig row."""
    cfg = db.get(LocationConfig, location)
    return cfg.floating_days if cfg else 2


def _smtp_configured() -> bool:
    return bool(os.environ.get("LEAVELY_SMTP_HOST")) and bool(os.environ.get("LEAVELY_SMTP_USER")) and bool(os.environ.get("LEAVELY_SMTP_PASSWORD"))


def _send_temporary_password_email(email: str, temp_password: str) -> None:
    """Send the new user their temporary password by email."""
    smtp_host = os.environ.get("LEAVELY_SMTP_HOST")
    smtp_port = int(os.environ.get("LEAVELY_SMTP_PORT", "587"))
    smtp_user = os.environ.get("LEAVELY_SMTP_USER")
    smtp_password = os.environ.get("LEAVELY_SMTP_PASSWORD")
    from_address = os.environ.get("LEAVELY_EMAIL_FROM", "no-reply@leavely.com")
    smtp_timeout = float(os.environ.get("LEAVELY_SMTP_TIMEOUT", "10"))

    message = EmailMessage()
    message["Subject"] = "Your Leavely account has been created"
    message["From"] = from_address
    message["To"] = email
    message.set_content(
        f"Hello,\n\n"
        f"An account has been created for you in Leavely. Use the temporary password below to log in:\n\n"
        f"Temporary password: {temp_password}\n\n"
        "You will be asked to set a new password after you log in.\n\n"
        "If you did not expect this email, please contact your administrator.\n"
    )

    try:
        if smtp_port == 465:
            smtp = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=smtp_timeout)
        else:
            smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=smtp_timeout)

        with smtp:
            smtp.ehlo()
            if smtp_port != 465 and smtp.has_extn("STARTTLS"):
                smtp.starttls()
                smtp.ehlo()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)
    except Exception as exc:
        logging.error(
            "Failed to send temporary password email to %s via %s:%s: %s",
            email,
            smtp_host,
            smtp_port,
            exc,
            exc_info=True,
        )
        raise


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/auth/login", response_model=UserOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated. Contact your administrator.")
    return user


@app.post("/auth/change-password", response_model=UserOut)
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, payload.user_id)
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

@app.get("/calendar/{user_id}", response_model=List[CalendarDayOut])
def get_calendar(user_id: int, month: str = Query(..., description="YYYY-MM"), db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    try:
        year, mon = (int(p) for p in month.split("-"))
        start = date_cls(year, mon, 1)
        end = date_cls(year, mon, cal.monthrange(year, mon)[1])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="month must be in YYYY-MM format.")

    days: dict[date_cls, CalendarDayOut] = {}

    holidays = (
        db.query(Holiday)
        .filter(Holiday.location == user.location, Holiday.date >= start, Holiday.date <= end)
        .all()
    )
    for h in holidays:
        days[h.date] = CalendarDayOut(date=h.date, status="holiday", name=h.name)

    requests_ = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.user_id == user_id, LeaveRequest.date >= start, LeaveRequest.date <= end)
        .all()
    )
    for r in requests_:
        days[r.date] = CalendarDayOut(
            date=r.date, status=r.status, type=r.type, request_id=r.id, session=r.session
        )

    return sorted(days.values(), key=lambda d: d.date)


# ---------------------------------------------------------------------------
# Leave lifecycle
# ---------------------------------------------------------------------------

@app.post("/leave/apply", response_model=LeaveRequestOut)
def apply_leave(payload: LeaveApplyRequest, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, payload.user_id)

    if payload.type not in VALID_LEAVE_TYPES:
        raise HTTPException(status_code=400, detail=f"type must be one of {VALID_LEAVE_TYPES}.")

    if payload.session not in VALID_SESSIONS:
        raise HTTPException(status_code=400, detail=f"session must be one of {VALID_SESSIONS}.")

    holiday = (
        db.query(Holiday)
        .filter(Holiday.location == user.location, Holiday.date == payload.date)
        .first()
    )
    if holiday:
        raise HTTPException(status_code=400, detail="This is an existing holiday for your location.")

    duplicate = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.user_id == user.id,
            LeaveRequest.date == payload.date,
            LeaveRequest.status.in_(["pending", "approved"]),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=400, detail="A leave request already exists for this date.")

    balance = db.query(LeaveBalance).filter_by(user_id=user.id).first()
    remaining = getattr(balance, payload.type)
    units = _leave_units(payload.session)
    if remaining < units:
        raise HTTPException(status_code=400, detail=f"Insufficient {payload.type} balance.")

    req = LeaveRequest(
        user_id=user.id,
        date=payload.date,
        type=payload.type,
        status="pending",
        session=payload.session,
        applied_on=datetime.utcnow(),
    )
    db.add(req)
    setattr(balance, payload.type, remaining - units)
    db.commit()
    db.refresh(req)
    return req


@app.patch("/leave/{request_id}/approve", response_model=LeaveRequestOut)
def approve_leave(request_id: int, payload: LeaveActionRequest, db: Session = Depends(get_db)):
    req = _get_request_or_404(db, request_id)
    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot approve a request that is already {req.status}.")
    req.status = "approved"
    req.decided_by = payload.decided_by
    db.commit()
    db.refresh(req)
    return req


@app.patch("/leave/{request_id}/reject", response_model=LeaveRequestOut)
def reject_leave(request_id: int, payload: LeaveActionRequest, db: Session = Depends(get_db)):
    req = _get_request_or_404(db, request_id)
    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot reject a request that is already {req.status}.")
    req.status = "rejected"
    req.decided_by = payload.decided_by
    balance = db.query(LeaveBalance).filter_by(user_id=req.user_id).first()
    setattr(balance, req.type, getattr(balance, req.type) + _leave_units(req.session))
    db.commit()
    db.refresh(req)
    return req


@app.patch("/leave/{request_id}/cancel", response_model=LeaveRequestOut)
def cancel_leave(request_id: int, payload: LeaveActionRequest, db: Session = Depends(get_db)):
    req = _get_request_or_404(db, request_id)
    if req.status not in ("pending", "approved"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel a request that is already {req.status}.")
    req.status = "cancelled"
    req.decided_by = payload.decided_by
    balance = db.query(LeaveBalance).filter_by(user_id=req.user_id).first()
    setattr(balance, req.type, getattr(balance, req.type) + _leave_units(req.session))
    db.commit()
    db.refresh(req)
    return req


@app.get("/leave/balance/{user_id}", response_model=BalanceOut)
def get_balance(user_id: int, db: Session = Depends(get_db)):
    _get_user_or_404(db, user_id)
    balance = db.query(LeaveBalance).filter_by(user_id=user_id).first()
    if not balance:
        raise HTTPException(status_code=404, detail="Leave balance not found.")
    return balance


@app.get("/leave/requests", response_model=List[LeaveRequestOut])
def list_requests(
    user_id: Optional[int] = None,
    manager_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(LeaveRequest)
    if user_id is not None:
        q = q.filter(LeaveRequest.user_id == user_id)
    if manager_id is not None:
        q = q.filter(LeaveRequest.user_id.in_(_team_ids(db, manager_id)))
    if status is not None:
        q = q.filter(LeaveRequest.status == status)
    return q.order_by(LeaveRequest.date.desc()).all()


# ---------------------------------------------------------------------------
# Team / manager analytics
# ---------------------------------------------------------------------------

@app.get("/team/members", response_model=List[UserOut])
def get_team_members(manager_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.manager_id == manager_id).all()


@app.get("/team/members-with-balances", response_model=List[TeamMemberBalanceOut])
def get_team_members_with_balances(manager_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(User, LeaveBalance)
        .outerjoin(LeaveBalance, User.id == LeaveBalance.user_id)
        .filter(User.manager_id == manager_id)
        .all()
    )
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "manager_id": user.manager_id,
            "location": user.location,
            "bio": user.bio,
            "is_active": user.is_active,
            "must_change_password": user.must_change_password,
            "casual": balance.casual if balance else 0.0,
            "sick": balance.sick if balance else 0.0,
            "earned": balance.earned if balance else 0.0,
            "floating": balance.floating if balance else 0.0,
            "maternity": balance.maternity if balance else 0.0,
            "paternity": balance.paternity if balance else 0.0,
        }
        for user, balance in rows
    ]


@app.get("/team/capacity", response_model=List[CapacityDayOut])
def team_capacity(
    manager_id: int,
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    month: Optional[str] = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
):
    team_ids = _team_ids(db, manager_id)
    total = len(team_ids)

    if date is not None:
        try:
            d = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="date must be in YYYY-MM-DD format.")
        n = (
            db.query(func.count(LeaveRequest.id))
            .filter(
                LeaveRequest.user_id.in_(team_ids),
                LeaveRequest.date == d,
                LeaveRequest.status == "approved",
            )
            .scalar()
        ) if team_ids else 0
        return [CapacityDayOut(date=d, total=total, on_leave=n, available=total - n)]

    if month is not None:
        try:
            year, mon = (int(p) for p in month.split("-"))
        except ValueError:
            raise HTTPException(status_code=400, detail="month must be in YYYY-MM format.")
        days_in_month = cal.monthrange(year, mon)[1]
        start = date_cls(year, mon, 1)
        end = date_cls(year, mon, days_in_month)

        counts = {}
        if team_ids:
            rows = (
                db.query(LeaveRequest.date, func.count(LeaveRequest.id).label("on_leave"))
                .filter(
                    LeaveRequest.user_id.in_(team_ids),
                    LeaveRequest.date >= start,
                    LeaveRequest.date <= end,
                    LeaveRequest.status == "approved",
                )
                .group_by(LeaveRequest.date)
                .all()
            )
            counts = {row.date: row.on_leave for row in rows}

        out = []
        for day_num in range(1, days_in_month + 1):
            d = date_cls(year, mon, day_num)
            n = counts.get(d, 0)
            out.append(CapacityDayOut(date=d, total=total, on_leave=n, available=total - n))
        return out

    raise HTTPException(status_code=400, detail="Provide either date or month.")


# ---------------------------------------------------------------------------
# Holidays
# ---------------------------------------------------------------------------

@app.get("/holidays", response_model=List[HolidayOut])
def get_holidays(location: str, db: Session = Depends(get_db)):
    return db.query(Holiday).filter(Holiday.location == location).order_by(Holiday.date).all()


@app.post("/holidays", response_model=HolidayOut)
def create_holiday(payload: HolidayCreate, db: Session = Depends(get_db)):
    _require_superuser(db, payload.requested_by)
    existing = (
        db.query(Holiday)
        .filter(Holiday.date == payload.date, Holiday.location == payload.location)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="A holiday already exists for this date and location.")
    holiday = Holiday(date=payload.date, name=payload.name, location=payload.location)
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday


@app.delete("/holidays/{holiday_id}")
def delete_holiday(holiday_id: int, requested_by: int = Query(...), db: Session = Depends(get_db)):
    _require_superuser(db, requested_by)
    holiday = db.get(Holiday, holiday_id)
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found.")
    db.delete(holiday)
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Locations (per-state/country config — currently just floating-day count)
# ---------------------------------------------------------------------------

@app.get("/locations", response_model=List[LocationConfigOut])
def get_locations(db: Session = Depends(get_db)):
    return db.query(LocationConfig).order_by(LocationConfig.location).all()


@app.post("/locations", response_model=LocationConfigOut)
def create_location(payload: LocationConfigCreate, db: Session = Depends(get_db)):
    _require_superuser(db, payload.requested_by)
    existing = db.get(LocationConfig, payload.location)
    if existing:
        raise HTTPException(status_code=400, detail="This location is already configured.")
    loc = LocationConfig(location=payload.location, country=payload.country, floating_days=payload.floating_days)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@app.patch("/locations/{location}", response_model=LocationConfigOut)
def update_location(location: str, payload: LocationConfigUpdate, db: Session = Depends(get_db)):
    _require_superuser(db, payload.requested_by)
    loc = db.get(LocationConfig, location)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found.")
    loc.floating_days = payload.floating_days
    db.commit()
    db.refresh(loc)
    return loc


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@app.get("/notifications/{manager_id}", response_model=List[NotificationOut])
def get_notifications(manager_id: int, db: Session = Depends(get_db)):
    team_ids = _team_ids(db, manager_id)
    if not team_ids:
        return []
    pending = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.user_id.in_(team_ids), LeaveRequest.status == "pending")
        .order_by(LeaveRequest.applied_on.desc())
        .all()
    )
    out = []
    for r in pending:
        u = db.get(User, r.user_id)
        out.append(
            NotificationOut(
                id=r.id,
                employee_id=u.id,
                employee_name=u.name,
                date=r.date,
                type=r.type,
                applied_on=r.applied_on,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Employees — admin-wide directory + a manager's-own-team view. One flexible
# GET with query filters covers "get all / by manager / by location / by
# role" rather than four separate endpoint paths for the same underlying
# data, matching how /leave/requests and /team/members already filter via
# query params elsewhere in this file.
# ---------------------------------------------------------------------------

@app.get("/employees", response_model=List[UserOut])
def list_employees(
    role: Optional[str] = None,
    location: Optional[str] = None,
    manager_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if role is not None:
        q = q.filter(User.role == role)
    if location is not None:
        q = q.filter(User.location == location)
    if manager_id is not None:
        q = q.filter(User.manager_id == manager_id)
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    return q.order_by(User.name).all()


@app.get("/employees/{employee_id}", response_model=UserOut)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    return _get_user_or_404(db, employee_id)


@app.post("/employees", response_model=EmployeeCreateOut)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    _require_superuser(db, payload.requested_by)

    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {VALID_ROLES}.")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    if payload.manager_id is not None:
        manager = db.get(User, payload.manager_id)
        if not manager:
            raise HTTPException(status_code=404, detail="manager_id does not refer to an existing user.")
        if manager.role != "manager":
            raise HTTPException(status_code=400, detail="manager_id must refer to a user with role 'manager'.")

    # Auto-generated, shown once in the response below, never stored or
    # retrievable in plaintext again — the employee must change it on first
    # login (must_change_password=True; enforced by the frontend, see app.py).
    temp_password = secrets.token_urlsafe(6)
    user = User(
        name=payload.name.strip(),
        email=payload.email.strip(),
        password_hash=hash_password(temp_password),
        role=payload.role,
        manager_id=payload.manager_id,
        location=payload.location,
        bio=(payload.bio or "").strip() or None,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.flush()  # assign id before the LeaveBalance row references it

    # Mirrors seed.py's _create_user — every user needs a balance row or
    # /leave/balance/{id} (and the whole apply-leave flow) 404s for them.
    db.add(LeaveBalance(
        user_id=user.id,
        casual=10.0,
        sick=10.0,
        earned=10.0,
        floating=float(_floating_days_for(db, payload.location)),
        maternity=180.0,
        paternity=30.0,
    ))

    if _smtp_configured():
        try:
            _send_temporary_password_email(payload.email.strip(), temp_password)
        except Exception as exc:
            logging.warning(
                "Unable to send temporary password email to %s; created user anyway. SMTP error: %s",
                payload.email.strip(),
                exc,
                exc_info=True,
            )
    else:
        logging.warning(
            "SMTP config missing; skipping temporary password email for %s.",
            payload.email.strip(),
        )

    db.commit()
    db.refresh(user)

    return EmployeeCreateOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        manager_id=user.manager_id,
        location=user.location,
        bio=user.bio,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        temp_password=temp_password,
    )


@app.put("/employees/{employee_id}", response_model=UserOut)
def update_employee(employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    target = _get_user_or_404(db, employee_id)
    requester = _get_user_or_404(db, payload.requested_by)

    fields = payload.model_dump(exclude_unset=True)
    fields.pop("requested_by", None)

    is_admin = requester.role == "superuser"
    if not is_admin:
        # A manager may only touch their own direct reports, and only
        # name/bio — role, manager re-assignment, and location stay
        # superuser-only. Enforced here, not just hidden in the UI.
        if not (requester.role == "manager" and target.manager_id == requester.id):
            raise HTTPException(status_code=403, detail="You can only edit your own direct reports.")
        restricted = set(fields) - {"name", "bio"}
        if restricted:
            raise HTTPException(
                status_code=403,
                detail=f"A manager can only edit name/bio. Not allowed to change: {', '.join(sorted(restricted))}.",
            )

    if "role" in fields and fields["role"] not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {VALID_ROLES}.")

    if "manager_id" in fields and fields["manager_id"] is not None:
        manager = db.get(User, fields["manager_id"])
        if not manager:
            raise HTTPException(status_code=404, detail="manager_id does not refer to an existing user.")
        if manager.role != "manager":
            raise HTTPException(status_code=400, detail="manager_id must refer to a user with role 'manager'.")

    for key, value in fields.items():
        if key == "name" and isinstance(value, str):
            value = value.strip()
        elif key == "bio" and isinstance(value, str):
            value = value.strip() or None
        setattr(target, key, value)

    db.commit()
    db.refresh(target)
    return target


@app.patch("/employees/{employee_id}/deactivate", response_model=UserOut)
def deactivate_employee(employee_id: int, requested_by: int = Query(...), db: Session = Depends(get_db)):
    _require_superuser(db, requested_by)
    target = _get_user_or_404(db, employee_id)
    target.is_active = False
    db.commit()
    db.refresh(target)
    return target


@app.patch("/employees/{employee_id}/reactivate", response_model=UserOut)
def reactivate_employee(employee_id: int, requested_by: int = Query(...), db: Session = Depends(get_db)):
    """Not explicitly requested, but deactivation without a way back would
    be a one-way trap with no UI path to undo a mistaken deactivation —
    added so admin isn't stuck needing direct DB access to reverse it."""
    _require_superuser(db, requested_by)
    target = _get_user_or_404(db, employee_id)
    target.is_active = True
    db.commit()
    db.refresh(target)
    return target


@app.delete("/employees/{employee_id}", response_model=UserOut)
def delete_employee(employee_id: int, requested_by: int = Query(...), db: Session = Depends(get_db)):
    """Deliberately implemented as a soft delete (is_active=False), the same
    action as /deactivate above — not a real SQL DELETE. A hard delete would
    orphan/violate the leave_requests and leave_balances foreign keys that
    point at this user_id and would erase their leave history permanently;
    this preserves both while still blocking login (see /auth/login)."""
    _require_superuser(db, requested_by)
    target = _get_user_or_404(db, employee_id)
    target.is_active = False
    db.commit()
    db.refresh(target)
    return target
