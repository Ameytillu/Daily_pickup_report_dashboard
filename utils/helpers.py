from __future__ import annotations

import math

import pandas as pd
import streamlit as st


MONEY_FIELDS = {
    "revenue",
    "adr",
    "revpar",
    "revenue_pickup",
    "adr_pickup",
    "transient_revenue",
    "transient_adr",
    "transient_revenue_pickup",
    "group_revenue",
    "group_adr",
    "group_revenue_pickup",
    "forecast_revenue",
    "forecast_transient_revenue",
    "forecast_group_revenue",
    "revenue_gap",
    "revenue_needed",
    "transient_revenue_gap",
    "group_revenue_gap",
}


def apply_theme():
    st.markdown(
        """
        <style>
        :root {
            --rm-green: #15803d;
            --rm-blue: #2563eb;
            --rm-orange: #ea580c;
            --rm-purple: #7c3aed;
            --rm-teal: #0f766e;
            --rm-red: #dc2626;
            --rm-ink: #172033;
            --rm-muted: #667085;
            --rm-line: #d9e2ec;
            --rm-panel: #ffffff;
            --rm-bg: #f6f8fb;
        }
        .stApp { background: var(--rm-bg); color: var(--rm-ink); }
        [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--rm-line); }
        .hero {
            min-height: 360px;
            display: flex;
            align-items: center;
            padding: 56px 48px;
            color: white;
            background:
                linear-gradient(90deg, rgba(15, 35, 52, .88), rgba(15, 35, 52, .42)),
                url("https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1800&q=80");
            background-size: cover;
            background-position: center;
            border-bottom: 1px solid rgba(255,255,255,.18);
        }
        .hero h1 { max-width: 780px; font-size: 44px; line-height: 1.08; margin: 0 0 16px; letter-spacing: 0; }
        .hero p { max-width: 680px; font-size: 17px; margin: 0; }
        .eyebrow { text-transform: uppercase; font-size: 12px !important; font-weight: 700; letter-spacing: 0 !important; opacity: .9; margin-bottom: 14px !important; }
        .metric-card {
            background: var(--rm-panel);
            border: 1px solid var(--rm-line);
            border-radius: 8px;
            padding: 16px;
            min-height: 114px;
            box-shadow: 0 8px 24px rgba(23, 32, 51, .05);
        }
        .metric-card .label { color: var(--rm-muted); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0; }
        .metric-card .value { font-size: 26px; line-height: 1.2; font-weight: 800; margin-top: 8px; overflow-wrap: anywhere; }
        .metric-card .note { font-size: 12px; color: var(--rm-muted); margin-top: 8px; }
        .status-ahead { color: var(--rm-green); font-weight: 800; }
        .status-behind { color: var(--rm-red); font-weight: 800; }
        .section-title { font-size: 22px; font-weight: 800; margin: 8px 0 14px; }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--rm-line);
            border-radius: 8px;
            padding: 14px 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, subtitle: str):
    st.markdown(f"## {title}")
    st.caption(subtitle)


def metric_card(label: str, value, note: str = "", status: str | None = None):
    css = ""
    if status == "ahead":
        css = "status-ahead"
    elif status == "behind":
        css = "status-behind"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value {css}">{value}</div>
            <div class="note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_error_box(title: str, message: str):
    st.error(f"{title}: {message}")


def fmt_money(value) -> str:
    if _missing(value):
        return "-"
    return f"${value:,.0f}"


def fmt_number(value) -> str:
    if _missing(value):
        return "-"
    return f"{value:,.0f}"


def fmt_percent(value) -> str:
    if _missing(value):
        return "-"
    return f"{value:,.1f}%"


def fmt_occupancy(value) -> str:
    if _missing(value):
        return "-"
    return f"{value * 100:,.1f}%"


def forecast_status(needed) -> tuple[str, str]:
    if _missing(needed):
        return "Not available", ""
    return ("Ahead of Forecast", "ahead") if needed <= 0 else ("Behind Forecast", "behind")


def format_by_metric(metric: str, value) -> str:
    key = metric.lower().replace(" ", "_")
    if "occupancy" in key:
        return fmt_occupancy(value)
    if "achievement" in key:
        return fmt_percent(value)
    if any(part in key for part in ["revenue", "adr", "revpar", "gap", "needed", "forecast"]):
        return fmt_money(value)
    return fmt_number(value)


def _missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value)
