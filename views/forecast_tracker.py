import streamlit as st

from utils.charts import gauge, progress_bars, variance_chart
from utils.helpers import page_title


def render(context):
    page_title("Forecast Tracker", "Forecast, current OTB, gap, achievement, and business needed.")
    table = context.forecast_table.copy()
    st.dataframe(table, use_container_width=True)

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(gauge(context.metrics["forecast_achievement_pct"], "Revenue Achievement"), use_container_width=True)
    with g2:
        st.plotly_chart(gauge(context.metrics["rooms_achievement_pct"], "Rooms Achievement"), use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(progress_bars(table), use_container_width=True)
    with right:
        st.plotly_chart(variance_chart(table), use_container_width=True)


