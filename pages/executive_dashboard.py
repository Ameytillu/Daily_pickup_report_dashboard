import streamlit as st

from utils.charts import revenue_mix
from utils.helpers import (
    fmt_money,
    fmt_number,
    fmt_occupancy,
    fmt_percent,
    forecast_status,
    metric_card,
    page_title,
)


def render(context):
    m = context.metrics
    page_title("Executive Dashboard", "Monthly OTB pace, pickup, segment mix, and forecast status.")

    cols = st.columns(4)
    with cols[0]:
        metric_card("OTB Rooms", fmt_number(m["otb_rooms"]), f"Pickup {fmt_number(m['rooms_pickup'])}")
    with cols[1]:
        metric_card("OTB Revenue", fmt_money(m["otb_revenue"]), f"Pickup {fmt_money(m['revenue_pickup'])}")
    with cols[2]:
        metric_card("ADR", fmt_money(m["adr"]), f"RevPAR {fmt_money(m['revpar'])}")
    with cols[3]:
        metric_card("Occupancy", fmt_occupancy(m["occupancy_pct"]), "433 room inventory")

    cols = st.columns(4)
    status, css = forecast_status(m["revenue_needed"])
    with cols[0]:
        metric_card("Revenue Gap", fmt_money(m["revenue_gap"]), status, css)
    with cols[1]:
        metric_card("Forecast Achievement", fmt_percent(m["forecast_achievement_pct"]), "Revenue forecast")
    with cols[2]:
        status, css = forecast_status(m["revenue_needed"])
        metric_card("Revenue Needed", fmt_money(m["revenue_needed"]), status, css)
    with cols[3]:
        status, css = forecast_status(m["rooms_needed"])
        metric_card("Rooms Needed", fmt_number(m["rooms_needed"]), status, css)

    left, right = st.columns([1, 1])
    with left:
        st.plotly_chart(
            revenue_mix(m["transient_revenue"], m["group_revenue"], m["other_revenue"]),
            use_container_width=True,
        )
    with right:
        st.markdown("#### Pickup Summary")
        p1, p2 = st.columns(2)
        p1.metric("Rooms Pickup", fmt_number(m["rooms_pickup"]))
        p2.metric("Revenue Pickup", fmt_money(m["revenue_pickup"]))
        p1.metric("Transient Rooms Pickup", fmt_number(m["transient_rooms_pickup"]))
        p2.metric("Transient Revenue Pickup", fmt_money(m["transient_revenue_pickup"]))
        p1.metric("Group Rooms Pickup", fmt_number(m["group_rooms_pickup"]))
        p2.metric("Group Revenue Pickup", fmt_money(m["group_revenue_pickup"]))


