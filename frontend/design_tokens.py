"""
Leavely — Design System
========================
Single source of truth for all visual tokens and reusable component CSS.
Every Streamlit screen imports this module and calls `apply_design_system()`
once at the top of the page. No page/business logic lives here — tokens,
CSS, and small presentational render-helpers only.

Visual identity: premium micro-SaaS. Google Material typography with
Linear/Stripe-grade interaction polish. Glassmorphism accents. Generous
whitespace. Navy anchor color. Status colors are semantic and reserved
exclusively for leave-status indicators (badges, calendar cells) — never
reused for generic UI accents.
"""

# ---------------------------------------------------------------------------
# COLOR TOKENS
# ---------------------------------------------------------------------------

COLORS = {
    # Base
    "white": "#FFFFFF",
    "surface": "#FFFFFF",
    "background": "#F7F9FC",

    # Navy anchor (brand)
    "navy": "#0B1F3A",
    "navy_700": "#122B4D",
    "navy_600": "#1B3A63",
    "navy_500": "#27496B",
    "navy_100": "#E7ECF3",

    # Neutrals (text, borders, dividers)
    "ink": "#0F1729",          # primary text
    "slate": "#4B5868",        # secondary text
    "muted": "#8A93A3",        # tertiary / placeholder text
    "border": "#E3E8EF",
    "divider": "#EDF1F6",

    # Glass
    "glass_fill": "rgba(255, 255, 255, 0.62)",
    "glass_fill_strong": "rgba(255, 255, 255, 0.80)",
    "glass_border": "rgba(255, 255, 255, 0.45)",

    # --- Semantic status colors — leave-status ONLY, do not reuse ---
    "status_pending": "#F5C242",
    "status_approved": "#34A853",
    "status_cancelled": "#8D6E63",
    "status_rejected": "#EA4335",
    "status_holiday": "#E0E0E0",

    # --- Misc data accents (login flourish, avatar palette only — no longer
    # leave-type colors, see "type_*" tokens below for those). ---
    "data_teal": "#0E7C86",
    "data_violet": "#6C63FF",
    "data_blue": "#1A73E8",    # Google Blue — login flourish
    "data_amber": "#F2A93B",   # warm accent, distinct from status_pending — login flourish

    # --- Leave TYPE palette (2026-06 refresh) — a Google-brand swatch the
    # user supplied directly (Bright Navy Blue / Viva La Bleu / Dublin /
    # Marigold), replacing the old navy/blue/teal/violet set. Deliberately
    # none of these are red or brown — those two hues are reserved
    # exclusively for rejected/cancelled (status_rejected/status_cancelled
    # above, and the note on TYPE_COLORS below) so a leave type can never
    # be mistaken for a voided one. ---
    "type_casual": "#1976D2",    # Bright Navy Blue
    "type_sick": "#98C0E3",      # Viva La Bleu
    "type_earned": "#6EBC6B",    # Dublin
    "type_floating": "#FFC107", # Marigold
}

# Soft tint backgrounds for status badges (small pills — text label carries
# most of the meaning, so a light tint is enough).
STATUS_TINTS = {
    "pending": "rgba(245, 194, 66, 0.16)",
    "approved": "rgba(52, 168, 83, 0.14)",
    "cancelled": "rgba(141, 110, 99, 0.16)",
    "rejected": "rgba(234, 67, 53, 0.14)",
    "holiday": "rgba(224, 224, 224, 0.55)",
}

# Vibrant tint backgrounds for calendar day cells, where the background
# color is the ONLY signal at a glance (no text label inside the cell).
# Pushed well past badge-strength opacity — at small tile size, anything
# under ~0.45 alpha reads as washed-out/pale against the white surface.
# Paired with a solid (non-transparent) top accent bar in calendar.py for a
# Google-Calendar-chip-style two-tier look: tinted fill + a bold stripe.
CAL_TINTS = {
    "pending": "rgba(245, 194, 66, 0.55)",
    "approved": "rgba(52, 168, 83, 0.50)",
    "cancelled": "rgba(141, 110, 99, 0.48)",
    "rejected": "rgba(234, 67, 53, 0.46)",
    "holiday": "rgba(224, 224, 224, 0.80)",
}

STATUS_COLOR_MAP = {
    "pending": COLORS["status_pending"],
    "approved": COLORS["status_approved"],
    "cancelled": COLORS["status_cancelled"],
    "rejected": COLORS["status_rejected"],
    "holiday": COLORS["status_holiday"],
}

