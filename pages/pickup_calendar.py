import streamlit as st

from utils.charts import calendar_heatmap
from utils.helpers import page_title


def render(context):
    page_title("Pickup Calendar Heatmap", "Monthly calendar view colored by pickup strength.")
    metric = st.selectbox("Heatmap Metric", ["revenue_pickup", "rooms_pickup", "adr_pickup"], format_func=lambda x: x.replace("_", " ").title())
    st.plotly_chart(calendar_heatmap(context.pickup, metric), use_container_width=True)


