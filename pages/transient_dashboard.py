import streamlit as st

from utils.charts import line_chart
from utils.helpers import fmt_money, fmt_number, metric_card, page_title


def render(context):
    m = context.metrics
    page_title("Transient Business Dashboard", "Transient rooms, revenue, ADR, pickup, and forecast variance.")
    cols = st.columns(5)
    cols[0].metric("Transient Rooms", fmt_number(m["transient_rooms"]))
    cols[1].metric("Transient Revenue", fmt_money(m["transient_revenue"]))
    cols[2].metric("Transient ADR", fmt_money(m["transient_adr"]))
    cols[3].metric("Transient Pickup", fmt_money(m["transient_revenue_pickup"]))
    with cols[4]:
        metric_card("Forecast Gap", fmt_money(m["transient_revenue_gap"]))

    pace = context.current_pace
    pickup = context.pickup
    tabs = st.tabs(["Daily Trend", "Pickup Trend", "Forecast Variance", "Revenue Trend", "ADR Trend"])
    with tabs[0]:
        st.plotly_chart(line_chart(pace, "transient_rooms", "Transient Daily Room Trend"), use_container_width=True)
    with tabs[1]:
        st.plotly_chart(line_chart(pickup, "transient_revenue_pickup", "Transient Pickup Trend"), use_container_width=True)
    with tabs[2]:
        pace = pace.copy()
        forecast = m["forecast_transient_revenue"]
        pace["forecast_variance"] = pace["transient_revenue"].cumsum() - forecast
        st.plotly_chart(line_chart(pace, "forecast_variance", "Transient Forecast Variance Trend"), use_container_width=True)
    with tabs[3]:
        st.plotly_chart(line_chart(pace, "transient_revenue", "Transient Revenue Trend"), use_container_width=True)
    with tabs[4]:
        st.plotly_chart(line_chart(pace, "transient_adr", "Transient ADR Trend"), use_container_width=True)