# ---------------------------------------------------------------------------
# LEAVE-TYPE COLORS — the single source of truth for "which color is casual/
# sick/earned/floating/maternity/paternity", reused by BOTH the balance pie
# chart (charts.py imports this directly) and the calendar's pending/approved
# cells (calendar.py), so a glance at either one always agrees with the
# other. Maternity/paternity get a color too — the calendar still needs to
# show them — but they're excluded from the pie chart itself (see
# charts.py PIE_CHART_TYPES) since they're statutory pools, not part of the
# day-to-day discretionary mix the donut visualizes.
#
# IMPORTANT: this only governs ACTIVE leave (pending/approved). Voided leave
# (rejected/cancelled) deliberately does NOT use these colors — calendar.py
# colors those by STATUS instead (always red for rejected, always brown for
# cancelled), so a voided day reads as its own state first, not as a faded
# version of whatever type it happened to be.
# ---------------------------------------------------------------------------
TYPE_COLORS = {
    "casual": COLORS["type_casual"],
    "sick": COLORS["type_sick"],
    "earned": COLORS["type_earned"],
    "floating": COLORS["type_floating"],
    "maternity": "#D81B60",
    "paternity": "#3949AB",
}


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """'#RRGGBB' -> 'rgba(r, g, b, a)', so calendar tints derive from
    TYPE_COLORS instead of a hand-maintained parallel palette that can
    drift out of sync with the chart legend."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


# Translucent calendar-tint per leave type, same alpha strength as CAL_TINTS
# so pending-by-type cells carry the same visual weight as status-colored
# ones (approved/rejected/cancelled).
TYPE_CAL_TINTS = {t: _hex_to_rgba(v, 0.50) for t, v in TYPE_COLORS.items()}

# ---------------------------------------------------------------------------
# SPACING SCALE
# ---------------------------------------------------------------------------

SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
    "xxl": "48px",
}

RADIUS = {
    "sm": "8px",
    "md": "12px",
    "lg": "16px",   # card standard
    "pill": "999px",
}

SHADOWS = {
    "soft": "0 4px 16px rgba(11, 31, 58, 0.06)",
    "card": "0 8px 24px rgba(11, 31, 58, 0.08)",
    "raised": "0 12px 32px rgba(11, 31, 58, 0.14)",
    "glow_navy": "0 8px 28px rgba(11, 31, 58, 0.22)",
}

# ---------------------------------------------------------------------------
# MOTION — state-change transitions only, no decorative animation
# ---------------------------------------------------------------------------

MOTION = {
    "fast": "150ms ease-out",
    "base": "200ms ease-out",
    "slow": "250ms ease-out",
}

# ---------------------------------------------------------------------------
# TYPOGRAPHY
# ---------------------------------------------------------------------------

FONTS = {
    # Body/UI hierarchy: Google Sans is not freely distributable, so we pair
    # the closest open Google-Material equivalents (Product Sans lineage)
    # with Roboto as the system fallback.
    "body": "'Google Sans Text', 'Roboto', -apple-system, sans-serif",
    "heading": "'Google Sans', 'Roboto', -apple-system, sans-serif",
    # Premium display face reserved for the "Leavely" wordmark only.
    "wordmark": "'Sora', 'Google Sans', sans-serif",
}

GOOGLE_FONTS_IMPORT_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Sora:wght@600;700;800&"
    "family=Roboto:wght@400;500;600;700&"
    "display=swap"
)

TYPE_SCALE = {
    "h1": {"size": "32px", "weight": "700", "line_height": "40px", "letter_spacing": "-0.01em"},
    "h2": {"size": "24px", "weight": "600", "line_height": "32px", "letter_spacing": "-0.005em"},
    "h3": {"size": "18px", "weight": "600", "line_height": "26px", "letter_spacing": "0"},
    "body": {"size": "14px", "weight": "400", "line_height": "22px", "letter_spacing": "0"},
    "body_strong": {"size": "14px", "weight": "600", "line_height": "22px", "letter_spacing": "0"},
    "caption": {"size": "12px", "weight": "500", "line_height": "16px", "letter_spacing": "0.01em"},
    "wordmark": {"size": "26px", "weight": "700", "line_height": "32px", "letter_spacing": "-0.01em"},
}


# ---------------------------------------------------------------------------
# CSS GENERATION
# ---------------------------------------------------------------------------

def get_css() -> str:
    """Returns the full component CSS (cards, buttons, badges, calendar
    cells, modal, nav items, KPI tiles) built entirely from the tokens
    above. Imported once per page via apply_design_system()."""

    c = COLORS
    s = SPACING
    r = RADIUS
    sh = SHADOWS
    m = MOTION
    f = FONTS
    t = TYPE_SCALE

    return f"""
<style>
@import url('{GOOGLE_FONTS_IMPORT_URL}');

html, body, [class*="css"] {{
    font-family: {f['body']};
    color: {c['ink']};
}}

/* Hide the deploy/menu chrome but NOT the whole <header>. An earlier pass
   tried to fix a vanishing sidebar by forcing the reopen arrow
   (button[data-testid="collapsedControl"]) to stay visible — that treated
   the symptom, not the cause: the sidebar IS the app's only nav, so it
   must never be collapsible in the first place, on any screen size.
   Belt-and-suspenders fix: app.py pins initial_sidebar_state="expanded",
   and every control that could collapse it (or that only shows once
   collapsed) is hidden outright here, with the sidebar's own width/
   transform forced regardless of whatever expanded/collapsed state
   Streamlit's client JS tries to apply. */
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{
    background: transparent;
    box-shadow: none;
}}
header[data-testid="stHeader"] [data-testid="stToolbar"] {{
    visibility: hidden;
}}
button[data-testid="collapsedControl"],
button[data-testid="stSidebarCollapseButton"],
div[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
    visibility: hidden !important;
}}
section[data-testid="stSidebar"] {{
    transform: none !important;
    visibility: visible !important;
    min-width: 280px !important;
    max-width: 280px !important;
    width: 280px !important;
    margin-left: 0 !important;
}}
section[data-testid="stSidebar"][aria-expanded="false"] {{
    transform: none !important;
    margin-left: 0 !important;
    min-width: 280px !important;
    width: 280px !important;
}}

