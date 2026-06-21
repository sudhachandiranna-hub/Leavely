"""Employees — admin-wide directory (full CRUD) and a manager's own-team
view (edit name/bio on direct reports only). Both render functions live
here since they share almost all row/table/dialog code; the real
permission boundary is enforced server-side (backend/main.py update_employee),
not by what this file chooses to show — a manager calling the API directly
with a disallowed field still gets a 403.

Dialogs in this file follow the exact pattern already established in
components/modals.py (day_dialog, range_apply_dialog): a button click opens
the dialog directly, every action inside it is a single submit -> API call
-> st.rerun() (closing it and refreshing the underlying list), no dialog
tries to show a second screen after success. The one exception is the new
employee's one-time temp password, which can't be shown that way (the
dialog closes immediately on rerun) — it's stashed in session_state and
rendered as a persistent banner on the main page instead, dismissed
explicitly by the admin.
"""
import streamlit as st

import api_client as api
from design_tokens import avatar_html, holiday_tag_html, COLORS

ROLE_LABELS = {"employee": "Employee", "manager": "Manager", "superuser": "Admin"}
ROLE_BADGE_COLORS = {
    "employee": COLORS["navy_500"],
    "manager": COLORS["data_blue"],
    "superuser": COLORS["navy"],
}
ROLE_OPTIONS = ["employee", "manager", "superuser"]
NO_MANAGER = "— No manager —"


def _role_pill(role: str) -> str:
    return holiday_tag_html(ROLE_LABELS.get(role, (role or "").capitalize()), ROLE_BADGE_COLORS.get(role, COLORS["muted"]))


def _status_pill(is_active: bool) -> str:
    return (
        holiday_tag_html("Active", COLORS["status_approved"]) if is_active
        else holiday_tag_html("Inactive", COLORS["status_rejected"])
    )


def _managers_list(exclude_id: int = None) -> list:
    try:
        mgrs = api.list_employees(role="manager", is_active=True)
    except api.APIError:
        mgrs = []
    if exclude_id is not None:
        mgrs = [m for m in mgrs if m["id"] != exclude_id]
    return mgrs


def _locations_list() -> list:
    try:
        locs = [l["location"] for l in api.get_locations()]
    except api.APIError:
        locs = []
    return locs or ["Chennai"]


def _manager_name_map(managers: list) -> dict:
    return {m["id"]: m["name"] for m in managers}


# ---------------------------------------------------------------------------
# Add employee (admin only)
# ---------------------------------------------------------------------------

