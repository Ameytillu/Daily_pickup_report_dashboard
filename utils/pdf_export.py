from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.helpers import fmt_money, fmt_number, fmt_percent


def build_executive_pdf(context) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Hotel Revenue Management Pickup & Forecast Dashboard", styles["Title"]),
        Paragraph(f"Report comparison: {context.previous_sheet} to {context.current_sheet}", styles["Normal"]),
        Spacer(1, 0.2 * inch),
    ]

    metrics = context.metrics
    kpi_rows = [
        ["OTB Rooms", fmt_number(metrics["otb_rooms"]), "OTB Revenue", fmt_money(metrics["otb_revenue"])],
        ["ADR", fmt_money(metrics["adr"]), "Occupancy", fmt_percent(metrics["occupancy_pct"] * 100)],
        ["Rooms Pickup", fmt_number(metrics["rooms_pickup"]), "Revenue Pickup", fmt_money(metrics["revenue_pickup"])],
        ["Revenue Gap", fmt_money(metrics["revenue_gap"]), "Forecast Achievement", fmt_percent(metrics["forecast_achievement_pct"])],
    ]
    story.append(_styled_table(kpi_rows))
    story.append(Spacer(1, 0.25 * inch))

    forecast_rows = [["Metric", "Forecast", "Current OTB", "Gap", "Achievement %", "Needed"]]
    for _, row in context.forecast_table.iterrows():
        forecast_rows.append(
            [
                row["Metric"],
                fmt_money(row["Forecast"]) if "Revenue" in row["Metric"] or row["Metric"] == "ADR" else fmt_number(row["Forecast"]),
                fmt_money(row["Current OTB"]) if "Revenue" in row["Metric"] or row["Metric"] == "ADR" else fmt_number(row["Current OTB"]),
                fmt_money(row["Gap"]) if "Revenue" in row["Metric"] or row["Metric"] == "ADR" else fmt_number(row["Gap"]),
                fmt_percent(row["Achievement %"]),
                fmt_money(row["Needed"]) if "Revenue" in row["Metric"] or row["Metric"] == "ADR" else fmt_number(row["Needed"]),
            ]
        )
    story.append(Paragraph("Forecast Tracker", styles["Heading2"]))
    story.append(_styled_table(forecast_rows, header=True))
    doc.build(story)
    return buffer.getvalue()


def _styled_table(rows, header: bool = False):
    table = Table(rows, hAlign="LEFT")
    style = [
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9e2ec")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#172033")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    table.setStyle(TableStyle(style))
    return table
