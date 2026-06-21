"""Superuser view — same personal Calendar/My Requests every role gets,
plus the read-only Holiday Calendar, plus the superuser-exclusive Settings
page (location + holiday administration).

Scope call: a superuser is not automatically a manager — they have no team
here (manager_id is null for everyone, so there's nobody to approve leave
for), so Approve Leave/Notifications/Analytics are intentionally left off
this nav rather than shown empty. Their job is org-wide configuration
(holidays, locations), not people-management.
"""
import streamlit as st

from components.sidebar import render_sidebar
from views.shared_sections import calendar_section, my_requests_section
from views.holiday_view import render_holiday_calendar
from views.settings_view import render_settings
from views.employees_view import render_employees_admin

NAV_ITEMS = ["Calendar", "My Requests", "Holiday Calendar", "Employees", "Settings"]


def render_superuser_view(user: dict):
    render_sidebar(NAV_ITEMS, state_key="nav", user=user)
    nav = st.session_state.get("nav", "Calendar")

    if nav == "Calendar":
        calendar_section(user, key_prefix="su")
    elif nav == "My Requests":
        my_requests_section(user, key_prefix="su")
    elif nav == "Holiday Calendar":
        render_holiday_calendar(user)
    elif nav == "Employees":
        render_employees_admin(user)
    elif nav == "Settings":
        render_settings(user)
