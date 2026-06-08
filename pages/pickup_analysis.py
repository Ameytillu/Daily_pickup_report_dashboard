import streamlit as st

from utils.charts import line_chart
from utils.helpers import page_title


METRICS = {
    "Rooms Pickup": "rooms_pickup",
    "Revenue Pickup": "revenue_pickup",
    "ADR Pickup": "adr_pickup",
    "Transient Rooms Pickup": "transient_rooms_pickup",
    "Transient Revenue Pickup": "transient_revenue_pickup",
    "Transient ADR Pickup": "transient_adr_pickup",
    "Group Rooms Pickup": "group_rooms_pickup",
    "Group Revenue Pickup": "group_revenue_pickup",
    "Group ADR Pickup": "group_adr_pickup",
}


def render(context):
    page_title("Pickup Analysis", "Daily pickup activity by metric and segment.")
    df = context.pickup.copy()
    if df.empty:
        st.info("No pickup rows are available for the selected report.")
        return

    min_date, max_date = df["date"].min().date(), df["date"].max().date()
    c1, c2, c3 = st.columns([1, 1, 1])
    date_range = c1.date_input("Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)
    metric_label = c2.selectbox("Metric Selector", list(METRICS.keys()))
    segment = c3.selectbox("Segment Selector", ["All", "Transient", "Group"])

    if isinstance(date_range, tuple) and len(date_range) == 2:
        df = df[(df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])]

    metric = METRICS[metric_label]
    if segment == "Transient" and not metric.startswith("transient"):
        metric = "transient_" + metric
    if segment == "Group" and not metric.startswith("group"):
        metric = "group_" + metric
    if metric not in df.columns:
        metric = METRICS[metric_label]

    tabs = st.tabs(["Selected Metric", "Rooms", "Revenue", "ADR", "All Pickup Data"])
    with tabs[0]:
        st.plotly_chart(line_chart(df, metric, metric.replace("_", " ").title()), use_container_width=True)
    with tabs[1]:
        st.plotly_chart(line_chart(df, ["rooms_pickup", "transient_rooms_pickup", "group_rooms_pickup"], "Rooms Pickup Trend"), use_container_width=True)
    with tabs[2]:
        st.plotly_chart(line_chart(df, ["revenue_pickup", "transient_revenue_pickup", "group_revenue_pickup"], "Revenue Pickup Trend"), use_container_width=True)
    with tabs[3]:
        st.plotly_chart(line_chart(df, ["adr_pickup", "transient_adr_pickup", "group_adr_pickup"], "ADR Pickup Trend"), use_container_width=True)
    with tabs[4]:
        st.dataframe(df, use_container_width=True)


