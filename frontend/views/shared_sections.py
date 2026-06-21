"""Calendar and My-Requests sections, shared by employee and manager views
(a manager manages their own leave the exact same way an employee does).
Holds the thin UI-glue between api_client and the visual components only —
no business rules live here."""
from datetime import date as date_cls, timedelta

import streamlit as st

import api_client as api
from design_tokens import badge_html, kpi_tile_html, TYPE_COLORS
from components.calendar import render_month_calendar
from components.modals import day_dialog, range_apply_dialog, ACTIVE_STATUSES
from components.charts import donut_balance_chart

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

SESSION_SUFFIX = {"morning": " · Morning", "evening": " · Evening"}


def _next_business_day(d: date_cls) -> date_cls:
    nd = d + timedelta(days=1)
    while nd.weekday() >= 5:  # skip Sat/Sun — range-apply already skips them
        nd += timedelta(days=1)
    return nd


def group_consecutive_requests(requests_: list) -> list:
    """Collapse a flat list of one-row-per-day LeaveRequestOut dicts (the
    backend stores every day of a multi-day apply as its own row — see
    components/modals.py range_apply_dialog) into contiguous blocks: same
    user, leave type, status, and session, with dates that are either
    literally back-to-back or exactly one business day apart (a weekend
    that range-apply already skipped over still counts as "the same
    request"). Used by My Requests and Approve Leave so a 3-day leave shows
    as one row — start date, end date, day count, type — with a single
    action button that acts on every underlying row at once.

    Each returned block: {ids, user_id, type, status, session, start_date,
    end_date, day_count, applied_on}.
    """
    if not requests_:
        return []

    def sort_key(r):
        return (r["user_id"], r["type"], r["status"], r.get("session", "full"), r["date"])

    ordered = sorted(requests_, key=sort_key)
    blocks = []
    current = None
    for r in ordered:
        d = date_cls.fromisoformat(r["date"]) if isinstance(r["date"], str) else r["date"]
        session = r.get("session") or "full"
        same_group = (
            current is not None
            and r["user_id"] == current["user_id"]
            and r["type"] == current["type"]
            and r["status"] == current["status"]
            and session == current["session"]
            and d == _next_business_day(current["end_date"])
        )
        if same_group:
            current["ids"].append(r["id"])
            current["end_date"] = d
            current["day_count"] += 1
            current["applied_on"] = min(current["applied_on"], r["applied_on"])
        else:
            if current:
                blocks.append(current)
            current = {
                "ids": [r["id"]],
                "user_id": r["user_id"],
                "type": r["type"],
                "status": r["status"],
                "session": session,
                "start_date": d,
                "end_date": d,
                "day_count": 1,
                "applied_on": r["applied_on"],
            }
    if current:
        blocks.append(current)

    blocks.sort(key=lambda b: b["start_date"], reverse=True)
    return blocks


def block_date_label(b: dict) -> str:
    if b["day_count"] > 1:
        return f'{b["start_date"].strftime("%d %b")} – {b["end_date"].strftime("%d %b %Y")}'
    return b["start_date"].strftime("%d %b %Y")


