"""Shared header for every logged-in view: wordmark, welcome greeting, a
user chip (avatar + name), and a proper "Log out" control, top-right.

Previous version used a bare "Logout (power glyph)" button stretched full-width across
a narrow column -- wrong icon semantics and an ugly forced stretch. This version sizes
the button to its content and uses a real exit icon + label."""
import streamlit as st

from design_tokens import avatar_html


def render_header(user: dict):
    # Single flat row of columns (no nested st.columns-inside-a-column) --
    # nesting a second [2, 1.3] split inside an already-narrow 1.4-wide
    # outer column left the logout button with too little real width,
    # which is why "Log out" wrapped onto two lines. Giving it its own
    # fixed-width column at the top level guarantees enough room.
    left, chip_col, btn_col = st.columns([5.2, 1.6, 1.6], vertical_alignment="center")
    with left:
        st.markdown(
            '<div class="ly-enter" style="display:flex; align-items:baseline; gap:14px;">'
            '<span class="ly-wordmark">Leavely</span>'
            f'<span class="ly-body">Welcome, {user["name"]}</span>'
            "</div>",
            unsafe_allow_html=True,
        )
    with chip_col:
        st.markdown(
            f'<div class="ly-user-chip">{avatar_html(user["name"], size=26)}'
            f'<span class="name">{user["name"].split()[0]}</span></div>',
            unsafe_allow_html=True,
        )
    with btn_col:
        if st.button("Log out", key="logout-btn", icon=":material/logout:", type="secondary"):
            # .clear() is Streamlit's own documented way to wipe every key --
            # equivalent to the old manual "delete every key" loop but
            # without relying on dict-mutation-while-iterating semantics
            # holding up across Streamlit versions.
            st.session_state.clear()
            st.rerun()
    st.markdown('<hr class="ly-divider">', unsafe_allow_html=True)