.stApp {{
    background: {c['white']};
}}

/* ---------------- Typography helpers ---------------- */
.ly-h1 {{ font-family: {f['heading']}; font-size: {t['h1']['size']}; font-weight: {t['h1']['weight']};
          line-height: {t['h1']['line_height']}; letter-spacing: {t['h1']['letter_spacing']}; color: {c['ink']}; margin: 0; }}
.ly-h2 {{ font-family: {f['heading']}; font-size: {t['h2']['size']}; font-weight: {t['h2']['weight']};
          line-height: {t['h2']['line_height']}; letter-spacing: {t['h2']['letter_spacing']}; color: {c['ink']}; margin: 0; }}
.ly-h3 {{ font-family: {f['heading']}; font-size: {t['h3']['size']}; font-weight: {t['h3']['weight']};
          line-height: {t['h3']['line_height']}; color: {c['ink']}; margin: 0; }}
.ly-body {{ font-family: {f['body']}; font-size: {t['body']['size']}; font-weight: {t['body']['weight']};
            line-height: {t['body']['line_height']}; color: {c['slate']}; margin: 0; }}
.ly-body-strong {{ font-family: {f['body']}; font-size: {t['body_strong']['size']}; font-weight: {t['body_strong']['weight']};
            line-height: {t['body_strong']['line_height']}; color: {c['ink']}; margin: 0; }}
.ly-caption {{ font-family: {f['body']}; font-size: {t['caption']['size']}; font-weight: {t['caption']['weight']};
               line-height: {t['caption']['line_height']}; letter-spacing: {t['caption']['letter_spacing']};
               color: {c['muted']}; text-transform: uppercase; margin: 0; }}
.ly-wordmark {{ font-family: {f['wordmark']}; font-size: {t['wordmark']['size']}; font-weight: {t['wordmark']['weight']};
               letter-spacing: {t['wordmark']['letter_spacing']}; color: {c['navy']}; margin: 0; }}
.ly-wordmark.on-navy {{ color: {c['white']}; }}

/* ---------------- Card (glass) ---------------- */
.ly-card {{
    background: {c['glass_fill']};
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid {c['border']};
    border-radius: {r['lg']};
    box-shadow: {sh['card']};
    padding: {s['lg']};
    transition: box-shadow {m['base']}, transform {m['base']};
}}
.ly-card.hover-lift:hover {{
    box-shadow: {sh['raised']};
    transform: translateY(-2px);
}}
.ly-card.solid {{
    background: {c['surface']};
    backdrop-filter: none;
}}

/* ---------------- Buttons ---------------- */
.stButton > button {{
    border-radius: {r['sm']};
    font-family: {f['body']};
    font-weight: 600;
    font-size: 14px;
    padding: 0.5rem 1.1rem;
    transition: background-color {m['base']}, border-color {m['base']}, color {m['base']}, box-shadow {m['base']};
    border: 1px solid transparent;
}}
.stButton > button[kind="primary"] {{
    background-color: {c['navy']};
    color: {c['white']};
    box-shadow: {sh['soft']};
}}
.stButton > button[kind="primary"]:hover {{
    background-color: {c['navy_600']};
    box-shadow: {sh['glow_navy']};
}}
.stButton > button[kind="secondary"] {{
    background-color: transparent;
    color: {c['navy']};
    border: 1px solid {c['navy']};
}}
.stButton > button[kind="secondary"]:hover {{
    background-color: {c['navy_100']};
}}

/* ---------------- Approve button (manager queue) ----------------
   Deliberately NOT the navy primary button — green reads as "this is a
   positive, approving action," distinct from the navy primary used for
   neutral submit actions elsewhere. Scoped to the "appr-" key prefix used
   by every approve button (including the consolidated multi-day block),
   so this never touches any other button on the page. */
div[class*="st-key-appr-"] .stButton > button,
div[class*="st-key-appr-"] button {{
    background-color: {c['status_approved']} !important;
    border-color: {c['status_approved']} !important;
    color: {c['white']} !important;
    box-shadow: {sh['soft']};
}}
div[class*="st-key-appr-"] .stButton > button:hover,
div[class*="st-key-appr-"] button:hover {{
    background-color: #2C8F47 !important;
    border-color: #2C8F47 !important;
}}

