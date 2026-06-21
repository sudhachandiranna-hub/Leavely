"""Day-detail / apply-leave modal — one st.dialog shared by every calendar
(employee and manager alike). Content adapts to whether the clicked date
already carries a leave request:
  - pending/approved  -> status badge + a Cancel-request action
  - rejected/cancelled -> a small note + a fresh apply form (backend allows
    re-applying on these dates)
  - no request        -> the apply form directly

Submitting/cancelling calls the backend then triggers a full st.rerun() so
the calendar, balance, and chart all reflect the new state immediately.
"""
from datetime import date as date_cls, timedelta

import streamlit as st

import api_client as api
from design_tokens import badge_html

LEAVE_TYPE_LABELS = {
    "casual": "Casual", "sick": "Sick", "earned": "Earned", "floating": "Floating",
    "maternity": "Maternity", "paternity": "Paternity",
}
LEAVE_TYPE_OPTIONS = ["casual", "sick", "earned", "floating", "maternity", "paternity"]
SESSION_OPTIONS = ["full", "morning", "evening"]
SESSION_LABELS = {"full": "Full day", "morning": "Morning session", "evening": "Evening session"}
ACTIVE_STATUSES = ("pending", "approved")

_DATE_ICON = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>'
)


def _leave_units(session: str) -> float:
    """Mirrors backend.main._leave_units — half a day for morning/evening
    sessions, a full day otherwise. Frontend and backend are separate
    processes talking over HTTP, so this is intentionally duplicated
    rather than shared; keep both in sync if the rule ever changes."""
    return 0.5 if session in ("morning", "evening") else 1.0


def _date_header_html(label: str) -> str:
    return (
        f'<div class="ly-modal-date"><span class="ico">{_DATE_ICON}</span>'
        f'<span class="txt"><p class="ly-body-strong">{label}</p></span></div>'
    )


def _session_radio(key: str) -> str:
    """Full day / Morning session / Evening session selector — half-day
    leave deducts 0.5 from balance (see _leave_units)."""
    st.markdown('<p class="ly-modal-field-label">Duration</p>', unsafe_allow_html=True)
    return st.radio(
        "Duration", options=SESSION_OPTIONS, format_func=lambda s: SESSION_LABELS[s],
        key=key, horizontal=True, label_visibility="collapsed",
    )


