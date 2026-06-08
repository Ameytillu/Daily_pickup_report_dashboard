import streamlit as st

from utils.forecasting import project_month_end
from utils.helpers import fmt_money, fmt_number, fmt_occupancy, metric_card, page_title


def render(context):
    page_title("Month-End Projection", "Linear trend and pickup-based month-end forecast methods.")
    method = st.radio("Projection Method", ["Linear Trend", "Pickup Based Projection"], horizontal=True)
    projection = project_month_end(context.current_pace, context.pickup, method)
    if not projection:
        st.info("No projection can be calculated for the selected report.")
        return

    cols = st.columns(5)
    with cols[0]:
        metric_card("Projected Rooms", fmt_number(projection["Projected Rooms"]))
    with cols[1]:
        metric_card("Projected Revenue", fmt_money(projection["Projected Revenue"]))
    with cols[2]:
        metric_card("Projected ADR", fmt_money(projection["Projected ADR"]))
    with cols[3]:
        metric_card("Projected Occupancy", fmt_occupancy(projection["Projected Occupancy"]))
    with cols[4]:
        metric_card("Projected RevPAR", fmt_money(projection["Projected RevPAR"]), f"Confidence: {projection['Confidence']}")

    st.info(f"Confidence indicator: {projection['Confidence']}. Method selected: {method}.")

