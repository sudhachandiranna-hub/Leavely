"""Settings — superuser-only. Configure locations (states/countries, each
with their own floating-holiday allotment) and the holiday list per
location. The nav item itself is only ever shown to a superuser (see
superuser_view.py), but this view re-checks the role directly too — the
real enforcement lives server-side on the /holidays and /locations
endpoints (see backend/main.py:_require_superuser), so this check is a
courtesy UI guard, not the actual security boundary.

"Add location"/"Add holiday"/"Copy holidays" are buttons above their
table, opening an st.dialog — the same single-action-then-close pattern
already used by components/modals.py's day_dialog (submit -> API call ->
st.rerun(), which closes the dialog and refreshes the table beneath it).
Copy holidays can't show its "N copied, M skipped" result inside the
dialog (rerun closes it), so — like the new-employee temp-password banner
in employees_view.py — that result is stashed in session_state and shown
as a dismissible banner on the page underneath instead.
"""
from datetime import date as date_cls

import streamlit as st

import api_client as api


def render_settings(user: dict):
    if user.get("role") != "superuser":
        st.markdown('<p class="ly-body">Settings is only available to a superuser.</p>', unsafe_allow_html=True)
        return

    st.markdown('<p class="ly-h2" style="margin-bottom:16px;">Settings</p>', unsafe_allow_html=True)

    _locations_section(user)
    st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
    _holidays_section(user)


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

@st.dialog("Add a new location")
def _add_location_dialog(user: dict):
    c1, c2 = st.columns(2)
    with c1:
        new_location = st.text_input("State / city", key="new-location-name", placeholder="e.g. Bengaluru")
    with c2:
        new_country = st.text_input("Country", key="new-location-country", value="India")
    new_floating = st.number_input("Floating days", min_value=0, max_value=30, value=2, key="new-location-floating")

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
    if st.button("Add location", key="add-location-btn", type="primary", use_container_width=True):
        if not new_location.strip():
            st.error("Enter a state or city name.")
        else:
            try:
                api.create_location(
                    requested_by=user["id"],
                    location=new_location.strip(),
                    country=new_country.strip() or "India",
                    floating_days=int(new_floating),
                )
                st.rerun()
            except api.APIError as e:
                st.error(e.message)


