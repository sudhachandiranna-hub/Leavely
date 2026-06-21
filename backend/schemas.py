"""Pydantic schemas. Payloads are deliberately minimal — IDs and enums only."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str
    manager_id: Optional[int] = None
    location: str
    bio: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False


class BalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    casual: float
    sick: float
    earned: float
    floating: float
    maternity: float
    paternity: float


class LeaveApplyRequest(BaseModel):
    user_id: int
    date: date
    type: str  # casual | sick | earned | floating | maternity | paternity
    session: str = "full"  # full | morning | evening


class LeaveActionRequest(BaseModel):
    decided_by: int


class LeaveRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    date: date
    type: str
    status: str
    session: str = "full"
    applied_on: datetime
    decided_by: Optional[int] = None


class HolidayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date
    name: str
    location: str


class HolidayCreate(BaseModel):
    requested_by: int  # must be a superuser
    date: date
    name: str
    location: str


class LocationConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    location: str
    country: str
    floating_days: int


class LocationConfigCreate(BaseModel):
    requested_by: int  # must be a superuser
    location: str
    country: str = "India"
    floating_days: int = 2


class LocationConfigUpdate(BaseModel):
    requested_by: int  # must be a superuser
    floating_days: int


class CalendarDayOut(BaseModel):
    date: date
    status: str  # pending | approved | rejected | cancelled | holiday
    type: Optional[str] = None
    name: Optional[str] = None
    request_id: Optional[int] = None
    session: Optional[str] = None


class CapacityDayOut(BaseModel):
    date: date
    total: int
    on_leave: int
    available: int


class NotificationOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    date: date
    type: str
    applied_on: datetime


# ---------------------------------------------------------------------------
# Employees (admin/manager directory — see backend/main.py "Employees" section)
# ---------------------------------------------------------------------------

class EmployeeCreate(BaseModel):
    requested_by: int  # must be a superuser
    name: str
    email: str
    role: str  # "employee" | "manager" | "superuser"
    bio: Optional[str] = None
    manager_id: Optional[int] = None
    location: str = "Chennai"


class EmployeeCreateOut(BaseModel):
    """Same shape as UserOut, plus the one-time auto-generated temp password —
    this is the only response that ever carries a plaintext password; it is
    not stored anywhere and can't be retrieved again after this call."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str
    manager_id: Optional[int] = None
    location: str
    bio: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = True
    temp_password: str


class EmployeeUpdate(BaseModel):
    """All fields optional — only the ones actually present in the request
    body are applied (see main.py's use of model_dump(exclude_unset=True)),
    so omitting a field always means 'leave it alone', not 'clear it'.

    requested_by's role decides what's allowed: a superuser may change any
    field; a manager may only change name/bio on their own direct reports
    (role/manager_id/location changes from a non-superuser are rejected with
    a 403 server-side — this is the real boundary, not just a hidden field
    in the UI)."""
    requested_by: int
    name: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None
    manager_id: Optional[int] = None
    location: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    user_id: int
    current_password: str
    new_password: str