/* ---------------- Status badge (pill) ---------------- */
.ly-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: {r['pill']};
    font-family: {f['body']};
    font-size: {t['caption']['size']};
    font-weight: 700;
    letter-spacing: 0.01em;
    text-transform: capitalize;
    transition: background-color {m['base']}, color {m['base']};
}}
.ly-badge .dot {{ width: 6px; height: 6px; border-radius: 50%; }}
.ly-badge.status-pending   {{ background: {STATUS_TINTS['pending']};   color: #8a6107; }}
.ly-badge.status-approved  {{ background: {STATUS_TINTS['approved']};  color: #1e6b34; }}
.ly-badge.status-cancelled {{ background: {STATUS_TINTS['cancelled']}; color: {c['status_cancelled']}; }}
.ly-badge.status-rejected  {{ background: {STATUS_TINTS['rejected']};  color: #a4271f; }}
.ly-badge.status-holiday   {{ background: {STATUS_TINTS['holiday']};   color: #6b6b6b; }}
.ly-badge.status-pending .dot   {{ background: {c['status_pending']}; }}
.ly-badge.status-approved .dot  {{ background: {c['status_approved']}; }}
.ly-badge.status-cancelled .dot {{ background: {c['status_cancelled']}; }}
.ly-badge.status-rejected .dot  {{ background: {c['status_rejected']}; }}
.ly-badge.status-holiday .dot   {{ background: {c['status_holiday']}; }}

/* ---------------- Calendar day cell ----------------
   Each actionable day is ONE real st.button (no decorative div stacked on
   top of it — stacking a static div above a separate button is what
   produced the doubled, disjointed boxes in the first pass). Geometry
   lives here, scoped to any container whose key contains "cal-grid"; the
   per-day status tint and "today" ring are injected as small inline
   <style> blocks by calendar.py, keyed to that day's exact button key. */
div[class*="-cal-grid"] [data-testid="stColumn"] {{
    height: 78px !important;
    min-height: 78px !important;
    max-height: 78px !important;
    overflow: hidden;
}}
/* Holiday cells stopped going through this CSS-only height fight entirely
   (see calendar.py) — they now sit inside a real st.container(height=78),
   which is Streamlit's own native fixed-height mechanism. These two
   selectors just strip that container's default padding/margin so its
   78px is usable space, not space minus Streamlit's own chrome. */
div[class*="-cal-grid"] div[data-testid="stVerticalBlockBorderWrapper"],
div[class*="-cal-grid"] div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {{
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    box-sizing: border-box;
}}
div[class*="-cal-grid"] .stButton > button {{
    width: 100%;
    height: 78px !important;
    min-height: 78px !important;
    max-height: 78px !important;
    box-sizing: border-box;
    border-radius: {r['md']};
    border: 1px solid {c['divider']};
    background: {c['surface']};
    font-family: {f['heading']};
    font-size: 16px;
    font-weight: 700;
    color: {c['ink']};
    box-shadow: none;
    padding: 0;
    overflow: hidden;
    transition: background-color {m['base']}, border-color {m['base']}, transform {m['base']}, box-shadow {m['base']};
}}
div[class*="-cal-grid"] .stButton > button:hover {{
    border-color: {c['navy_500']};
    box-shadow: {sh['soft']};
    transform: translateY(-1px);
}}
div[class*="-cal-grid"] .stButton > button:focus:not(:active) {{
    border-color: {c['navy_500']};
    box-shadow: {sh['soft']};
}}

/* Non-actionable cells: empty month-padding days, and holidays (static,
   no button — holidays aren't editable, so they don't need one). Every
   cell variant — button, empty, holiday — shares the exact same `height`
   (not min-height, which let long holiday names wrap and grow the tile
   taller than its neighbors) so the grid stays pixel-uniform regardless
   of content.

   The remaining size mismatch users see isn't the inner tile — it's the
   OUTER Streamlit wrapper. st.button renders inside div.stButton, but
   st.markdown renders inside div[data-testid="stElementContainer"]
   (or the older "element-container" testid), and those two wrappers ship
   different default margins/line-heights. Two same-height children inside
   differently-sized parents still look "uneven" in the grid. Reset both
   wrappers to zero margin/padding inside the calendar grid specifically so
   button cells and markdown cells sit flush in the same box model. */
div[class*="-cal-grid"] div[data-testid="stElementContainer"],
div[class*="-cal-grid"] div[data-testid="element-container"],
div[class*="-cal-grid"] div.stButton,
div[class*="-cal-grid"] div.stMarkdown {{
    margin: 0 !important;
    padding: 0 !important;
    line-height: 0;
    height: 78px !important;
    min-height: 78px !important;
    max-height: 78px !important;
    box-sizing: border-box;
}}
.ly-cal-empty {{ height: 78px !important; min-height: 78px !important; max-height: 78px !important; box-sizing: border-box; }}
.ly-cal-holiday {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
    border-radius: {r['md']};
    border: 1px solid {c['divider']};
    border-top: 3px solid {c['slate']};
    background: {CAL_TINTS['holiday']};
    text-align: center;
    overflow: hidden;
    padding: 4px 4px 0 4px;
}}
.ly-cal-holiday .num {{ font-family: {f['heading']}; font-size: 16px; font-weight: 700; color: {c['slate']}; line-height: 1.1; }}
.ly-cal-holiday .cap {{
    font-family: {f['body']}; font-size: 9.5px; color: {c['muted']}; margin-top: 2px;
    line-height: 1.15; max-width: 100%; padding: 0 2px;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    white-space: normal; overflow: hidden; text-overflow: ellipsis;
}}

/* Month prev/next controls — a bare "‹"/"›" glyph in a default button read
   as inert punctuation rather than a clickable control. Icon-only filled
   circles (the same affordance as carousel/pagination arrows everywhere
   else) make the click target obvious; the text label is kept in the DOM
   for accessibility/help-text but visually hidden so only the chevron shows. */
div[class*="-prev-month"] .stButton > button,
div[class*="-next-month"] .stButton > button {{
    width: 40px !important;
    height: 40px !important;
    min-height: 40px !important;
    min-width: 40px !important;
    border-radius: 50% !important;
    background: {c['navy']} !important;
    border: none !important;
    color: {c['white']} !important;
    box-shadow: {sh['soft']};
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0 !important;
    transition: background-color {m['base']}, transform {m['base']};
}}
div[class*="-prev-month"] .stButton > button:hover,
div[class*="-next-month"] .stButton > button:hover {{
    background: {c['navy_500']} !important;
    transform: translateY(-1px);
}}
div[class*="-prev-month"] .stButton > button p,
div[class*="-next-month"] .stButton > button p {{
    display: none !important;
}}
/* Streamlit's :material/...: icon renders as a span[data-testid="stIconMaterial"]
   with color:inherit — NOT an <svg> in this Streamlit version (1.58). The old
   `button svg {{ color: white }}` rule never matched anything, so the chevron
   silently inherited the button's own (navy) text color onto a navy fill —
   invisible icon-on-fill. Target the actual element and force white directly,
   keep the svg rule too as a defensive fallback for other Streamlit versions. */
div[class*="-prev-month"] .stButton > button [data-testid="stIconMaterial"],
div[class*="-next-month"] .stButton > button [data-testid="stIconMaterial"],
div[class*="-prev-month"] .stButton > button svg,
div[class*="-next-month"] .stButton > button svg {{
    color: {c['white']} !important;
    fill: {c['white']} !important;
    margin: 0 !important;
}}

/* Range-selection banner above the grid (hotel-booking style: shows once a
   start date is picked, prompting for the end date, with a way to bail out). */
.ly-range-banner {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    background: {c['navy_100']};
    border: 1px solid {c['navy_500']};
    border-radius: {r['sm']};
    padding: 10px 14px;
    margin-bottom: {s['sm']};
}}
.ly-range-banner .txt {{ font-family: {f['body']}; font-size: 13px; font-weight: 600; color: {c['navy']}; }}
div[class*="-range-clear"] .stButton > button {{
    background: transparent;
    border: 1px solid {c['navy']};
    color: {c['navy']};
    padding: 4px 12px;
    font-size: 12px;
    min-height: 0;
    box-shadow: none;
}}

/* ---------------- Modal (st.dialog content wrapper) ---------------- */
.ly-modal-card {{
    padding: {s['sm']} 0 0 0;
}}
div[data-testid="stDialog"] > div {{
    border-radius: {r['lg']};
}}

/* Apply-leave dialog: a colored date header bar instead of a bare line of
   text, plus a small uppercase field label above each radio group so the
   leave-type / session choices read as distinct, labeled steps. */
.ly-modal-date {{
    display: flex;
    align-items: center;
    gap: 10px;
    background: {c['navy_100']};
    border-radius: {r['md']};
    padding: 12px 14px;
    margin-bottom: {s['md']};
}}
.ly-modal-date .ico {{
    width: 32px; height: 32px; flex-shrink: 0;
    border-radius: {r['sm']};
    background: {c['navy']};
    color: {c['white']};
    display: flex; align-items: center; justify-content: center;
}}
.ly-modal-date .txt p {{ margin: 0; }}
.ly-modal-field-label {{
    font-family: {f['body']};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: {c['muted']};
    margin: {s['md']} 0 6px 0;
}}
.ly-modal-note {{
    font-family: {f['body']};
    font-size: 12px;
    color: {c['muted']};
    background: {c['background']};
    border-radius: {r['sm']};
    padding: 8px 10px;
    margin-top: 8px;
    line-height: 1.5;
}}

/* ---------------- Sidebar navigation ----------------
   A real st.button per item (genuine click/rerun interactivity), each
   carrying a native Material Symbols icon via st.button(icon=...) rather
   than emoji glyphs — emoji render inconsistently across OS/fonts and read
   as a hobby-project shortcut, which is most of why this panel looked
   "plain" next to a Linear/Stripe/Google-grade nav. Active item gets a
   tinted fill + a left accent bar (Linear's pattern); inactive items are
   transparent ghost rows that tint on hover. */
section[data-testid="stSidebar"] {{
    background: {c['navy']};
    border-right: none;
}}
section[data-testid="stSidebar"] > div:first-child {{
    padding-top: {s['md']};
}}
.ly-sidebar-brand {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 10px {s['md']} 10px;
    margin-bottom: {s['sm']};
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}}
.ly-sidebar-brand .mark {{
    width: 32px;
    height: 32px;
    border-radius: {r['sm']};
    background: {c['white']};
    color: {c['navy']};
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: {f['wordmark']};
    font-weight: 800;
    font-size: 16px;
    flex-shrink: 0;
}}
.ly-sidebar-brand .meta {{ display: flex; flex-direction: column; gap: 2px; line-height: 1.1; }}
.ly-sidebar-brand .ly-wordmark {{ color: {c['white']}; }}
.ly-sidebar-brand .role-pill {{
    font-family: {f['body']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.55);
}}
.ly-sidebar-section-label {{
    font-family: {f['body']};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.40);
    padding: 0 10px;
    margin: 2px 0 6px 0;
}}
section[data-testid="stSidebar"] .stButton {{
    margin-bottom: 2px;
}}
section[data-testid="stSidebar"] .stButton > button {{
    width: 100%;
    text-align: left;
    justify-content: flex-start;
    gap: 10px;
    font-weight: 600;
    font-size: 14px;
    padding: 9px 12px;
    border-radius: {r['sm']};
}}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {{
    background: transparent;
    color: rgba(255, 255, 255, 0.75);
    border: 1px solid transparent;
    box-shadow: none;
}}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {{
    background: rgba(255, 255, 255, 0.08);
    color: {c['white']};
}}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
    background: rgba(255, 255, 255, 0.12);
    color: {c['white']};
    border: 1px solid transparent;
    border-left: 3px solid {c['data_blue']};
    border-radius: 0 {r['sm']} {r['sm']} 0;
    padding-left: 9px;
    box-shadow: none;
}}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
    background: rgba(255, 255, 255, 0.18);
}}
section[data-testid="stSidebar"] .stButton > button svg {{
    color: rgba(255, 255, 255, 0.65);
}}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] svg {{
    color: {c['white']};
}}

