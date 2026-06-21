"""Manager view — Calendar, My Requests, Approve Leave, Notifications,
Analytics. Calendar/My Requests reuse the exact same sections as the
employee view (a manager's own leave works identically); the remaining
three sections are manager-only."""
from datetime import date as date_cls, datetime as datetime_cls

import streamlit as st

import api_client as api
from design_tokens import badge_html, kpi_tile_html, avatar_html, card_open, CARD_CLOSE, COLORS, type_chip_html
from components.sidebar import render_sidebar
from components.charts import team_capacity_bar
from views.shared_sections import calendar_section, my_requests_section, group_consecutive_requests, block_date_label, SESSION_SUFFIX
from views.holiday_view import render_holiday_calendar
from views.employees_view import render_employees_manager

NAV_ITEMS = ["Calendar", "My Requests", "Approve Leave", "Notifications", "Analytics", "Holiday Calendar", "Employees"]

# Small inline Material-style icons (24x24, stroke=currentColor) for section
# headers — kept local since they're presentation details of this one view,
# not reusable tokens.
_ICON_CAPACITY = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M3 3v18h18"/><path d="M7 16l4-5 3 3 5-7"/></svg>'
)
_ICON_TEAM = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
    '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
)
_ICON_BELL = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M6 8a6 6 0 0 1 12 0c0 4 1.5 5.5 2 6.5H4c.5-1 2-2.5 2-6.5"/>'
    '<path d="M10.5 19a1.5 1.5 0 0 0 3 0"/></svg>'
)


def _relative_applied_label(applied_on_iso: str) -> str:
    """'2026-06-19T10:00:00' -> 'Applied yesterday' etc. Falls back to the
    raw date if the timestamp doesn't parse, rather than raising — this is
    a cosmetic label, not something that should ever break the page."""
    try:
        applied_dt = datetime_cls.fromisoformat(applied_on_iso)
    except (ValueError, TypeError):
        return f"Applied {str(applied_on_iso)[:10]}"
    days = (date_cls.today() - applied_dt.date()).days
    if days <= 0:
        return "Applied today"
    if days == 1:
        return "Applied yesterday"
    return f"Applied {days} days ago"


def _section_header_html(icon: str, title: str) -> str:
    return (
        f'<div class="ly-section-header"><span class="ico">{icon}</span>'
        f'<span class="ly-h3">{title}</span></div>'
    )


def render_manager_view(user: dict):
    render_sidebar(NAV_ITEMS, state_key="nav", user=user)
    nav = st.session_state.get("nav", "Calendar")

    if nav == "Calendar":
        calendar_section(user, key_prefix="mgr")
    elif nav == "My Requests":
        my_requests_section(user, key_prefix="mgr")
    elif nav == "Approve Leave":
        _approve_leave_section(user)
    elif nav == "Notifications":
        _notifications_section(user)
    elif nav == "Analytics":
        _analytics_section(user)
    elif nav == "Holiday Calendar":
        render_holiday_calendar(user)
    elif nav == "Employees":
        render_employees_manager(user)


