"""Plotly chart builders — donut balance chart (employee/manager personal
view) and team capacity bar/heatmap (manager analytics).

Leave-status colors (pending/approved/cancelled/rejected/holiday) are never
reused here. These are aggregate/type charts, not status indicators, so
per the design system's rule they use the navy-family palette only.
"""
import plotly.graph_objects as go

from design_tokens import COLORS, FONTS, TYPE_COLORS

# Maternity/paternity are real, applyable leave types (see modals.py) but are
# deliberately excluded from this chart — they're statutory pools, not part
# of the discretionary day-to-day mix the donut is meant to visualize.
PIE_CHART_TYPES = ["casual", "sick", "earned", "floating"]
_TYPE_LABELS = {
    "casual": "Casual", "sick": "Sick", "earned": "Earned", "floating": "Floating",
    "maternity": "Maternity", "paternity": "Paternity",
}


def donut_balance_chart(balance: dict) -> go.Figure:
    types = PIE_CHART_TYPES
    values = [balance.get(t, 0) for t in types]
    labels = [_TYPE_LABELS[t] for t in types]
    colors = [TYPE_COLORS[t] for t in types]
    total = sum(values)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.66,
                marker=dict(colors=colors, line=dict(color=COLORS["white"], width=2)),
                textinfo="value",
                textfont=dict(family=FONTS["body"], size=13, color=COLORS["white"]),
                hovertemplate="%{label}: %{value} day(s)<extra></extra>",
                sort=False,
            )
        ]
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5,
            font=dict(family=FONTS["body"], size=12, color=COLORS["slate"]),
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        annotations=[
            dict(
                text=f"<b>{total}</b><br><span style='font-size:11px;color:{COLORS['muted']}'>days left</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(family=FONTS["heading"], size=22, color=COLORS["navy"]),
            )
        ],
    )
    return fig


def team_capacity_bar(capacity_days: list) -> go.Figure:
    """capacity_days: list of {"date", "total", "on_leave", "available"}."""
    day_labels = [d["date"][-2:] for d in capacity_days]
    full_dates = [d["date"] for d in capacity_days]
    available = [d["available"] for d in capacity_days]
    on_leave = [d["on_leave"] for d in capacity_days]

    fig = go.Figure()
    fig.add_bar(
        x=day_labels, y=available, name="Available",
        marker_color=COLORS["navy_100"],
        customdata=full_dates,
        hovertemplate="%{customdata}<br>Available: %{y}<extra></extra>",
    )
    fig.add_bar(
        x=day_labels, y=on_leave, name="On leave",
        marker_color=COLORS["navy"],
        customdata=full_dates,
        hovertemplate="%{customdata}<br>On leave: %{y}<extra></extra>",
    )
    fig.update_layout(
        barmode="stack",
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            font=dict(family=FONTS["body"], size=12, color=COLORS["slate"]),
        ),
        xaxis=dict(showgrid=False, tickfont=dict(family=FONTS["body"], size=11, color=COLORS["muted"])),
        yaxis=dict(showgrid=True, gridcolor=COLORS["divider"], tickfont=dict(family=FONTS["body"], size=11, color=COLORS["muted"])),
        font=dict(family=FONTS["body"]),
    )
    return fig


def team_capacity_heatmap(capacity_days: list) -> go.Figure:
    """Single-row heatmap of on-leave count across the month, navy sequential scale."""
    day_labels = [d["date"][-2:] for d in capacity_days]
    full_dates = [d["date"] for d in capacity_days]
    on_leave = [d["on_leave"] for d in capacity_days]

    fig = go.Figure(
        data=go.Heatmap(
            z=[on_leave],
            x=day_labels,
            y=["On leave"],
            customdata=[full_dates],
            colorscale=[[0, COLORS["navy_100"]], [1, COLORS["navy"]]],
            showscale=True,
            colorbar=dict(thickness=10, len=0.8, tickfont=dict(family=FONTS["body"], size=10, color=COLORS["muted"])),
            hovertemplate="%{customdata}<br>On leave: %{z}<extra></extra>",
            xgap=3,
            ygap=3,
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=140,
        xaxis=dict(showgrid=False, tickfont=dict(family=FONTS["body"], size=10, color=COLORS["muted"])),
        yaxis=dict(showgrid=False, tickfont=dict(family=FONTS["body"], size=11, color=COLORS["muted"])),
        font=dict(family=FONTS["body"]),
    )
    return fig