/* ---------------- Divider ---------------- */
.ly-divider {{
    border: none;
    border-top: 1px solid {c['divider']};
    margin: {s['sm']} 0 {s['lg']} 0;
}}

/* ---------------- Native bordered containers -> glass card ---------------- */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: {r['lg']} !important;
    border-color: {c['border']} !important;
    box-shadow: {sh['soft']};
    transition: box-shadow {m['base']};
    background: {c['glass_fill_strong']};
}}

/* ---------------- KPI tile ---------------- */
.ly-kpi-tile {{
    background: {c['glass_fill_strong']};
    border: 1px solid {c['border']};
    border-left: 3px solid var(--ly-kpi-accent, {c['navy']});
    border-radius: {r['lg']};
    padding: {s['md']} {s['sm']};
    box-shadow: {sh['soft']};
    transition: box-shadow {m['base']};
    text-align: center;
}}
.ly-kpi-tile:hover {{ box-shadow: {sh['card']}; }}
.ly-kpi-tile .kpi-value {{
    font-family: {f['heading']}; font-size: 26px; font-weight: 700; color: {c['navy']}; margin: 0;
}}
.ly-kpi-tile .kpi-label {{
    font-family: {f['body']}; font-size: 11px; font-weight: 600; color: {c['muted']};
    text-transform: uppercase; letter-spacing: 0.02em; margin: 0 0 4px 0;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}

/* ---------------- Avatar (initials, color hashed from name) ---------------- */
.ly-avatar {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    color: {c['white']};
    font-family: {f['heading']};
    font-weight: 700;
    flex-shrink: 0;
    line-height: 1;
}}