def _approve_leave_section(user: dict):
    st.markdown('<p class="ly-h2" style="margin-bottom:16px;">Approve Leave</p>', unsafe_allow_html=True)
    try:
        pending = api.list_requests(manager_id=user["id"], status="pending")
    except api.APIError as e:
        st.error(e.message)
        pending = []

    if not pending:
        st.markdown('<p class="ly-body">No pending requests.</p>', unsafe_allow_html=True)
        return

    try:
        members = {m["id"]: m["name"] for m in api.get_team_members(user["id"])}
    except api.APIError:
        members = {}

    # Same grouping used in My Requests: a 3-day apply is 3 backend rows,
    # shown here as a single row with a date range and one Approve/Reject
    # pair that decides every day in the block at once.
    blocks = group_consecutive_requests(pending)

    for b in blocks:
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1.8, 1.4, 1.4, 1, 1])
            with c1:
                st.markdown(f'<p class="ly-body-strong">{members.get(b["user_id"], "—")}</p>', unsafe_allow_html=True)
            with c2:
                suffix = SESSION_SUFFIX.get(b["session"], "")
                st.markdown(
                    f'<p class="ly-body">{block_date_label(b)}</p>'
                    f'<p class="ly-caption" style="text-transform:none; color:{COLORS["muted"]};">'
                    f'{b["day_count"]} day{"s" if b["day_count"] > 1 else ""}{suffix}</p>',
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(f'<p class="ly-body">{b["type"].capitalize()}</p>', unsafe_allow_html=True)
            with c4:
                st.markdown(badge_html(b["status"]), unsafe_allow_html=True)
            with c5:
                if st.button("Approve", key=f"appr-{b['ids'][0]}", type="primary", use_container_width=True):
                    try:
                        for rid in b["ids"]:
                            api.approve_leave(rid, decided_by=user["id"])
                        st.rerun()
                    except api.APIError as e:
                        st.error(e.message)
            with c6:
                if st.button("Reject", key=f"rej-{b['ids'][0]}", use_container_width=True):
                    try:
                        for rid in b["ids"]:
                            api.reject_leave(rid, decided_by=user["id"])
                        st.rerun()
                    except api.APIError as e:
                        st.error(e.message)


def _notifications_section(user: dict):
    st.markdown(_section_header_html(_ICON_BELL, "Notifications"), unsafe_allow_html=True)

    try:
        notes = api.get_notifications(user["id"])
    except api.APIError as e:
        st.error(e.message)
        notes = []

    if not notes:
        with st.container(border=True):
            st.markdown(
                '<div style="text-align:center; padding:32px 0;">'
                f'<p class="ly-h3" style="margin-bottom:4px;">All caught up</p>'
                f'<p class="ly-body" style="color:{COLORS["muted"]};">'
                'No pending requests from your team need your review right now.</p>'
                '</div>',
                unsafe_allow_html=True,
            )
        return

    count_label = f'{len(notes)} request{"s" if len(notes) != 1 else ""}'
    st.markdown(
        f'<p class="ly-body" style="margin:2px 0 18px 0;">'
        f'<strong>{count_label}</strong> from your team awaiting your review, newest first.</p>',
        unsafe_allow_html=True,
    )

    for n in notes:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2.6, 1.7, 1.7, 1.3], vertical_alignment="center")
            with c1:
                leave_date = date_cls.fromisoformat(n["date"]).strftime("%d %b %Y")
                st.markdown(
                    f'<div class="ly-member-row">{avatar_html(n["employee_name"], size=34)}'
                    f'<span class="info"><span class="ly-body-strong">{n["employee_name"]}</span>'
                    f'<span class="ly-caption" style="text-transform:none; color:{COLORS["muted"]};">'
                    f'Leave for {leave_date}</span></span></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(type_chip_html(n["type"].capitalize(), "leave", n["type"]), unsafe_allow_html=True)
            with c3:
                st.markdown(
                    f'<p class="ly-caption" style="text-transform:none; color:{COLORS["muted"]};">'
                    f'{_relative_applied_label(n["applied_on"])}</p>',
                    unsafe_allow_html=True,
                )
            with c4:
                if st.button(
                    "Review", key=f"notif-review-{n['id']}",
                    icon=":material/task_alt:", use_container_width=True,
                ):
                    # Jumps to Approve Leave (where this request lives,
                    # grouped with the rest) rather than duplicating
                    # Approve/Reject actions here — one place to decide,
                    # this screen is for surfacing what needs attention.
                    st.session_state["nav"] = "Approve Leave"
                    st.rerun()


def _analytics_section(user: dict):
    st.markdown('<p class="ly-h2" style="margin-bottom:16px;">Analytics</p>', unsafe_allow_html=True)
    today = date_cls.today()
    month_str = f"{today.year:04d}-{today.month:02d}"

    try:
        capacity_days = api.get_team_capacity(user["id"], month=month_str)
    except api.APIError as e:
        st.error(e.message)
        capacity_days = []

    try:
        members = api.get_team_members(user["id"])
    except api.APIError:
        members = []

    team_size = len(members)
    today_capacity = next((d for d in capacity_days if d["date"] == today.isoformat()), None)
    on_leave_today = today_capacity["on_leave"] if today_capacity else 0

    # Accent each tile a different color (navy/amber/green) — round 1 had
    # three visually identical cards with no way to scan them at a glance;
    # the accent bar gives each metric its own identity without adding
    # more elements.
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(kpi_tile_html("Team size", str(team_size), accent=COLORS["navy"]), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_tile_html("On leave today", str(on_leave_today), accent=COLORS["status_pending"]), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_tile_html("Available today", str(team_size - on_leave_today), accent=COLORS["status_approved"]), unsafe_allow_html=True)

    st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)

    if capacity_days:
        st.markdown(card_open(), unsafe_allow_html=True)
        st.markdown(_section_header_html(_ICON_CAPACITY, "Team capacity this month"), unsafe_allow_html=True)
        st.plotly_chart(team_capacity_bar(capacity_days), use_container_width=True, key="capacity-bar")
        st.markdown(CARD_CLOSE, unsafe_allow_html=True)
    else:
        st.markdown('<p class="ly-body">No team members yet.</p>', unsafe_allow_html=True)

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    if not members:
        st.markdown('<p class="ly-body">No team members yet.</p>', unsafe_allow_html=True)
        return

    st.markdown(_section_header_html(_ICON_TEAM, "Per-resource availability"), unsafe_allow_html=True)

    try:
        approved_requests = api.list_requests(manager_id=user["id"], status="approved")
    except api.APIError:
        approved_requests = []
    on_leave_ids_today = {r["user_id"] for r in approved_requests if r["date"] == today.isoformat()}

    for m in members:
        try:
            bal = api.get_balance(m["id"])
        except api.APIError:
            bal = {"casual": 0, "sick": 0, "earned": 0, "floating": 0}
        is_on_leave = m["id"] in on_leave_ids_today
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.4, 1.3, 3.3], vertical_alignment="center")
            with c1:
                st.markdown(
                    f'<div class="ly-member-row">{avatar_html(m["name"], size=32)}'
                    f'<span class="info"><span class="ly-body-strong">{m["name"]}</span></span></div>',
                    unsafe_allow_html=True,
                )
            with c2:
                if is_on_leave:
                    st.markdown(badge_html("approved"), unsafe_allow_html=True)
                else:
                    st.markdown('<p class="ly-body">Available</p>', unsafe_allow_html=True)
            with c3:
                # Colored per leave type using the same TYPE_COLORS hue as
                # the donut chart legend and the calendar's pending cells —
                # flat gray pills (round 1) gave no visual link between
                # this row and the rest of the app's leave-type coloring.
                st.markdown(
                    type_chip_html("Casual", bal.get("casual", 0), "casual") +
                    type_chip_html("Sick", bal.get("sick", 0), "sick") +
                    type_chip_html("Earned", bal.get("earned", 0), "earned") +
                    type_chip_html("Floating", bal.get("floating", 0), "floating"),
                    unsafe_allow_html=True,
                )
