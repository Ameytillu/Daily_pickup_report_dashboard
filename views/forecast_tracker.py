import pandas as pd
import streamlit as st

from utils.charts import gauge, progress_bars, variance_chart
from utils.helpers import page_title


def render(context):
    page_title("Forecast Tracker", "Forecast, current OTB, gap, achievement, and business needed.")
    table = context.forecast_table.copy()
    st.dataframe(_format_forecast_table(table), use_container_width=True)

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(gauge(context.metrics["forecast_achievement_pct"], "Revenue Achievement"), use_container_width=True)
    with g2:
        if pd.isna(context.metrics["forecast_rooms"]):
            st.markdown(
                """
                <div class="metric-card">
                    <div class="label">Rooms Achievement</div>
                    <div class="value">N/A</div>
                    <div class="note">No rooms forecast set</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.plotly_chart(gauge(context.metrics["rooms_achievement_pct"], "Rooms Achievement"), use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(progress_bars(table), use_container_width=True)
    with right:
        st.plotly_chart(variance_chart(table), use_container_width=True)


def _format_forecast_table(table):
    display = table.copy().astype(object)
    for idx, row in table.iterrows():
        metric = row["Metric"]
        is_money = "Revenue" in metric or metric == "ADR"
        for col in ["Forecast", "Current OTB", "Gap", "Needed"]:
            display.at[idx, col] = _format_money_or_number(row[col], is_money)
        for col in ["Achievement %", "Pace-Adjusted Expected %", "vs Expected"]:
            display.at[idx, col] = _format_percent(row[col])
    return display.style.map(lambda value: "color: #98a2b3;" if value == "—" else "")


def _format_money_or_number(value, is_money: bool):
    if pd.isna(value):
        return "—"
    return f"${value:,.0f}" if is_money else f"{value:,.0f}"


def _format_percent(value):
    if pd.isna(value):
        return "—"
    return f"{value:,.1f}%"
