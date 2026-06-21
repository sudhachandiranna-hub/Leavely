"""Month calendar grid — one clean tile per day, not two stacked boxes.

The first version layered a static colored <div> on top of a separate
st.button for every day, because raw HTML can't trigger a Python rerun.
That produced a disjointed "double box per day" look (a colored card,
then a plain default-styled button underneath it). This version collapses
that into a single real st.button per actionable day: the button itself
carries the day's status color and the "today" ring, applied via a small
inline <style> block keyed to that exact button's widget key. Holidays and
empty month-padding cells aren't clickable, so they stay plain styled divs
— there's nothing to merge there in the first place.

No business logic lives here, only presentation; shared geometry (size,
radius, hover-lift) is defined once in design_tokens.py.
"""
import calendar as cal_module
from datetime import date as date_cls

import streamlit as st

from design_tokens import (
    CAL_TINTS,
    COLORS,
    STATUS_COLOR_MAP,
    TYPE_COLORS,
    TYPE_CAL_TINTS,
)

WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TYPE_LABELS = {
    "casual": "Casual", "sick": "Sick", "earned": "Earned", "floating": "Floating",
    "maternity": "Maternity", "paternity": "Paternity",
}
SESSION_LABELS = {"morning": " (AM)", "evening": " (PM)"}