/* ---------------- Header: user chip + logout ----------------
   The old logout button was a bare power-glyph stretched to fill a narrow
   column (use_container_width on a 1-of-7 column) — wrong icon semantics
   (⏻ reads as "power off", not "log out") and an ugly forced stretch.
   Replaced with an intrinsic-width pill: avatar + name, then a real
   ghost button with a proper exit icon and a text label next to it. */
.ly-user-chip {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px 4px 4px;
    border-radius: {r['pill']};
    background: {c['navy_100']};
}}
.ly-user-chip .name {{ font-family: {f['body']}; font-size: 13px; font-weight: 600; color: {c['navy']}; white-space: nowrap; }}
div[class*="st-key-logout-btn"] {{ display: flex; justify-content: flex-end; }}
div[class*="st-key-logout-btn"] .stButton {{ flex-shrink: 0; }}
div[class*="st-key-logout-btn"] .stButton > button {{
    width: auto;
    min-width: 0;
    flex-shrink: 0;
    white-space: nowrap;
    /* Tinted red by default (not only on hover) — exit/destructive intent
       should read at a glance, the same red the app already uses for
       Reject/Cancel, instead of looking like just another neutral button. */
    background: {STATUS_TINTS['rejected']};
    color: {c['status_rejected']};
    border: 1px solid {_hex_to_rgba(c['status_rejected'], 0.35)};
    padding: 8px 14px;
    box-shadow: none;
}}
div[class*="st-key-logout-btn"] .stButton > button p {{
    white-space: nowrap;
}}
div[class*="st-key-logout-btn"] .stButton > button svg {{
    color: {c['status_rejected']} !important;
}}
div[class*="st-key-logout-btn"] .stButton > button:hover {{
    background: {c['status_rejected']};
    border-color: {c['status_rejected']};
    color: {c['white']} !important;
}}
div[class*="st-key-logout-btn"] .stButton > button:hover svg {{
    color: {c['white']} !important;
}}

