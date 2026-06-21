"""SQLAlchemy models for Leavely: User, LeaveBalance, LeaveRequest, Holiday."""
from datetime import date as date_, datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # "employee" | "manager" | "superuser"
    manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    location: Mapped[str] = mapped_column(String(80), default="Chennai")
    # Free-text bio shown on the Employees screen (admin/manager directory) —
    # has no effect anywhere else in the app.
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    # Soft-delete flag. An admin "deactivating" someone sets this False rather
    # than deleting the row outright — leave_requests/leave_balances keep a
    # valid user_id to point at, and DELETE /employees/{id} (see main.py) is
    # actually implemented as this same flip, not a real SQL DELETE. Login is
    # blocked while False (see /auth/login).
    is_active: Mapped[bool] = mapped_column(default=True)
    # True right after an admin creates the account with an auto-generated
    # temp password; the frontend forces a password-change screen before
    # showing anything else while this is True (see app.py + /auth/change-password).
    must_change_password: Mapped[bool] = mapped_column(default=False)


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    casual: Mapped[float] = mapped_column(Float, default=10.0)
    sick: Mapped[float] = mapped_column(Float, default=10.0)
    earned: Mapped[float] = mapped_column(Float, default=10.0)
    floating: Mapped[float] = mapped_column(Float, default=2.0)
    # Allowed but deliberately excluded from the balance pie chart (see
    # charts.py PIE_CHART_TYPES) — these are statutory leave pools, not part
    # of the day-to-day discretionary mix the donut is meant to visualize.
    maternity: Mapped[float] = mapped_column(Float, default=180.0)
    paternity: Mapped[float] = mapped_column(Float, default=30.0)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[date_] = mapped_column(Date, index=True)
    type: Mapped[str] = mapped_column(String(20))  # casual | sick | earned | floating | maternity | paternity
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    # full | morning | evening — morning/evening are half-day requests that
    # deduct 0.5 from the balance instead of 1.0.
    session: Mapped[str] = mapped_column(String(10), default="full")
    applied_on: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)


class Holiday(Base):
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date_] = mapped_column(Date, index=True)
    name: Mapped[str] = mapped_column(String(120))
    location: Mapped[str] = mapped_column(String(80), index=True)

    __table_args__ = (UniqueConstraint("date", "location", name="uq_holiday_date_location"),)


class LocationConfig(Base):
    """Per-location (state/country) settings — currently just the floating-
    holiday allotment, since that's the one balance number that legitimately
    varies by location. A superuser adds rows here for new states/countries;
    new users at that location pick up its floating_days as their starting
    balance at seed/creation time."""
    __tablename__ = "location_configs"

    location: Mapped[str] = mapped_column(String(80), primary_key=True)
    country: Mapped[str] = mapped_column(String(80), default="India")
    floating_days: Mapped[int] = mapped_column(Integer, default=2)