@st.dialog("Leave")
def day_dialog(user_id: int, iso_date: str, ev: dict, balance: dict):
    d = date_cls.fromisoformat(iso_date)
    st.markdown(_date_header_html(d.strftime("%A, %d %B %Y")), unsafe_allow_html=True)

    if ev and ev.get("status") in ACTIVE_STATUSES:
        session_suffix = {"morning": " (Morning)", "evening": " (Evening)"}.get(ev.get("session"), "")
        st.markdown(badge_html(ev["status"]), unsafe_allow_html=True)
        st.markdown(
            f'<p class="ly-body" style="margin-top:10px;">'
            f'{LEAVE_TYPE_LABELS.get(ev.get("type"), "")} leave{session_suffix}</p>',
            unsafe_allow_html=True,
        )
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        if st.button("Cancel request", key="day-cancel", use_container_width=True):
            try:
                api.cancel_leave(ev["request_id"], decided_by=user_id)
                st.success("Request cancelled.")
                st.rerun()
            except api.APIError as e:
                st.error(e.message)
        return

    if ev and ev.get("status") in ("rejected", "cancelled"):
        st.markdown(
            f'<p class="ly-caption" style="margin-bottom:14px; text-transform:none;">'
            f'Previously {ev["status"]} — you can apply again for this date.</p>',
            unsafe_allow_html=True,
        )

    st.markdown('<p class="ly-modal-field-label">Leave type</p>', unsafe_allow_html=True)
    leave_type = st.radio(
        "Leave type",
        options=LEAVE_TYPE_OPTIONS,
        format_func=lambda t: f"{LEAVE_TYPE_LABELS[t]} · {balance.get(t, 0)} left" if t in balance else LEAVE_TYPE_LABELS[t],
        key="day-apply-type",
        horizontal=True,
        label_visibility="collapsed",
    )
    session = _session_radio("day-apply-session")

    units = _leave_units(session)
    remaining = balance.get(leave_type, 0)
    if units > remaining:
        st.markdown(
            f'<div class="ly-modal-note">Not enough {LEAVE_TYPE_LABELS[leave_type].lower()} balance — '
            f'{remaining} day(s) left, this needs {units}.</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
    if st.button("Apply for leave", key="day-apply-submit", type="primary", use_container_width=True):
        try:
            api.apply_leave(user_id, iso_date, leave_type, session=session)
            st.success("Leave applied.")
            st.rerun()
        except api.APIError as e:
            st.error(e.message)


@st.dialog("Apply for a date range")
def range_apply_dialog(user_id: int, start_iso: str, end_iso: str, balance: dict):
    """Hotel-booking-style range apply: first click sets a start date,
    second click sets the end date, and every day in between is treated as
    a leave candidate — except weekends, configured holidays, and dates
    that already carry a pending/approved request, which are auto-skipped
    rather than deducted from balance (matching how Workday/Zoho People
    handle multi-day leave). Always fetches its own per-day status rather
    than trusting the caller's single-month events_by_date, since a range
    can span two different calendar months."""
    start_d = date_cls.fromisoformat(start_iso)
    end_d = date_cls.fromisoformat(end_iso)
    if start_d > end_d:
        start_d, end_d = end_d, start_d

    all_days = []
    d = start_d
    while d <= end_d:
        all_days.append(d)
        d += timedelta(days=1)

    months_needed = sorted({f"{dd.year:04d}-{dd.month:02d}" for dd in all_days})
    events_by_date = {}
    try:
        for m in months_needed:
            for e in api.get_calendar(user_id, m):
                events_by_date[e["date"]] = e
    except api.APIError as e:
        st.error(e.message)

    eligible, skipped = [], []
    for dd in all_days:
        iso = dd.isoformat()
        ev = events_by_date.get(iso)
        status = ev["status"] if ev else None
        if status == "holiday":
            skipped.append((dd, f"Holiday — {ev.get('name', '')}" if ev and ev.get("name") else "Holiday"))
        elif dd.weekday() >= 5:
            skipped.append((dd, "Weekend"))
        elif status in ACTIVE_STATUSES:
            skipped.append((dd, "Already requested"))
        else:
            eligible.append(dd)

    single_day = start_d == end_d
    span_label = (
        f'{start_d.strftime("%d %b")} – {end_d.strftime("%d %b %Y")}'
        if not single_day else start_d.strftime("%A, %d %B %Y")
    )
    st.markdown(_date_header_html(span_label), unsafe_allow_html=True)
    st.markdown(
        f'<p class="ly-caption" style="text-transform:none; margin-top:6px; line-height:1.5;">'
        f'{len(all_days)} day(s) selected · <b>{len(eligible)}</b> working day(s) will use leave balance. '
        f'Weekends, holidays, and days already requested are skipped automatically.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    if not eligible:
        st.markdown(
            '<p class="ly-body">Nothing to apply for — every day in this range is a weekend, '
            'a holiday, or already requested.</p>',
            unsafe_allow_html=True,
        )
        return

    st.markdown('<p class="ly-modal-field-label">Leave type</p>', unsafe_allow_html=True)
    leave_type = st.radio(
        "Leave type",
        options=LEAVE_TYPE_OPTIONS,
        format_func=lambda t: f"{LEAVE_TYPE_LABELS[t]} · {balance.get(t, 0)} left" if t in balance else LEAVE_TYPE_LABELS[t],
        key="range-apply-type",
        horizontal=True,
        label_visibility="collapsed",
    )

    # Half-day (Morning/Evening) only makes sense for a single date — a
    # multi-day range is always full days per day, so the duration picker
    # only appears when the resolved range collapsed to one eligible day
    # (e.g. the user clicked the same day twice, or every other day in the
    # range got auto-skipped).
    session = "full"
    if single_day or len(eligible) == 1:
        session = _session_radio("range-apply-session")

    units_per_day = _leave_units(session)
    total_units = len(eligible) * units_per_day
    remaining = balance.get(leave_type, 0)
    if total_units > remaining:
        st.warning(
            f"This range needs {total_units:g} {LEAVE_TYPE_LABELS[leave_type].lower()} day(s), but "
            f"only {remaining:g} remain. Submitting will apply day-by-day and stop "
            f"once the balance runs out."
        )

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
    if st.button(f"Apply for {len(eligible)} day(s)", key="range-apply-submit", type="primary", use_container_width=True):
        applied, first_failure = 0, None
        for dd in eligible:
            try:
                api.apply_leave(user_id, dd.isoformat(), leave_type, session=session)
                applied += 1
            except api.APIError as e:
                first_failure = (dd, e.message)
                break
        if applied:
            st.success(f"Applied {applied} of {len(eligible)} day(s).")
        if first_failure:
            st.error(f"Stopped at {first_failure[0].isoformat()}: {first_failure[1]}")
        st.rerun()
