import streamlit as st

from utils.charts import line_chart
from utils.helpers import fmt_money, fmt_number, metric_card, page_title


def render(context):
    m = context.metrics
    page_title("Group Business Dashboard", "Group rooms, revenue, ADR, pickup, and forecast variance.")
    cols = st.columns(5)
    cols[0].metric("Group Rooms", fmt_number(m["group_rooms"]))
    cols[1].metric("Group Revenue", fmt_money(m["group_revenue"]))
    cols[2].metric("Group ADR", fmt_money(m["group_adr"]))
    cols[3].metric("Group Pickup", fmt_money(m["group_revenue_pickup"]))
    with cols[4]:
        metric_card("Forecast Gap", fmt_money(m["group_revenue_gap"]))

    pace = context.current_pace
    pickup = context.pickup
    tabs = st.tabs(["Daily Trend", "Pickup Trend", "Forecast Variance", "Revenue Trend", "ADR Trend"])
    with tabs[0]:
        st.plotly_chart(line_chart(pace, "group_rooms", "Group Daily Room Trend"), use_container_width=True)
    with tabs[1]:
        st.plotly_chart(line_chart(pickup, "group_revenue_pickup", "Group Pickup Trend"), use_container_width=True)
    with tabs[2]:
        pace = pace.copy()
        forecast = m["forecast_group_revenue"]
        pace["forecast_variance"] = pace["group_revenue"].cumsum() - forecast
        st.plotly_chart(line_chart(pace, "forecast_variance", "Group Forecast Variance Trend"), use_container_width=True)
    with tabs[3]:
        st.plotly_chart(line_chart(pace, "group_revenue", "Group Revenue Trend"), use_container_width=True)
    with tabs[4]:
        st.plotly_chart(line_chart(pace, "group_adr", "Group ADR Trend"), use_container_width=True)