def _locations_section(user: dict):
    header_l, header_r = st.columns([4, 1.6], vertical_alignment="center")
    with header_l:
        st.markdown('<p class="ly-h3">Locations</p>', unsafe_allow_html=True)
    with header_r:
        if st.button(
            "Add location", key="open-add-location", type="primary",
            icon=":material/add_location_alt:", use_container_width=True,
        ):
            _add_location_dialog(user)

    st.markdown(
        '<p class="ly-body" style="margin:2px 0 12px 0;">Each location has its own floating-holiday '
        'allotment. New employees at that location pick up this number as their starting balance.</p>',
        unsafe_allow_html=True,
    )

    try:
        locations = api.get_locations()
    except api.APIError as e:
        st.error(e.message)
        locations = []

    for loc in locations:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1.6, 1.6, 1.4])
            with c1:
                st.markdown(f'<p class="ly-body-strong">{loc["location"]}</p>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<p class="ly-body">{loc["country"]}</p>', unsafe_allow_html=True)
            with c3:
                new_days = st.number_input(
                    "Floating days", min_value=0, max_value=30, value=loc["floating_days"],
                    key=f"floating-{loc['location']}", label_visibility="collapsed",
                )
            with c4:
                if st.button("Update", key=f"update-loc-{loc['location']}", use_container_width=True):
                    if new_days != loc["floating_days"]:
                        try:
                            api.update_location(loc["location"], requested_by=user["id"], floating_days=int(new_days))
                            st.success(f"Updated {loc['location']}.")
                            st.rerun()
                        except api.APIError as e:
                            st.error(e.message)
                    else:
                        st.info("No change to save.")

    if not locations:
        st.markdown('<p class="ly-body">No locations configured yet.</p>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Holidays
# ---------------------------------------------------------------------------

@st.dialog("Add a holiday")
def _add_holiday_dialog(user: dict, default_location: str, location_names: list):
    c1, c2 = st.columns(2)
    with c1:
        new_date = st.date_input("Date", value=date_cls.today(), key="new-holiday-date")
    with c2:
        idx = location_names.index(default_location) if default_location in location_names else 0
        new_loc = st.selectbox("Location", options=location_names, key="new-holiday-location", index=idx)
    new_name = st.text_input("Name", key="new-holiday-name", placeholder="e.g. Diwali")

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
    if st.button("Add holiday", key="add-holiday-btn", type="primary", use_container_width=True):
        if not new_name.strip():
            st.error("Enter a holiday name.")
        else:
            try:
                api.create_holiday(
                    requested_by=user["id"], date=new_date.isoformat(),
                    name=new_name.strip(), location=new_loc,
                )
                st.rerun()
            except api.APIError as e:
                st.error(e.message)


@st.dialog("Copy holidays from another location")
def _copy_holidays_dialog(user: dict, target_location: str, location_names: list):
    source_options = [l for l in location_names if l != target_location]
    if not source_options:
        st.markdown('<p class="ly-body">No other locations to copy from yet.</p>', unsafe_allow_html=True)
        return

    st.markdown(
        f'<p class="ly-body">Copy holidays into <strong>{target_location}</strong> from:</p>',
        unsafe_allow_html=True,
    )
    source = st.selectbox("Source location", options=source_options, key="copy-holiday-source", label_visibility="collapsed")

    try:
        source_holidays = api.get_holidays(source)
    except api.APIError as e:
        st.error(e.message)
        source_holidays = []

    if not source_holidays:
        st.markdown(f'<p class="ly-body" style="margin-top:8px;">{source} has no holidays yet.</p>', unsafe_allow_html=True)
        return

    st.markdown(
        f'<p class="ly-body" style="margin:10px 0 6px 0;">{len(source_holidays)} holiday(s) in {source}. '
        f"Any date that already has a holiday in {target_location} is skipped.</p>",
        unsafe_allow_html=True,
    )
    with st.container(height=180, border=True):
        for h in source_holidays:
            st.markdown(
                f'<p class="ly-body" style="margin:2px 0;">{h["date"]} — {h["name"]}</p>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    if st.button(
        f"Copy {len(source_holidays)} holiday(s) to {target_location}",
        key="copy-holidays-submit", type="primary", use_container_width=True,
    ):
        copied, skipped = 0, 0
        for h in source_holidays:
            try:
                api.create_holiday(
                    requested_by=user["id"], date=h["date"], name=h["name"], location=target_location,
                )
                copied += 1
            except api.APIError:
                skipped += 1
        st.session_state["copy_holidays_result"] = {
            "copied": copied, "skipped": skipped, "source": source, "target": target_location,
        }
        st.rerun()


def _copy_result_banner():
    result = st.session_state.get("copy_holidays_result")
    if not result:
        return
    skipped_note = f', skipped {result["skipped"]} that already existed' if result["skipped"] else ""
    with st.container(border=True, key="copy-holidays-result-banner"):
        st.markdown(
            f'<p class="ly-body-strong">Copied {result["copied"]} holiday(s) from '
            f'{result["source"]} to {result["target"]}{skipped_note}.</p>',
            unsafe_allow_html=True,
        )
        if st.button("Dismiss", key="dismiss-copy-holidays-result"):
            del st.session_state["copy_holidays_result"]
            st.rerun()
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)


def _holidays_section(user: dict):
    st.markdown('<p class="ly-h3" style="margin-bottom:10px;">Holidays</p>', unsafe_allow_html=True)

    try:
        locations = api.get_locations()
    except api.APIError as e:
        st.error(e.message)
        locations = []
    location_names = [l["location"] for l in locations] or [user.get("location", "Chennai")]

    c_loc, c_copy, c_add = st.columns([2.4, 1.9, 1.4], vertical_alignment="bottom")
    with c_loc:
        picked = st.selectbox("Location", options=location_names, key="settings-holiday-location")
    with c_copy:
        if st.button(
            "Copy from another location", key="open-copy-holidays",
            icon=":material/content_copy:", use_container_width=True,
        ):
            _copy_holidays_dialog(user, picked, location_names)
    with c_add:
        if st.button(
            "Add holiday", key="open-add-holiday", type="primary",
            icon=":material/event:", use_container_width=True,
        ):
            _add_holiday_dialog(user, picked, location_names)

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    _copy_result_banner()

    try:
        holidays = api.get_holidays(picked)
    except api.APIError as e:
        st.error(e.message)
        holidays = []

    for h in holidays:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 3, 1.2])
            with c1:
                st.markdown(f'<p class="ly-body">{h["date"]}</p>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<p class="ly-body">{h["name"]}</p>', unsafe_allow_html=True)
            with c3:
                if st.button("Remove", key=f"del-holiday-{h['id']}", use_container_width=True):
                    try:
                        api.delete_holiday(h["id"], requested_by=user["id"])
                        st.rerun()
                    except api.APIError as e:
                        st.error(e.message)

    if not holidays:
        st.markdown('<p class="ly-body">No holidays for this location yet.</p>', unsafe_allow_html=True)