def render_month_calendar(
    year: int,
    month: int,
    events_by_date: dict,
    state_key: str,
    today: date_cls = None,
    key_prefix: str = "cal",
    range_start: str = None,
):
    """events_by_date: dict[iso_date_str] -> {"status", "type", "name", "request_id"}.

    Clicking a non-holiday day sets st.session_state[state_key] to that
    day's ISO date string. The caller checks that key right after this call
    to decide whether to open the day/apply dialog, then must clear it back
    to None so the dialog doesn't reopen on unrelated future reruns.

    range_start: ISO date string of a pending hotel-booking-style range
    selection (the caller is waiting on a second click to resolve the end
    date). When set, that one cell gets a strong highlight so the user can
    see where their range starts while picking the end date.
    """
    today = today or date_cls.today()
    cal_module.setfirstweekday(cal_module.MONDAY)
    weeks = cal_module.monthcalendar(year, month)

    # Per-day color/ring overrides, scoped to each button's own widget key
    # (key="<prefix>-<iso>" -> a ".st-key-<prefix>-<iso>" class Streamlit
    # attaches to that button's wrapper). Built once and injected before
    # the grid so every cell that needs a non-default look gets one.
    style_rules = []
    for week in weeks:
        for day_num in week:
            if day_num == 0:
                continue
            d = date_cls(year, month, day_num)
            iso = d.isoformat()
            ev = events_by_date.get(iso)
            status = ev["status"] if ev else None
            if status == "holiday" or (not status and d != today and iso != range_start):
                continue
            decls = []
            leave_type = (ev or {}).get("type")
            if status in ("pending", "approved"):
                # Every active leave-block (awaiting decision OR booked) is
                # colored by leave TYPE — matching the balance pie chart's
                # legend exactly — rather than a status color unrelated to
                # the legend. At a glance you can tell which kind of leave
                # it is everywhere it appears: pie chart, KPI tiles, and
                # the calendar grid all use the same hue per type.
                type_color = TYPE_COLORS.get(leave_type, COLORS["status_pending"])
                tint = TYPE_CAL_TINTS.get(leave_type, CAL_TINTS[status])
                decls.append(f"background: {tint} !important")
                decls.append("border-color: transparent !important")
                decls.append(f"border-top: 3px solid {type_color} !important")
            elif status == "cancelled":
                # Always brown, regardless of leave type. Cancelled is a
                # STATUS, not a type — it should read as its own state at a
                # glance, not as a faded version of whatever type it was.
                decls.append(f"background: {CAL_TINTS['cancelled']} !important")
                decls.append("border-color: transparent !important")
                decls.append(f"border-top: 3px dashed {STATUS_COLOR_MAP['cancelled']} !important")
                decls.append("text-decoration: line-through !important")
                decls.append(f"color: {COLORS['muted']} !important")
            elif status == "rejected":
                # Always red, same reasoning as cancelled above — plus an
                # explicit "Rejected" caption injected via ::after below,
                # since red alone can be ambiguous against a warm leave-type
                # color at this tile size; the word removes any doubt.
                decls.append(f"background: {CAL_TINTS['rejected']} !important")
                decls.append("border-color: transparent !important")
                decls.append(f"border-top: 3px dashed {STATUS_COLOR_MAP['rejected']} !important")
                decls.append("text-decoration: line-through !important")
                decls.append(f"color: {COLORS['muted']} !important")
                decls.append("display: flex !important")
                decls.append("flex-direction: column !important")
                decls.append("align-items: center !important")
                decls.append("justify-content: center !important")
                decls.append("gap: 1px !important")
            elif status:
                decls.append(f"background: {CAL_TINTS[status]} !important")
                decls.append("border-color: transparent !important")
                decls.append(f"border-top: 3px solid {STATUS_COLOR_MAP[status]} !important")
            if d == today:
                decls.append(f"box-shadow: inset 0 0 0 2px {COLORS['navy']} !important")
            if iso == range_start:
                # Hotel-booking "check-in" anchor: solid navy fill, not just
                # a ring, so it's unmistakable while a second click is
                # pending — visually distinct from the lighter status tints.
                decls.append(f"background: {COLORS['navy']} !important")
                decls.append(f"border-color: {COLORS['navy']} !important")
                decls.append(f"color: {COLORS['white']} !important")
            sel = f'div[class*="st-key-{key_prefix}-{iso}"] button'
            style_rules.append(f"{sel} {{ {'; '.join(decls)}; }}")
            if status == "rejected":
                # Second, non-color signal for rejected days: a small
                # uppercase caption under the day number, so "rejected"
                # never has to depend on red being distinguishable on its
                # own from a warm leave-type hue at this tile size.
                style_rules.append(
                    f'{sel}::after {{ content: "Rejected"; font-size: 8.5px; '
                    f'font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; '
                    f"color: {STATUS_COLOR_MAP['rejected']}; text-decoration: none; line-height: 1; }}"
                )
    if style_rules:
        st.markdown(f"<style>{''.join(style_rules)}</style>", unsafe_allow_html=True)

    with st.container(key=f"{key_prefix}-cal-grid"):
        header_cols = st.columns(7, gap="small")
        for i, label in enumerate(WEEKDAY_LABELS):
            header_cols[i].markdown(
                f'<p class="ly-caption" style="text-align:center; margin-bottom:8px;">{label}</p>',
                unsafe_allow_html=True,
            )

        for week in weeks:
            cols = st.columns(7, gap="small")
            for i, day_num in enumerate(week):
                with cols[i]:
                    if day_num == 0:
                        st.markdown('<div class="ly-cal-empty"></div>', unsafe_allow_html=True)
                        continue

                    d = date_cls(year, month, day_num)
                    iso = d.isoformat()
                    ev = events_by_date.get(iso)
                    status = ev["status"] if ev else None

                    if status == "holiday":
                        name = (ev or {}).get("name", "Holiday")
                        # This cell kept rendering taller than its neighbors
                        # even after three rounds of external CSS trying to
                        # pin its height with height/min-height/max-height
                        # !important on every wrapper — the same class of
                        # bug as the prev/next-month button label CSS that
                        # never reliably took effect live either. Rather
                        # than fight that selector cascade a 4th time,
                        # st.container(height=...) is Streamlit's own native
                        # fixed-height mechanism (already proven in this
                        # codebase — see the copy-holidays list in
                        # settings_view.py): Streamlit sets the height
                        # directly on the element it renders, so it doesn't
                        # depend on our stylesheet correctly matching
                        # Streamlit's generated class names at all.
                        with st.container(height=78, border=False, key=f"{key_prefix}-hol-{iso}"):
                            st.markdown(
                                f'<div class="ly-cal-holiday ly-enter">'
                                f'<span class="num">{day_num}</span>'
                                f'<span class="cap">{name}</span></div>',
                                unsafe_allow_html=True,
                            )
                        continue

                    tooltip = "Apply for leave"
                    if status:
                        type_label = TYPE_LABELS.get((ev or {}).get("type"), "")
                        session_suffix = SESSION_LABELS.get((ev or {}).get("session"), "")
                        tooltip = f"{type_label} leave{session_suffix} — {status.capitalize()}"
                    elif d == today:
                        tooltip = "Today — apply for leave"
                    if iso == range_start:
                        tooltip = "Start date — click another day to select the range"

                    st.button(
                        str(day_num),
                        key=f"{key_prefix}-{iso}",
                        help=tooltip,
                        use_container_width=True,
                        on_click=lambda iso=iso: st.session_state.update({state_key: iso}),
                    )