def calendar_section(user: dict, key_prefix: str = "self"):
    state_key = f"{key_prefix}-month"
    today = date_cls.today()
    if state_key not in st.session_state:
        st.session_state[state_key] = (today.year, today.month)
    year, month = st.session_state[state_key]

    try:
        balance = api.get_balance(user["id"])
    except api.APIError as e:
        st.error(e.message)
        balance = {"casual": 0, "sick": 0, "earned": 0, "floating": 0}

    try:
        cal_events = api.get_calendar(user["id"], f"{year:04d}-{month:02d}")
    except api.APIError as e:
        st.error(e.message)
        cal_events = []
    events_by_date = {e["date"]: e for e in cal_events}

    range_start_key = f"{key_prefix}-range-start"
    range_start = st.session_state.get(range_start_key)

    col_cal, col_chart = st.columns([2.1, 1.2], gap="large")

    with col_cal:
        nav_l, nav_mid, nav_r = st.columns([1, 5, 1], vertical_alignment="center")
        with nav_l:
            # Plain "‹" text in a default button read as static punctuation,
            # not a control — a filled circular icon button (design_tokens'
            # -prev-month/-next-month CSS) is the same chevron affordance
            # browsers use for carousel/pagination controls. Label is empty —
            # CSS alone (button p {{display:none}}) turned out not to
            # reliably suppress the text in the live app (it wrapped onto a
            # second line instead), so the "Previous month" wording now only
            # lives in the tooltip (help=), never in the button's own label.
            if st.button(
                " ", key=f"{key_prefix}-prev-month",
                icon=":material/chevron_left:", help="Previous month",
            ):
                m, y = (12, year - 1) if month == 1 else (month - 1, year)
                st.session_state[state_key] = (y, m)
                st.rerun()
        with nav_mid:
            st.markdown(
                f'<p class="ly-h2" style="text-align:center;">{MONTH_NAMES[month - 1]} {year}</p>',
                unsafe_allow_html=True,
            )
        with nav_r:
            # Same empty-label treatment as Previous month, above.
            if st.button(
                " ", key=f"{key_prefix}-next-month",
                icon=":material/chevron_right:", help="Next month",
            ):
                m, y = (1, year + 1) if month == 12 else (month + 1, year)
                st.session_state[state_key] = (y, m)
                st.rerun()

        if range_start:
            start_label = date_cls.fromisoformat(range_start).strftime("%d %b %Y")
            banner_l, banner_r = st.columns([5, 1.3], vertical_alignment="center")
            with banner_l:
                st.markdown(
                    f'<div class="ly-range-banner"><span class="txt">Start: {start_label} — '
                    f'click an end date to select the range.</span></div>',
                    unsafe_allow_html=True,
                )
            with banner_r:
                if st.button("Clear", key=f"{key_prefix}-range-clear", use_container_width=True):
                    st.session_state[range_start_key] = None
                    st.rerun()

        click_state_key = f"{key_prefix}-selected-day"
        render_month_calendar(
            year, month, events_by_date, click_state_key, today=today,
            key_prefix=key_prefix, range_start=range_start,
        )

        selected_iso = st.session_state.get(click_state_key)
        if selected_iso:
            st.session_state[click_state_key] = None
            ev = events_by_date.get(selected_iso)

            if range_start is None:
                if ev and ev.get("status") in ACTIVE_STATUSES:
                    # Already-booked day with nothing pending: keep the
                    # original single-day view/cancel flow rather than
                    # folding it into a range (there's nothing to "extend"
                    # from a day you're already on leave on).
                    day_dialog(user_id=user["id"], iso_date=selected_iso, ev=ev, balance=balance)
                else:
                    # First click of a potential range — anchor it and wait
                    # for the second click. No dialog yet.
                    st.session_state[range_start_key] = selected_iso
                    st.rerun()
            else:
                start_iso, end_iso = sorted([range_start, selected_iso])
                st.session_state[range_start_key] = None
                range_apply_dialog(user_id=user["id"], start_iso=start_iso, end_iso=end_iso, balance=balance)

    with col_chart:
        st.markdown('<p class="ly-h3" style="margin-bottom:12px;">Remaining balance</p>', unsafe_allow_html=True)
        st.plotly_chart(donut_balance_chart(balance), use_container_width=True, key=f"{key_prefix}-donut")
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        kpi_cols = st.columns(4)
        for col, t, label in zip(
            kpi_cols,
            ("casual", "sick", "earned", "floating"),
            ("Casual", "Sick", "Earned", "Floating"),
        ):
            with col:
                st.markdown(
                    kpi_tile_html(label, str(balance.get(t, 0)), accent=TYPE_COLORS.get(t)),
                    unsafe_allow_html=True,
                )


def my_requests_section(user: dict, key_prefix: str = "self"):
    st.markdown('<p class="ly-h2" style="margin-bottom:16px;">My Requests</p>', unsafe_allow_html=True)
    try:
        requests_ = api.list_requests(user_id=user["id"])
    except api.APIError as e:
        st.error(e.message)
        requests_ = []

    if not requests_:
        st.markdown('<p class="ly-body">No leave requests yet.</p>', unsafe_allow_html=True)
        return

    # A multi-day apply creates one backend row per day (see
    # range_apply_dialog). Grouped here so a 3-day leave is one row with a
    # date range and a single Cancel that acts on every day in the block,
    # instead of three near-identical rows each needing their own click.
    blocks = group_consecutive_requests(requests_)

    for b in blocks:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2.2, 2, 2, 1.4])
            with c1:
                st.markdown(
                    f'<p class="ly-body-strong">{block_date_label(b)}</p>'
                    f'<p class="ly-caption" style="text-transform:none; color:var(--ly-muted, #7C8AA5);">'
                    f'{b["day_count"]} day{"s" if b["day_count"] > 1 else ""}</p>',
                    unsafe_allow_html=True,
                )
            with c2:
                suffix = SESSION_SUFFIX.get(b["session"], "")
                st.markdown(f'<p class="ly-body">{b["type"].capitalize()}{suffix}</p>', unsafe_allow_html=True)
            with c3:
                st.markdown(badge_html(b["status"]), unsafe_allow_html=True)
            with c4:
                if b["status"] in ("pending", "approved"):
                    if st.button("Cancel", key=f"{key_prefix}-cancel-{b['ids'][0]}", use_container_width=True):
                        try:
                            for rid in b["ids"]:
                                api.cancel_leave(rid, decided_by=user["id"])
                            st.rerun()
                        except api.APIError as e:
                            st.error(e.message)
