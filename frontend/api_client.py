"""Thin wrapper around the Leavely FastAPI backend. No business logic here —
just HTTP calls and error normalization so views can stay simple.
"""
import os
from functools import lru_cache
from typing import Optional

import requests

API_BASE_URL = os.environ.get("LEAVELY_API_URL", "http://127.0.0.1:8000")
_TIMEOUT = 25  # generous on purpose: free-tier cloud hosts (e.g. Fly.io) suspend
# idle machines and take a few seconds to wake on the first request after a gap
_SESSION = requests.Session()


class APIError(Exception):
    """Raised with a human-readable message extracted from the backend's
    error response, so views can show it directly via st.error(...)."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _request(method: str, path: str, **kwargs):
    url = f"{API_BASE_URL}{path}"
    try:
        resp = _SESSION.request(method, url, timeout=_TIMEOUT, **kwargs)
    except requests.exceptions.ConnectionError:
        raise APIError(
            "Can't reach the Leavely backend. Make sure the API server is running "
            f"at {API_BASE_URL}."
        )
    except requests.exceptions.Timeout:
        raise APIError("The Leavely backend took too long to respond.")

    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except ValueError:
            detail = resp.text
        raise APIError(str(detail), status_code=resp.status_code)

    if resp.status_code == 204 or not resp.content:
        return None
    return resp.json()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login(email: str, password: str) -> dict:
    return _request("POST", "/auth/login", json={"email": email, "password": password})


def change_password(user_id: int, current_password: str, new_password: str) -> dict:
    result = _request(
        "POST", "/auth/change-password",
        json={"user_id": user_id, "current_password": current_password, "new_password": new_password},
    )
    clear_cache()
    return result


def clear_cache():
    get_calendar.cache_clear()
    get_balance.cache_clear()
    list_requests.cache_clear()
    get_team_members.cache_clear()
    get_team_members_with_balances.cache_clear()
    get_team_capacity.cache_clear()
    get_holidays.cache_clear()
    get_locations.cache_clear()
    get_notifications.cache_clear()


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

@lru_cache(maxsize=128)
def get_calendar(user_id: int, month: str) -> list:
    return _request("GET", f"/calendar/{user_id}", params={"month": month})


# ---------------------------------------------------------------------------
# Leave lifecycle
# ---------------------------------------------------------------------------

def apply_leave(user_id: int, date: str, leave_type: str, session: str = "full") -> dict:
    result = _request(
        "POST", "/leave/apply",
        json={"user_id": user_id, "date": date, "type": leave_type, "session": session},
    )
    clear_cache()
    return result


def approve_leave(request_id: int, decided_by: int) -> dict:
    result = _request("PATCH", f"/leave/{request_id}/approve", json={"decided_by": decided_by})
    clear_cache()
    return result


def reject_leave(request_id: int, decided_by: int) -> dict:
    result = _request("PATCH", f"/leave/{request_id}/reject", json={"decided_by": decided_by})
    clear_cache()
    return result


def cancel_leave(request_id: int, decided_by: int) -> dict:
    result = _request("PATCH", f"/leave/{request_id}/cancel", json={"decided_by": decided_by})
    clear_cache()
    return result


@lru_cache(maxsize=128)
def get_balance(user_id: int) -> dict:
    return _request("GET", f"/leave/balance/{user_id}")


@lru_cache(maxsize=128)
def list_requests(user_id: Optional[int] = None, manager_id: Optional[int] = None, status: Optional[str] = None) -> list:
    params = {}
    if user_id is not None:
        params["user_id"] = user_id
    if manager_id is not None:
        params["manager_id"] = manager_id
    if status is not None:
        params["status"] = status
    return _request("GET", "/leave/requests", params=params)


# ---------------------------------------------------------------------------
# Team / manager analytics
# ---------------------------------------------------------------------------

@lru_cache(maxsize=128)
def get_team_members(manager_id: int) -> list:
    return _request("GET", "/team/members", params={"manager_id": manager_id})


@lru_cache(maxsize=128)
def get_team_members_with_balances(manager_id: int) -> list:
    return _request("GET", "/team/members-with-balances", params={"manager_id": manager_id})


@lru_cache(maxsize=128)
def get_team_capacity(manager_id: int, date: Optional[str] = None, month: Optional[str] = None) -> list:
    params = {"manager_id": manager_id}
    if date is not None:
        params["date"] = date
    if month is not None:
        params["month"] = month
    return _request("GET", "/team/capacity", params=params)


# ---------------------------------------------------------------------------
# Holidays
# ---------------------------------------------------------------------------

@lru_cache(maxsize=128)
def get_holidays(location: str) -> list:
    return _request("GET", "/holidays", params={"location": location})


def create_holiday(requested_by: int, date: str, name: str, location: str) -> dict:
    result = _request(
        "POST", "/holidays",
        json={"requested_by": requested_by, "date": date, "name": name, "location": location},
    )
    clear_cache()
    return result


def delete_holiday(holiday_id: int, requested_by: int) -> None:
    result = _request("DELETE", f"/holidays/{holiday_id}", params={"requested_by": requested_by})
    clear_cache()
    return result


# ---------------------------------------------------------------------------
# Locations (superuser-configurable: states/countries + floating-day count)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=128)
def get_locations() -> list:
    return _request("GET", "/locations")


def create_location(requested_by: int, location: str, country: str, floating_days: int) -> dict:
    result = _request(
        "POST", "/locations",
        json={"requested_by": requested_by, "location": location, "country": country, "floating_days": floating_days},
    )
    clear_cache()
    return result


def update_location(location: str, requested_by: int, floating_days: int) -> dict:
    result = _request(
        "PATCH", f"/locations/{location}",
        json={"requested_by": requested_by, "floating_days": floating_days},
    )
    clear_cache()
    return result


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@lru_cache(maxsize=128)
def get_notifications(manager_id: int) -> list:
    return _request("GET", f"/notifications/{manager_id}")


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------

def list_employees(
    role: Optional[str] = None,
    location: Optional[str] = None,
    manager_id: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> list:
    params = {}
    if role is not None:
        params["role"] = role
    if location is not None:
        params["location"] = location
    if manager_id is not None:
        params["manager_id"] = manager_id
    if is_active is not None:
        params["is_active"] = is_active
    return _request("GET", "/employees", params=params)


def get_employee(employee_id: int) -> dict:
    return _request("GET", f"/employees/{employee_id}")


def create_employee(
    requested_by: int, name: str, email: str, role: str,
    bio: str = "", manager_id: Optional[int] = None, location: str = "Chennai",
) -> dict:
    return _request(
        "POST", "/employees",
        json={
            "requested_by": requested_by, "name": name, "email": email, "role": role,
            "bio": bio, "manager_id": manager_id, "location": location,
        },
    )


def update_employee(employee_id: int, requested_by: int, **fields) -> dict:
    """fields: any of name/bio/role/manager_id/location — only pass the ones
    you actually want changed, so the backend's exclude_unset logic leaves
    everything else untouched."""
    payload = {"requested_by": requested_by, **fields}
    return _request("PUT", f"/employees/{employee_id}", json=payload)


def deactivate_employee(employee_id: int, requested_by: int) -> dict:
    return _request("PATCH", f"/employees/{employee_id}/deactivate", params={"requested_by": requested_by})


def reactivate_employee(employee_id: int, requested_by: int) -> dict:
    return _request("PATCH", f"/employees/{employee_id}/reactivate", params={"requested_by": requested_by})


def delete_employee(employee_id: int, requested_by: int) -> dict:
    """Soft delete — see backend/main.py delete_employee. Sets is_active to
    False, the same effect as deactivate_employee above."""
    return _request("DELETE", f"/employees/{employee_id}", params={"requested_by": requested_by})
