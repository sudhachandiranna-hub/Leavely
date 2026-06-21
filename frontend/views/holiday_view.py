"""Holiday Calendar — a read-only list of configured public holidays for a
location, visible to every role. A superuser edits this data from Settings;
everyone else just needs to see it (hence no role gating here at all).

Location data already supports multiple states/countries (Holiday.location +
LocationConfig), so the picker naturally grows as a superuser adds more
locations — today that's just "Chennai", seeded from holidays.json.
"""
from datetime import date as date_cls

import streamlit as st

import api_client as api
from design_tokens import kpi_tile_html, holiday_tag_html, COLORS

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_FLAG_ICON = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4 22V4"/><path d="M4 4h14l-2.5 4L18 12H4"/></svg>'
)


def render_holiday_calendar(user: dict):
    st.markdown('<p class="ly-h2" style="margin-bottom:4px;">Holiday Calendar</p>', unsafe_allow_html=True)
    # The "add more states/countries from Settings" hint is only actionable
    # by a superuser (Settings is superuser-only, see settings_view.py) — a
    # manager or employee can't do anything with it, so they just get the
    # plain description instead of a dead-end instruction.
    subtitle = "Public holidays for your location."
    if user.get("role") == "superuser":
        subtitle += " A superuser can add more states or countries from Settings."
    st.markdown(f'<p class="ly-body" style="margin-bottom:18px;">{subtitle}</p>', unsafe_allow_html=True)

    try:
        locations = api.get_locations()
    except api.APIError as e:
        st.error(e.message)
        locations = []

    location_names = [l["location"] for l in locations] or [user.get("location", "Chennai")]
    default_idx = location_names.index(user.get("location")) if user.get("location") in location_names else 0

    picked = st.selectbox("Location", options=location_names, index=default_idx, key="holiday-cal-location")

    try:
        holidays = api.get_holidays(picked)
    except api.APIError as e:
        st.error(e.message)
        holidays = []

    if not holidays:
        st.markdown('<p class="ly-body">No holidays configured for this location yet.</p>', unsafe_allow_html=True)
        return

    today = date_cls.today()
    parsed = [
        (date_cls.fromisoformat(h["date"]) if isinstance(h["date"], str) else h["date"], h["name"])
        for h in holidays
    ]
    parsed.sort(key=lambda x: x[0])
    upcoming = [p for p in parsed if p[0] >= today]
    next_holiday = upcoming[0] if upcoming else None

    # Stat row: at-a-glance counts instead of diving straight into a flat
    # list — gives the screen a top-level hierarchy before the day-by-day
    # detail.
    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(kpi_tile_html("Total holidays", str(len(parsed)), accent=COLORS["navy"]), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_tile_html("Upcoming", str(len(upcoming)), accent=COLORS["data_blue"]), unsafe_allow_html=True)
    with k3:
        next_label = f'{next_holiday[1]} · {next_holiday[0].strftime("%d %b")}' if next_holiday else "—"
        st.markdown(kpi_tile_html("Next up", next_label, accent=COLORS["status_approved"]), unsafe_allow_html=True)

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # One real <table> instead of a stack of individually-bordered
    # containers — column headers + hairline row dividers + a hover state
    # read as a single dataset (Stripe/Linear-style data table), not a pile
    # of separate cards repeating the same three fields.
    row_html = []
    current_month_key = None
    for d, name in parsed:
        month_key = (d.year, d.month)
        if month_key != current_month_key:
            current_month_key = month_key
            row_html.append(
                f'<tr class="ly-htable-month-row"><td colspan="4">'
                f'{MONTH_NAMES[d.month - 1]} {d.year}</td></tr>'
            )

        weekday = WEEKDAY_NAMES[d.weekday()]
        is_past = d < today
        is_today = d == today
        if is_today:
            tag, tag_color = "Today", COLORS["status_approved"]
        elif is_past:
            tag, tag_color = "Past", COLORS["muted"]
        else:
            tag, tag_color = "Upcoming", COLORS["data_blue"]

        row_class = "ly-htable-row is-today" if is_today else "ly-htable-row"
        row_html.append(
            f'<tr class="{row_class}">'
            f'<td><span class="ly-htable-date">{d.strftime("%d %b %Y")}</span></td>'
            f'<td><span class="ly-htable-day">{weekday}</span></td>'
            f'<td><span class="ly-htable-name">{_FLAG_ICON}{name}</span></td>'
            f'<td class="ly-htable-col-status">{holiday_tag_html(tag, tag_color)}</td>'
            f'</tr>'
        )

    st.markdown(
        '<div class="ly-htable-wrap ly-enter">'
        '<table class="ly-htable">'
        '<thead><tr>'
        '<th>Date</th><th>Day</th><th>Holiday</th>'
        '<th class="ly-htable-col-status">Status</th>'
        '</tr></thead>'
        f'<tbody>{"".join(row_html)}</tbody>'
        '</table></div>',
        unsafe_allow_html=True,
    )
