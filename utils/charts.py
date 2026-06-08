from __future__ import annotations

import calendar

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


COLORS = {
    "Revenue": "#15803d",
    "ADR": "#2563eb",
    "Occupancy": "#ea580c",
    "Transient": "#7c3aed",
    "Group": "#0f766e",
    "Forecast Gap": "#dc2626",
    "Achievement": "#15803d",
    "Neutral": "#475467",
}


def line_chart(df: pd.DataFrame, y, title: str, color=None):
    fig = px.line(df, x="date", y=y, markers=True, title=title, color=color)
    return style_fig(fig)


def bar_chart(df: pd.DataFrame, x, y, title: str, color=None):
    fig = px.bar(df, x=x, y=y, title=title, color=color)
    return style_fig(fig)


def revenue_mix(transient: float, group: float, other: float):
    fig = px.pie(
        names=["Transient", "Group", "Other"],
        values=[max(transient, 0), max(group, 0), max(other, 0)],
        title="Revenue Mix",
        hole=0.52,
        color=["Transient", "Group", "Other"],
        color_discrete_map={"Transient": COLORS["Transient"], "Group": COLORS["Group"], "Other": COLORS["Neutral"]},
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return style_fig(fig, height=360)


def gauge(value: float, title: str, suffix: str = "%", max_value: float = 100):
    safe_value = 0 if pd.isna(value) else value
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=safe_value,
            number={"suffix": suffix},
            title={"text": title},
            gauge={
                "axis": {"range": [0, max_value]},
                "bar": {"color": COLORS["Achievement"]},
                "steps": [
                    {"range": [0, max_value * 0.65], "color": "#fee2e2"},
                    {"range": [max_value * 0.65, max_value * 0.9], "color": "#fef3c7"},
                    {"range": [max_value * 0.9, max_value], "color": "#dcfce7"},
                ],
            },
        )
    )
    return style_fig(fig, height=260)


def calendar_heatmap(pickup: pd.DataFrame, metric: str = "revenue_pickup"):
    if pickup.empty:
        return go.Figure()
    df = pickup[["date", metric, "rooms_pickup", "revenue_pickup", "adr_pickup"]].copy()
    df["day"] = df["date"].dt.day
    df["weekday"] = df["date"].dt.weekday
    df["week"] = ((df["day"] + df["date"].dt.to_period("M").dt.start_time.dt.weekday - 1) // 7) + 1
    df["hover"] = (
        df["date"].dt.strftime("%b %d")
        + "<br>Rooms Pickup: "
        + df["rooms_pickup"].round(0).astype(str)
        + "<br>Revenue Pickup: $"
        + df["revenue_pickup"].round(0).astype(str)
        + "<br>ADR Pickup: $"
        + df["adr_pickup"].round(0).astype(str)
    )
    pivot = df.pivot_table(index="week", columns="weekday", values=metric, aggfunc="sum")
    text = df.pivot_table(index="week", columns="weekday", values="day", aggfunc="first")
    hover = df.pivot_table(index="week", columns="weekday", values="hover", aggfunc="first")
    pivot = pivot.reindex(columns=range(7))
    text = text.reindex(columns=range(7))
    hover = hover.reindex(columns=range(7))
    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=[calendar.day_abbr[i] for i in range(7)],
            y=pivot.index,
            text=text.values,
            texttemplate="%{text}",
            hovertext=hover.values,
            hoverinfo="text",
            colorscale=[[0, "#dc2626"], [0.45, "#facc15"], [0.65, "#bbf7d0"], [1, "#166534"]],
            colorbar={"title": metric.replace("_", " ").title()},
        )
    )
    fig.update_yaxes(autorange="reversed", title="")
    return style_fig(fig, height=520)


def variance_chart(table: pd.DataFrame):
    df = table.dropna(subset=["Gap"]).copy()
    fig = px.bar(
        df,
        x="Metric",
        y="Gap",
        title="Forecast Variance",
        color=df["Gap"].apply(lambda x: "Ahead" if x >= 0 else "Behind"),
        color_discrete_map={"Ahead": COLORS["Achievement"], "Behind": COLORS["Forecast Gap"]},
    )
    return style_fig(fig)


def progress_bars(table: pd.DataFrame):
    df = table.dropna(subset=["Achievement %"]).copy()
    fig = px.bar(
        df,
        x="Achievement %",
        y="Metric",
        orientation="h",
        range_x=[0, max(110, float(np.nanmax(df["Achievement %"])) if not df.empty else 100)],
        title="Forecast Achievement",
        color="Metric",
    )
    return style_fig(fig)


def style_fig(fig, height: int = 390):
    fig.update_layout(
        height=height,
        margin=dict(l=24, r=24, t=54, b=28),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#172033"),
        title_font=dict(size=17),
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=False, linecolor="#d9e2ec")
    fig.update_yaxes(gridcolor="#edf2f7", linecolor="#d9e2ec")
    return fig
