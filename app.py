import streamlit as st

from pages.alerts_dashboard import render as render_alerts
from pages.executive_dashboard import render as render_executive
from pages.export_center import render as render_export
from pages.forecast_tracker import render as render_forecast
from pages.group_dashboard import render as render_group
from pages.pace_analysis import render as render_pace
from pages.pickup_analysis import render as render_pickup
from pages.pickup_calendar import render as render_calendar
from pages.projection_dashboard import render as render_projection
from pages.transient_dashboard import render as render_transient
from utils.calculations import build_dashboard_context
from utils.data_loader import load_workbook
from utils.helpers import apply_theme, show_error_box


st.set_page_config(
    page_title="Hotel Revenue Pickup & Forecast Dashboard",
    page_icon="assets/favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()

PAGES = {
    "Executive Dashboard": render_executive,
    "Pickup Analysis": render_pickup,
    "Pace Analysis": render_pace,
    "Transient Business": render_transient,
    "Group Business": render_group,
    "Forecast Tracker": render_forecast,
    "Month-End Projection": render_projection,
    "Pickup Calendar": render_calendar,
    "Opportunities & Alerts": render_alerts,
    "Export Center": render_export,
}


def render_shell():
    st.sidebar.image("assets/logo.svg", use_container_width=True)
    st.sidebar.markdown("### Daily Revenue Meeting")
    uploaded_file = st.sidebar.file_uploader(
        "Upload Daily Pickup Excel Workbook",
        type=["xlsx", "xlsm"],
        help="Each worksheet should represent one report day.",
    )

    if not uploaded_file:
        st.markdown(
            """
            <section class="hero">
                <div>
                    <p class="eyebrow">433 Room Resort</p>
                    <h1>Hotel Revenue Management Pickup & Forecast Dashboard</h1>
                    <p>Upload the monthly Daily Pickup workbook to analyze pace, pickup, segment mix, forecast gaps, projections, and revenue risks.</p>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.info("Reads every worksheet dynamically and lets users compare prior and current report days.")
        c2.info("Calculates pickup, forecast achievement, business needed, and month-end projections.")
        c3.info("Exports executive PDF and Excel summary reports for daily revenue meetings.")
        return

    try:
        workbook = load_workbook(uploaded_file)
    except Exception as exc:
        show_error_box("Invalid workbook", str(exc))
        return

    if len(workbook.sheet_names) < 2:
        show_error_box("Missing report days", "The workbook must contain at least two usable worksheets.")
        return

    st.sidebar.divider()
    prev_index = max(0, len(workbook.sheet_names) - 2)
    current_index = max(0, len(workbook.sheet_names) - 1)
    previous_sheet = st.sidebar.selectbox("Previous Report Day", workbook.sheet_names, index=prev_index)
    current_sheet = st.sidebar.selectbox("Current Report Day", workbook.sheet_names, index=current_index)

    if previous_sheet == current_sheet:
        show_error_box("Select two different reports", "Previous Report Day and Current Report Day cannot be the same worksheet.")
        return

    try:
        context = build_dashboard_context(workbook, previous_sheet, current_sheet)
    except Exception as exc:
        show_error_box("Unable to calculate dashboard metrics", str(exc))
        return

    st.sidebar.divider()
    page = st.sidebar.radio("Dashboard Page", list(PAGES.keys()), label_visibility="collapsed")
    st.sidebar.caption(f"Workbook sheets detected: {len(workbook.sheet_names)}")
    st.sidebar.caption(f"Comparing {previous_sheet} to {current_sheet}")

    PAGES[page](context)


if __name__ == "__main__":
    render_shell()
