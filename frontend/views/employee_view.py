"""Employee view — Calendar, My Requests, Holiday Calendar."""
import streamlit as st

from components.sidebar import render_sidebar
from views.shared_sections import calendar_section, my_requests_section
from views.holiday_view import render_holiday_calendar

NAV_ITEMS = ["Calendar", "My Requests", "Holiday Calendar"]


def render_employee_view(user: dict):
    render_sidebar(NAV_ITEMS, state_key="nav", user=user)
    nav = st.session_state.get("nav", "Calendar")

    if nav == "Calendar":
        calendar_section(user, key_prefix="emp")
    elif nav == "My Requests":
        my_requests_section(user, key_prefix="emp")
    elif nav == "Holiday Calendar":
        render_holiday_calendar(user)
