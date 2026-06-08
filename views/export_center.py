from io import BytesIO

import pandas as pd
import streamlit as st

from utils.helpers import page_title
from utils.pdf_export import build_executive_pdf


def render(context):
    page_title("Export Center", "Generate executive PDF and Excel summary reports.")

    pdf_bytes = build_executive_pdf(context)
    st.download_button(
        "Download Executive PDF Report",
        data=pdf_bytes,
        file_name="executive_revenue_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    excel_bytes = _build_excel_summary(context)
    st.download_button(
        "Download Excel Summary Report",
        data=excel_bytes,
        file_name="hotel_revenue_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.markdown("#### Included Export Sections")
    st.write("KPI Summary, Forecast Summary, Pickup Summary, Current Pace, Calculated Pickup, Revenue Mix, Forecast Tracker, and Month-End Projection inputs.")


def _build_excel_summary(context) -> bytes:
    output = BytesIO()
    kpis = pd.DataFrame([context.metrics]).T.reset_index()
    kpis.columns = ["Metric", "Value"]
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        kpis.to_excel(writer, sheet_name="KPI Summary", index=False)
        context.forecast_table.to_excel(writer, sheet_name="Forecast Summary", index=False)
        context.pickup.to_excel(writer, sheet_name="Pickup Summary", index=False)
        context.current_pace.to_excel(writer, sheet_name="Current Pace", index=False)
        context.calculated_pickup.to_excel(writer, sheet_name="Calculated Pickup", index=False)
    return output.getvalue()
