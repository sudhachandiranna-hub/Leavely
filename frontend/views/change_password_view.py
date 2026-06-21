"""Forced password-change screen — shown instead of the normal role view
whenever the logged-in user's must_change_password flag is True (set by the
backend the moment an admin creates their account with an auto-generated
temp password, see backend/main.py create_employee). There is no skip path:
app.py checks this flag before routing to any role view, so it reappears on
every rerun until the change actually succeeds.
"""
import streamlit as st

import api_client as api


def render_change_password(user: dict):
    st.markdown(
        """
        <style>
        section[data-testid='stSidebar'] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown('<div style="height:9vh;"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="ly-enter" style="text-align:center; margin-bottom:24px;">'
            '<p class="ly-wordmark" style="font-size:32px;">Leavely</p>'
            f'<p class="ly-body" style="margin-top:10px;">Welcome, {user["name"]} — '
            "set a new password before continuing.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        with st.container(border=True, key="change-pw-card"):
            st.markdown('<p class="ly-h3" style="margin-bottom:6px;">Set a new password</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="ly-body" style="margin-bottom:16px;">Your account was just created with a '
                "temporary password. Enter that temporary password once, then choose a new one to "
                "continue into Leavely.</p>",
                unsafe_allow_html=True,
            )

            current = st.text_input(
                "Temporary password", key="cpw-current", type="password", placeholder="The temp password you logged in with",
            )
            new = st.text_input("New password", key="cpw-new", type="password", placeholder="At least 6 characters")
            confirm = st.text_input("Confirm new password", key="cpw-confirm", type="password")

            if st.button("Set password and continue", key="cpw-submit", type="primary", use_container_width=True):
                if not current or not new or not confirm:
                    st.error("Fill in all three fields.")
                elif len(new) < 6:
                    st.error("New password must be at least 6 characters.")
                elif new != confirm:
                    st.error("New password and confirmation don't match.")
                else:
                    try:
                        updated = api.change_password(user["id"], current, new)
                        st.session_state.user = updated
                        st.success("Password updated.")
                        st.rerun()
                    except api.APIError as e:
                        st.error(e.message)

            st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
            if st.button("Sign out instead", key="cpw-signout", type="secondary", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()