/* ---------------- Section header (icon + heading, used in Analytics etc.) ---------------- */
.ly-section-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
}}
.ly-section-header .ico {{
    width: 28px; height: 28px;
    border-radius: {r['sm']};
    background: {c['navy_100']};
    color: {c['navy']};
    display: flex; align-items: center; justify-content: center;
}}

/* ---------------- Member row (Analytics per-resource availability) ---------------- */
.ly-member-row {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.ly-member-row .info {{ display: flex; flex-direction: column; gap: 2px; line-height: 1.2; }}

/* ---------------- Type chip (leave-type colored balance pill) ----------------
   Used in Analytics' per-resource row: a colored dot + label + count, using
   the exact same TYPE_COLORS hue as the pie chart legend and the calendar's
   pending cells, so all three surfaces agree on "what color is sick leave". */
.ly-type-chip {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px 3px 8px;
    border-radius: {r['pill']};
    font-family: {f['body']};
    font-size: 11px;
    font-weight: 600;
    margin: 2px 4px 2px 0;
    white-space: nowrap;
}}
.ly-type-chip .dot {{ width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }}

/* ---------------- Holiday tag pill (Holiday Calendar: Today/Past/Upcoming) ---------------- */
.ly-holiday-tag {{
    display: inline-flex;
    align-items: center;
    padding: 3px 11px;
    border-radius: {r['pill']};
    font-family: {f['body']};
    font-size: 11px;
    font-weight: 700;
}}
.ly-month-label {{
    font-family: {f['heading']};
    font-size: 13px;
    font-weight: 700;
    color: {c['navy_500']};
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin: {s['lg']} 0 {s['sm']} 2px;
}}

/* ---------------- Holiday table (Holiday Calendar list) ----------------
   Was a stack of individually st.container(border=True)'d rows — each one
   its own little card, no shared header, no sense of "this is one dataset".
   A single real <table> with column headers, hairline row dividers, and a
   hover state reads as a proper SaaS data table (Stripe/Linear pattern)
   instead of a pile of separate boxes. */
.ly-htable-wrap {{
    border: 1px solid {c['border']};
    border-radius: {r['lg']};
    box-shadow: {sh['card']};
    overflow: hidden;
    background: {c['surface']};
}}
.ly-htable {{
    width: 100%;
    border-collapse: collapse;
    font-family: {f['body']};
}}
.ly-htable thead th {{
    text-align: left;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: {c['muted']};
    background: {c['background']};
    padding: 13px 20px;
    border-bottom: 1px solid {c['divider']};
}}
.ly-htable thead th.ly-htable-col-status {{ text-align: right; }}
.ly-htable tbody tr.ly-htable-month-row td {{
    padding: 11px 20px 7px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: {c['navy_500']};
    background: {c['background']};
    border-bottom: 1px solid {c['divider']};
}}
.ly-htable tbody tr.ly-htable-row {{
    transition: background-color {m['fast']};
}}
.ly-htable tbody tr.ly-htable-row:hover {{
    background: {c['background']};
}}
.ly-htable tbody tr.ly-htable-row td {{
    padding: 14px 20px;
    border-bottom: 1px solid {c['divider']};
    vertical-align: middle;
}}
.ly-htable tbody tr.ly-htable-row:last-child td {{
    border-bottom: none;
}}
.ly-htable tbody tr.ly-htable-row.is-today td:first-child {{
    box-shadow: inset 3px 0 0 {c['status_approved']};
}}
.ly-htable-date {{ font-weight: 600; color: {c['ink']}; font-size: 14px; }}
.ly-htable-day {{ color: {c['muted']}; font-size: 12px; margin-top: 2px; }}
.ly-htable-name {{ display: flex; align-items: center; gap: 9px; color: {c['ink']}; font-size: 14px; }}
.ly-htable-name svg {{ flex-shrink: 0; color: {c['navy_500']}; }}
.ly-htable-col-status {{ text-align: right; }}