@st.dialog("Add employee")
def _add_employee_dialog(user: dict):
    st.markdown('<p class="ly-modal-field-label">Name</p>', unsafe_allow_html=True)
    name = st.text_input("Name", key="add-emp-name", label_visibility="collapsed", placeholder="Full name")
    st.markdown('<p class="ly-modal-field-label">Email</p>', unsafe_allow_html=True)
    email = st.text_input("Email", key="add-emp-email", label_visibility="collapsed", placeholder="name@leavely.com")
    st.markdown('<p class="ly-modal-field-label">Bio</p>', unsafe_allow_html=True)
    bio = st.text_area("Bio", key="add-emp-bio", label_visibility="collapsed", placeholder="Short personal bio (optional)", height=80)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<p class="ly-modal-field-label">Role</p>', unsafe_allow_html=True)
        role = st.selectbox(
            "Role", options=ROLE_OPTIONS, format_func=lambda r: ROLE_LABELS[r],
            key="add-emp-role", label_visibility="collapsed",
        )
    with c2:
        st.markdown('<p class="ly-modal-field-label">Location</p>', unsafe_allow_html=True)
        locations = _locations_list()
        location = st.selectbox("Location", options=locations, key="add-emp-location", label_visibility="collapsed")

    managers = _managers_list()
    st.markdown('<p class="ly-modal-field-label">Manager</p>', unsafe_allow_html=True)
    mgr_options = [NO_MANAGER] + [m["name"] for m in managers]
    mgr_pick = st.selectbox("Manager", options=mgr_options, key="add-emp-manager", label_visibility="collapsed")
    manager_id = None
    if mgr_pick != NO_MANAGER:
        manager_id = next(m["id"] for m in managers if m["name"] == mgr_pick)

    st.markdown(
        '<div class="ly-modal-note">A temporary password is generated automatically. '
        "It's shown once after you create the account — share it with them directly. "
        "They'll be asked to set their own password the first time they log in.</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    if st.button("Create employee", key="add-emp-submit", type="primary", use_container_width=True):
        if not name.strip() or not email.strip():
            st.error("Name and email are required.")
        else:
            try:
                created = api.create_employee(
                    requested_by=user["id"], name=name.strip(), email=email.strip(),
                    role=role, bio=bio.strip(), manager_id=manager_id, location=location,
                )
                st.session_state["new_employee_creds"] = {
                    "name": created["name"], "email": created["email"],
                    "temp_password": created["temp_password"],
                }
                st.rerun()
            except api.APIError as e:
                st.error(e.message)


def _new_employee_banner():
    creds = st.session_state.get("new_employee_creds")
    if not creds:
        return
    with st.container(border=True, key="new-emp-creds-banner"):
        st.markdown(
            f'<p class="ly-body-strong">{creds["name"]} was added.</p>'
            f'<p class="ly-body" style="margin-top:4px;">Temporary password for {creds["email"]} — '
            "shown once, share it with them directly:</p>",
            unsafe_allow_html=True,
        )
        st.code(creds["temp_password"], language=None)
        st.markdown(
            '<p class="ly-caption" style="text-transform:none;">They\'ll be asked to set a new '
            "password the first time they log in.</p>",
            unsafe_allow_html=True,
        )
        if st.button("Dismiss", key="dismiss-new-emp-creds"):
            del st.session_state["new_employee_creds"]
            st.rerun()
    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Edit employee (admin: all fields. manager: name/bio only on own reports)
# ---------------------------------------------------------------------------

@st.dialog("Edit employee")
def _edit_employee_dialog(user: dict, employee: dict, full_access: bool):
    st.markdown('<p class="ly-modal-field-label">Name</p>', unsafe_allow_html=True)
    name = st.text_input(
        "Name", key=f"edit-emp-name-{employee['id']}", label_visibility="collapsed", value=employee["name"],
    )
    st.markdown('<p class="ly-modal-field-label">Bio</p>', unsafe_allow_html=True)
    bio = st.text_area(
        "Bio", key=f"edit-emp-bio-{employee['id']}", label_visibility="collapsed",
        value=employee.get("bio") or "", height=80,
    )

    role, manager_id, location = employee["role"], employee.get("manager_id"), employee["location"]

    if full_access:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<p class="ly-modal-field-label">Role</p>', unsafe_allow_html=True)
            role = st.selectbox(
                "Role", options=ROLE_OPTIONS, format_func=lambda r: ROLE_LABELS[r],
                key=f"edit-emp-role-{employee['id']}", label_visibility="collapsed",
                index=ROLE_OPTIONS.index(employee["role"]),
            )
        with c2:
            st.markdown('<p class="ly-modal-field-label">Location</p>', unsafe_allow_html=True)
            locations = _locations_list()
            loc_index = locations.index(employee["location"]) if employee["location"] in locations else 0
            location = st.selectbox(
                "Location", options=locations, key=f"edit-emp-location-{employee['id']}",
                label_visibility="collapsed", index=loc_index,
            )

        managers = _managers_list(exclude_id=employee["id"])
        st.markdown('<p class="ly-modal-field-label">Manager</p>', unsafe_allow_html=True)
        mgr_options = [NO_MANAGER] + [m["name"] for m in managers]
        name_by_id = _manager_name_map(managers)
        current_mgr_name = name_by_id.get(employee.get("manager_id"), NO_MANAGER)
        mgr_pick = st.selectbox(
            "Manager", options=mgr_options, key=f"edit-emp-manager-{employee['id']}",
            label_visibility="collapsed", index=mgr_options.index(current_mgr_name) if current_mgr_name in mgr_options else 0,
        )
        manager_id = None
        if mgr_pick != NO_MANAGER:
            manager_id = next(m["id"] for m in managers if m["name"] == mgr_pick)
    else:
        st.markdown(
            '<div class="ly-modal-note">As a manager, you can update name and bio only. '
            "Role, manager, and location changes need an admin.</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    if st.button("Save changes", key=f"edit-emp-submit-{employee['id']}", type="primary", use_container_width=True):
        if not name.strip():
            st.error("Name can't be empty.")
        else:
            try:
                if full_access:
                    api.update_employee(
                        employee["id"], requested_by=user["id"], name=name.strip(),
                        bio=bio.strip(), role=role, manager_id=manager_id, location=location,
                    )
                else:
                    api.update_employee(
                        employee["id"], requested_by=user["id"], name=name.strip(), bio=bio.strip(),
                    )
                st.rerun()
            except api.APIError as e:
                st.error(e.message)


# ---------------------------------------------------------------------------
# Admin: full directory
# ---------------------------------------------------------------------------

def render_employees_admin(user: dict):
    header_l, header_r = st.columns([5, 1.6], vertical_alignment="center")
    with header_l:
        st.markdown('<p class="ly-h2">Employees</p>', unsafe_allow_html=True)
    with header_r:
        if st.button("Add employee", key="open-add-emp", type="primary", icon=":material/person_add:", use_container_width=True):
            _add_employee_dialog(user)

    _new_employee_banner()

    try:
        all_employees = api.list_employees()
    except api.APIError as e:
        st.error(e.message)
        all_employees = []
    managers_by_id = _manager_name_map(all_employees)
    locations = sorted({e["location"] for e in all_employees}) or _locations_list()

    f1, f2, f3 = st.columns(3)
    with f1:
        role_filter = st.selectbox(
            "Role", options=["All"] + ROLE_OPTIONS, format_func=lambda r: "All roles" if r == "All" else ROLE_LABELS[r],
            key="emp-filter-role",
        )
    with f2:
        loc_filter = st.selectbox("Location", options=["All"] + locations, key="emp-filter-location")
    with f3:
        status_filter = st.selectbox("Status", options=["All", "Active", "Inactive"], key="emp-filter-status")

    rows = all_employees
    if role_filter != "All":
        rows = [e for e in rows if e["role"] == role_filter]
    if loc_filter != "All":
        rows = [e for e in rows if e["location"] == loc_filter]
    if status_filter != "All":
        want_active = status_filter == "Active"
        rows = [e for e in rows if e["is_active"] == want_active]
    rows = sorted(rows, key=lambda e: e["name"])

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    if not rows:
        st.markdown('<p class="ly-body">No employees match these filters.</p>', unsafe_allow_html=True)
        return

    for e in rows:
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([2.6, 1.3, 1.4, 1.6, 1, 1.2], vertical_alignment="center")
            with c1:
                st.markdown(
                    f'<div class="ly-member-row">{avatar_html(e["name"], size=32)}'
                    f'<span class="info"><span class="ly-body-strong">{e["name"]}</span>'
                    f'<span class="ly-caption" style="text-transform:none;">{e["email"]}</span></span></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(_role_pill(e["role"]), unsafe_allow_html=True)
            with c3:
                st.markdown(f'<p class="ly-body">{e["location"]}</p>', unsafe_allow_html=True)
            with c4:
                mgr_name = managers_by_id.get(e.get("manager_id"), "—")
                st.markdown(f'<p class="ly-body">{mgr_name}</p>', unsafe_allow_html=True)
            with c5:
                st.markdown(_status_pill(e["is_active"]), unsafe_allow_html=True)
            with c6:
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("Edit", key=f"edit-emp-{e['id']}", use_container_width=True):
                        _edit_employee_dialog(user, e, full_access=True)
                with bc2:
                    is_self = e["id"] == user["id"]
                    if e["is_active"]:
                        # Icon-only, same fix as the calendar's prev/next-month
                        # buttons: "Deactivate" doesn't fit this half-width
                        # column without wrapping/overflowing. The row already
                        # names the employee and shows their status pill, so a
                        # toggle_off glyph + tooltip carries the action without
                        # needing the label to fit.
                        if st.button(
                            " ", key=f"deactivate-emp-{e['id']}", use_container_width=True,
                            icon=":material/toggle_off:", disabled=is_self,
                            help="You can't deactivate your own account." if is_self else "Deactivate",
                        ):
                            try:
                                api.deactivate_employee(e["id"], requested_by=user["id"])
                                st.rerun()
                            except api.APIError as err:
                                st.error(err.message)
                    else:
                        if st.button(
                            " ", key=f"reactivate-emp-{e['id']}", use_container_width=True,
                            icon=":material/toggle_on:", help="Reactivate",
                        ):
                            try:
                                api.reactivate_employee(e["id"], requested_by=user["id"])
                                st.rerun()
                            except api.APIError as err:
                                st.error(err.message)


# ---------------------------------------------------------------------------
# Manager: own direct reports only
# ---------------------------------------------------------------------------

def render_employees_manager(user: dict):
    st.markdown('<p class="ly-h2" style="margin-bottom:4px;">Employees</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ly-body" style="margin-bottom:16px;">Your direct reports. You can update their '
        "name and bio — role, manager, and location changes need an admin.</p>",
        unsafe_allow_html=True,
    )

    try:
        reports = api.list_employees(manager_id=user["id"])
    except api.APIError as e:
        st.error(e.message)
        reports = []
    reports = sorted(reports, key=lambda e: e["name"])

    if not reports:
        st.markdown('<p class="ly-body">No one reports to you yet.</p>', unsafe_allow_html=True)
        return

    for e in reports:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 1.4, 1.4, 1], vertical_alignment="center")
            with c1:
                st.markdown(
                    f'<div class="ly-member-row">{avatar_html(e["name"], size=32)}'
                    f'<span class="info"><span class="ly-body-strong">{e["name"]}</span>'
                    f'<span class="ly-caption" style="text-transform:none;">{e["email"]}</span></span></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(_role_pill(e["role"]), unsafe_allow_html=True)
            with c3:
                st.markdown(_status_pill(e["is_active"]), unsafe_allow_html=True)
            with c4:
                if st.button("Edit", key=f"mgr-edit-emp-{e['id']}", use_container_width=True):
                    _edit_employee_dialog(user, e, full_access=False)
