"""Sidebar navigation. Real st.button widgets (for genuine click/rerun
interactivity) styled via design_tokens' sidebar rules. Icons are native
Streamlit Material Symbols (st.button(icon=...)) rather than emoji — same
icon family Google's own products use, crisp at any zoom/OS, and the
single highest-leverage fix for a nav that read as "plain/dull". The
active item renders with a tinted fill + left accent bar; inactive items
are ghost buttons that tint on hover."""
import streamlit as st

NAV_ICONS = {
    "Calendar": ":material/calendar_month:",
    "My Requests": ":material/list_alt:",
    "Approve Leave": ":material/task_alt:",
    "Notifications": ":material/notifications:",
    "Analytics": ":material/bar_chart_4_bars:",
    "Holiday Calendar": ":material/beach_access:",
    "Settings": ":material/settings:",
    "Employees": ":material/badge:",
}

ROLE_LABELS = {"employee": "Employee", "manager": "Manager", "superuser": "Admin"}


def render_sidebar(nav_items: list, state_key: str = "nav", user: dict = None):
    if state_key not in st.session_state or st.session_state[state_key] not in nav_items:
        st.session_state[state_key] = nav_items[0]

    with st.sidebar:
        role_label = ROLE_LABELS.get((user or {}).get("role"), "")
        st.markdown(
            '<div class="ly-sidebar-brand">'
            '<span class="mark">L</span>'
            '<span class="meta">'
            '<span class="ly-wordmark" style="font-size:18px;">Leavely</span>'
            f'<span class="role-pill">{role_label}</span>'
            "</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown('<p class="ly-sidebar-section-label">Menu</p>', unsafe_allow_html=True)
        for item in nav_items:
            is_active = st.session_state[state_key] == item
            if st.button(
                item,
                key=f"nav-{item}",
                icon=NAV_ICONS.get(item, ":material/circle:"),
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state[state_key] = item
                st.rerun()
