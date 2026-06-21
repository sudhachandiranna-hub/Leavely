"""Leavely — Streamlit entrypoint.

This file only handles page config, session-state, and role-based routing.
All visual styling comes from design_tokens; all business logic lives in
the FastAPI backend, reached through api_client.
"""
import streamlit as st

from design_tokens import apply_design_system
from components.header import render_header
from views.login_view import render_login
from views.change_password_view import render_change_password
from views.employee_view import render_employee_view
from views.manager_view import render_manager_view
from views.superuser_view import render_superuser_view

st.set_page_config(
    page_title="Leavely",
    page_icon="🗓️",
    layout="wide",
    # The nav lives entirely in the sidebar — without it the user can't
    # navigate at all, so it must always start (and stay, see design_tokens'
    # sidebar CSS) expanded rather than Streamlit's default "auto", which
    # remembers a prior collapse and can come back hidden.
    initial_sidebar_state="expanded",
)

if "user" not in st.session_state:
    st.session_state.user = None

apply_design_system()

if st.session_state.user is None:
    render_login()
elif st.session_state.user.get("must_change_password"):
    # No skip path: this is checked before any role view is reached, so it
    # reappears on every rerun until the change actually succeeds (see
    # change_password_view.py).
    render_change_password(st.session_state.user)
else:
    render_header(st.session_state.user)
    role = st.session_state.user.get("role")
    if role == "manager":
        render_manager_view(st.session_state.user)
    elif role == "superuser":
        render_superuser_view(st.session_state.user)
    else:
        render_employee_view(st.session_state.user)