/* ---------------- Entrance animation (state-change only) ---------------- */
@keyframes ly-fade-up {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
.ly-enter {{ animation: ly-fade-up {m['slow']} both; }}

/* Inputs — Streamlit's default theme accent is red (#FF4B4B); with no
   custom theme set, that red leaks into every native input's focus/active
   border (this was the cause of the red-bordered location selectbox on
   Holiday Calendar). .streamlit/config.toml now sets primaryColor to navy
   at the source; these rules are a CSS-level backstop for the same fix. */
.stTextInput > div > div > input {{
    border-radius: {r['sm']};
}}
div[data-baseweb="select"] > div {{
    border-color: {c['border']} !important;
    box-shadow: none !important;
}}
div[data-baseweb="select"]:focus-within > div {{
    border-color: {c['navy_500']} !important;
    box-shadow: 0 0 0 1px {c['navy_500']} !important;
}}

/* ---------------- Segmented radio (leave type / half-day session) ----------------
   st.radio(horizontal=True) renders as a row of bare BaseWeb radio circles
   by default — fine functionally, flat visually. Restyle each option as a
   pill/segmented button so leave-type and session choices in the apply
   dialog read as real controls, not a stray form field. */
div[data-testid="stRadio"] > div[role="radiogroup"] {{
    gap: 8px;
    flex-wrap: wrap;
}}
div[data-testid="stRadio"] label {{
    border: 1px solid {c['border']};
    border-radius: {r['pill']};
    padding: 6px 14px 6px 10px;
    background: {c['surface']};
    transition: background-color {m['fast']}, border-color {m['fast']};
}}
div[data-testid="stRadio"] label:hover {{
    border-color: {c['navy_500']};
}}
div[data-testid="stRadio"] label[data-baseweb="radio"] div:first-child {{
    background: transparent;
}}
div[data-testid="stRadio"] label:has(input:checked) {{
    background: {c['navy_100']};
    border-color: {c['navy']};
}}
div[data-testid="stRadio"] label:has(input:checked) p {{
    color: {c['navy']};
    font-weight: 700;
}}
</style>
"""


def apply_design_system():
    """Call once near the top of each Streamlit page to inject the
    Leavely design system CSS (fonts + component classes)."""
    import streamlit as st
    st.markdown(get_css(), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Small presentational render-helpers (pure HTML strings, no business logic)
# ---------------------------------------------------------------------------

def badge_html(status: str) -> str:
    """Returns the HTML for a status pill, e.g. badge_html('approved')."""
    status = (status or "").lower()
    label = status.capitalize()
    return (
        f'<span class="ly-badge status-{status}">'
        f'<span class="dot"></span>{label}</span>'
    )


def type_chip_html(label: str, value, type_key: str) -> str:
    """Returns the HTML for a leave-type balance chip, colored to match
    that type's slice in the pie chart / calendar (TYPE_COLORS)."""
    color = TYPE_COLORS.get(type_key, COLORS["muted"])
    tint = _hex_to_rgba(color, 0.12)
    return (
        f'<span class="ly-type-chip" style="background:{tint}; color:{color};">'
        f'<span class="dot" style="background:{color};"></span>{label} {value}</span>'
    )


def holiday_tag_html(label: str, color: str) -> str:
    """Returns the HTML for the Today/Past/Upcoming pill on Holiday Calendar."""
    tint = _hex_to_rgba(color, 0.14)
    return f'<span class="ly-holiday-tag" style="background:{tint}; color:{color};">{label}</span>'


_AVATAR_PALETTE = [
    COLORS["navy"], COLORS["data_teal"], COLORS["data_violet"],
    COLORS["data_blue"], COLORS["data_amber"], COLORS["navy_500"],
]


def avatar_html(name: str, size: int = 36) -> str:
    """Returns the HTML for an initials avatar, color hashed from the name
    so the same person always gets the same color across the app."""
    name = name or "?"
    parts = name.split()
    initials = "".join(p[0] for p in parts[:2]).upper() or "?"
    color = _AVATAR_PALETTE[sum(ord(ch) for ch in name) % len(_AVATAR_PALETTE)]
    font_size = max(11, int(size * 0.38))
    return (
        f'<span class="ly-avatar" style="width:{size}px; height:{size}px; '
        f'font-size:{font_size}px; background:{color};">{initials}</span>'
    )


def kpi_tile_html(label: str, value: str, accent: str = None) -> str:
    """Returns the HTML for a KPI tile, e.g. kpi_tile_html('On Leave Today', '4').
    accent: optional hex color for the tile's left border, so a row of KPI
    tiles can be told apart at a glance (e.g. Analytics: navy/amber/green
    for Team size / On leave / Available) instead of three identical
    flat cards."""
    style = f' style="--ly-kpi-accent:{accent};"' if accent else ""
    return (
        f'<div class="ly-kpi-tile"{style}>'
        f'<p class="kpi-label">{label}</p>'
        f'<p class="kpi-value">{value}</p>'
        f'</div>'
    )


def card_open(extra_class: str = "") -> str:
    """Opening tag for a glass card. Pair with CARD_CLOSE. Used when a
    card needs to wrap Streamlit-native widgets (st.markdown(..., unsafe_allow_html=True)
    cannot wrap real widgets, so prefer st.container(border=False) + this
    class via st.markdown for visual framing of pure-HTML content)."""
    return f'<div class="ly-card hover-lift {extra_class}">'


CARD_CLOSE = "</div>"
