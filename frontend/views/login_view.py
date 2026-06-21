"""Login screen — Linear/Stripe-grade restraint (clean white surface,
generous whitespace, one quiet accent) with a small Google-flavored detail
rather than a literal multi-color treatment, since "Google App colors" and
"Linear/Stripe/Apple minimalism" pull in different directions and trying to
satisfy both with loud color everywhere would satisfy neither.

The previous version's full-bleed navy gradient is exactly what read as
"the blue background" — gone. The page background is now Google's own
neutral surface gradient (white -> #F1F3F4, the literal tone Google
Workspace uses), with three barely-visible accent blobs (6-8% opacity) in
the app's own non-status colors so the page doesn't feel sterile. The card
is a plain elevated white surface (no glass/blur trick needed — there's no
color behind it worth blurring). Text reverts to default dark-ink styling
since the card is light again, which also fixes the earlier dark-on-dark
contrast workaround that's no longer needed.

The "Leavely" wordmark and the Sign-in button stay navy on purpose: navy is
the app's brand/action color used identically on every other screen
(buttons, active nav, KPI values). Changing just THIS button to a different
blue would make login look inconsistent with the rest of the app, not more
"on brand" — the dull/blue complaint was about the background wash, not the
one accent color used everywhere else. A thin four-color gradient bar under
the wordmark is the one deliberate nod to "Google App" — drawn from the
app's own established accent colors (teal/violet/blue/amber), not Google's
literal brand hex codes, two of which would otherwise collide with the
reserved status-color set.
"""
import streamlit as st

import api_client as api

DEMO_ACCOUNTS = (
    "manager@leavely.com / manager123 · "
    "rahul@leavely.com / employee123 · "
    "admin@leavely.com / admin123 (superuser)"
)


def render_login():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 14% 18%, rgba(14, 124, 134, 0.07) 0%, rgba(14, 124, 134, 0) 42%),
                radial-gradient(circle at 86% 14%, rgba(108, 99, 230, 0.07) 0%, rgba(108, 99, 230, 0) 42%),
                radial-gradient(circle at 76% 90%, rgba(242, 169, 59, 0.06) 0%, rgba(242, 169, 59, 0) 46%),
                linear-gradient(180deg, #FFFFFF 0%, #F1F3F4 100%) !important;
            background-attachment: fixed;
        }
        section[data-testid='stSidebar'] { display: none; }

        .ly-login-flourish {
            width: 64px;
            height: 5px;
            margin: 14px auto 0 auto;
            border-radius: 999px;
            background: linear-gradient(90deg, #1A73E8 0%, #0E7C86 34%, #F2A93B 67%, #6C63FF 100%);
        }

        div[class*="login-card"][data-testid="stVerticalBlockBorderWrapper"],
        div[class*="login-card"] div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF !important;
            border: 1px solid #E3E8EF !important;
            box-shadow: 0 16px 48px rgba(11, 31, 58, 0.10), 0 2px 8px rgba(11, 31, 58, 0.05) !important;
        }
        div[class*="login-card"] .stTextInput input {
            border: 1px solid #E3E8EF;
        }
        div[class*="login-card"] .stTextInput input:focus {
            box-shadow: 0 0 0 3px rgba(14, 124, 134, 0.18) !important;
            border-color: #0E7C86 !important;
        }
        .ly-demo-chip {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 999px;
            background: #F7F9FC;
            border: 1px solid #E3E8EF;
            color: #4B5868;
            font-family: 'Google Sans Text', 'Roboto', sans-serif;
            font-size: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown('<div style="height:9vh;"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="ly-enter" style="text-align:center; margin-bottom:28px;">'
            '<p class="ly-wordmark" style="font-size:44px;">Leavely</p>'
            '<div class="ly-login-flourish"></div>'
            '<p class="ly-body" style="margin-top:14px;">Leave, planned beautifully.</p>'
            "</div>",
            unsafe_allow_html=True,
        )

        with st.container(border=True, key="login-card"):
            st.markdown('<p class="ly-h3" style="margin-bottom:18px;">Sign in</p>', unsafe_allow_html=True)

            email = st.text_input("Email", key="login-email", placeholder="you@leavely.com")
            password = st.text_input("Password", key="login-password", type="password", placeholder="••••••••")

            if st.button("Sign in", key="login-submit", type="primary", use_container_width=True):
                if not email or not password:
                    st.error("Enter both email and password.")
                else:
                    try:
                        user = api.login(email.strip(), password)
                        st.session_state.user = user
                        st.session_state.nav = "Calendar"
                        st.rerun()
                    except api.APIError as e:
                        st.error(e.message)

            st.markdown(
                f'<div style="text-align:center; margin-top:18px;">'
                f'<span class="ly-demo-chip">Demo — {DEMO_ACCOUNTS}</span></div>',
                unsafe_allow_html=True,
            )
