from __future__ import annotations

from io import BytesIO
import math

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.helpers import fmt_money, fmt_number, fmt_percent

GREEN = colors.HexColor("#15803D")
BLUE = colors.HexColor("#2563EB")
ORANGE = colors.HexColor("#EA580C")
PURPLE = colors.HexColor("#7C3AED")
TEAL = colors.HexColor("#0F766E")
RED = colors.HexColor("#DC2626")
INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#667085")
LINE = colors.HexColor("#D9E2EC")


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
    story.append(Paragraph("Executive KPI Summary", styles["Heading2"]))
    story.append(_styled_table(kpi_rows))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Segment Scorecard", styles["Heading2"]))
    story.append(_styled_table(_segment_scorecard(metrics), header=True))
    story.append(Spacer(1, 0.18 * inch))

    story.append(Paragraph("Pickup Scorecard", styles["Heading2"]))
    story.append(_styled_table(_pickup_scorecard(metrics), header=True))
    story.append(Spacer(1, 0.2 * inch))

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
    story.append(PageBreak())

    pace = context.current_pace
    pickup = context.pickup
    story.append(Paragraph("Rooms Pace by Segment", styles["Heading2"]))
    story.append(
        _line_chart(
            pace,
            {"Transient Rooms": ("transient_rooms", PURPLE), "Group Rooms": ("group_rooms", TEAL)},
            y_title="Rooms",
        )
    )
    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph("Revenue Pace by Segment", styles["Heading2"]))
    story.append(
        _line_chart(
            pace,
            {"Transient Revenue": ("transient_revenue", PURPLE), "Group Revenue": ("group_revenue", TEAL)},
            y_title="Revenue",
            currency=True,
        )
    )
    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph("ADR Pace by Segment", styles["Heading2"]))
    story.append(
        _line_chart(
            pace,
            {"Transient ADR": ("transient_adr", BLUE), "Group ADR": ("group_adr", ORANGE)},
            y_title="ADR",
            currency=True,
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("Revenue Pickup by Segment", styles["Heading2"]))
    story.append(
        _line_chart(
            pickup,
            {"Transient Revenue Pickup": ("transient_revenue_pickup", PURPLE), "Group Revenue Pickup": ("group_revenue_pickup", TEAL)},
            y_title="Revenue Pickup",
            currency=True,
        )
    )
    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph("Rooms Pickup by Segment", styles["Heading2"]))
    story.append(
        _line_chart(
            pickup,
            {"Transient Rooms Pickup": ("transient_rooms_pickup", PURPLE), "Group Rooms Pickup": ("group_rooms_pickup", TEAL)},
            y_title="Rooms Pickup",
        )
    )
    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph("Forecast Variance by Segment", styles["Heading2"]))
    story.append(_variance_bar_chart(metrics))
    doc.build(story)
    return buffer.getvalue()


def _segment_scorecard(metrics: dict) -> list[list[str]]:
    return [
        ["Segment", "Rooms", "Revenue", "ADR", "Forecast", "Gap", "Needed"],
        [
            "Transient",
            fmt_number(metrics["transient_rooms"]),
            fmt_money(metrics["transient_revenue"]),
            fmt_money(metrics["transient_adr"]),
            fmt_money(metrics["forecast_transient_revenue"]),
            fmt_money(metrics["transient_revenue_gap"]),
            fmt_money(metrics["transient_revenue_needed"]),
        ],
        [
            "Group",
            fmt_number(metrics["group_rooms"]),
            fmt_money(metrics["group_revenue"]),
            fmt_money(metrics["group_adr"]),
            fmt_money(metrics["forecast_group_revenue"]),
            fmt_money(metrics["group_revenue_gap"]),
            fmt_money(metrics["group_revenue_needed"]),
        ],
        [
            "Total",
            fmt_number(metrics["otb_rooms"]),
            fmt_money(metrics["otb_revenue"]),
            fmt_money(metrics["adr"]),
            fmt_money(metrics["forecast_revenue"]),
            fmt_money(metrics["revenue_gap"]),
            fmt_money(metrics["revenue_needed"]),
        ],
    ]


def _pickup_scorecard(metrics: dict) -> list[list[str]]:
    return [
        ["Segment", "Rooms Pickup", "Revenue Pickup", "Pickup ADR"],
        ["Transient", fmt_number(metrics["transient_rooms_pickup"]), fmt_money(metrics["transient_revenue_pickup"]), fmt_money(metrics["transient_adr_pickup"])],
        ["Group", fmt_number(metrics["group_rooms_pickup"]), fmt_money(metrics["group_revenue_pickup"]), fmt_money(metrics["group_adr_pickup"])],
        ["Total", fmt_number(metrics["rooms_pickup"]), fmt_money(metrics["revenue_pickup"]), fmt_money(metrics["adr_pickup"])],
    ]


def _styled_table(rows, header: bool = False, col_widths=None):
    table = Table(rows, hAlign="LEFT", colWidths=col_widths)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.25, LINE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
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
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    table.setStyle(TableStyle(style))
    return table


def _line_chart(df, series: dict[str, tuple[str, colors.Color]], y_title: str, currency: bool = False):
    width, height = 520, 230
    left, right, bottom, top = 52, 24, 34, 28
    plot_w = width - left - right
    plot_h = height - bottom - top
    drawing = Drawing(width, height)

    if df.empty:
        drawing.add(String(left, height / 2, "No chart data available", fillColor=MUTED, fontSize=10))
        return drawing

    chart_series = []
    for label, (column, color) in series.items():
        if column in df:
            values = [float(v) for v in df[column].fillna(0).tolist()]
            chart_series.append((label, values, color))
    if not chart_series:
        drawing.add(String(left, height / 2, "No chart data available", fillColor=MUTED, fontSize=10))
        return drawing

    all_values = [value for _, values, _ in chart_series for value in values]
    y_min = min(0, min(all_values))
    y_max = max(all_values)
    if y_max == y_min:
        y_max = y_min + 1
    pad = (y_max - y_min) * 0.12
    y_min -= pad
    y_max += pad

    drawing.add(Line(left, bottom, left, bottom + plot_h, strokeColor=LINE))
    drawing.add(Line(left, bottom, left + plot_w, bottom, strokeColor=LINE))
    drawing.add(String(4, bottom + plot_h + 2, y_title, fillColor=MUTED, fontSize=8))

    for idx in range(4):
        y = bottom + (plot_h * idx / 3)
        value = y_min + ((y_max - y_min) * idx / 3)
        drawing.add(Line(left, y, left + plot_w, y, strokeColor=colors.HexColor("#EDF2F7")))
        drawing.add(String(4, y - 3, _axis_label(value, currency), fillColor=MUTED, fontSize=7))

    count = max(len(chart_series[0][1]), 1)
    x_step = plot_w / max(count - 1, 1)
    for label, values, color in chart_series:
        points = []
        for idx, value in enumerate(values):
            x = left + idx * x_step
            y = bottom + ((value - y_min) / (y_max - y_min)) * plot_h
            points.append((x, y))
        for start, end in zip(points, points[1:]):
            drawing.add(Line(start[0], start[1], end[0], end[1], strokeColor=color, strokeWidth=1.6))
        for x, y in points:
            drawing.add(Rect(x - 1.4, y - 1.4, 2.8, 2.8, fillColor=color, strokeColor=color))

    dates = df["date"].dt.strftime("%d").tolist() if "date" in df else [str(i + 1) for i in range(count)]
    for idx in _label_indexes(count):
        x = left + idx * x_step
        drawing.add(String(x - 4, bottom - 14, dates[idx], fillColor=MUTED, fontSize=7))

    legend_x = left + 4
    legend_y = height - 14
    for label, _, color in chart_series:
        drawing.add(Rect(legend_x, legend_y - 7, 7, 7, fillColor=color, strokeColor=color))
        drawing.add(String(legend_x + 11, legend_y - 7, label, fillColor=INK, fontSize=8))
        legend_x += min(180, 45 + len(label) * 4.5)
    return KeepTogether([drawing])


def _variance_bar_chart(metrics: dict):
    rows = [
        ("Transient", metrics["transient_revenue_gap"], PURPLE),
        ("Group", metrics["group_revenue_gap"], TEAL),
        ("Total", metrics["revenue_gap"], RED if metrics["revenue_gap"] < 0 else GREEN),
    ]
    width, height = 520, 210
    left, bottom, plot_w, plot_h = 72, 38, 410, 128
    drawing = Drawing(width, height)
    values = [float(value) if not _missing(value) else 0 for _, value, _ in rows]
    max_abs = max(abs(value) for value in values) or 1
    zero_y = bottom + plot_h / 2
    drawing.add(Line(left, zero_y, left + plot_w, zero_y, strokeColor=INK, strokeWidth=0.7))
    drawing.add(Line(left, bottom, left, bottom + plot_h, strokeColor=LINE))
    bar_w = 72
    gap = (plot_w - len(rows) * bar_w) / max(len(rows) - 1, 1)
    for idx, (label, value, color) in enumerate(rows):
        value = float(value) if not _missing(value) else 0
        x = left + idx * (bar_w + gap)
        bar_h = abs(value) / max_abs * (plot_h / 2 - 8)
        y = zero_y if value >= 0 else zero_y - bar_h
        fill = color if value >= 0 else RED
        drawing.add(Rect(x, y, bar_w, bar_h, fillColor=fill, strokeColor=fill))
        drawing.add(String(x + 4, bottom - 18, label, fillColor=INK, fontSize=8))
        drawing.add(String(x - 2, y + bar_h + 5 if value >= 0 else y - 12, fmt_money(value), fillColor=INK, fontSize=8))
    drawing.add(String(4, zero_y - 3, "$0", fillColor=MUTED, fontSize=8))
    drawing.add(String(4, bottom + plot_h - 3, _axis_label(max_abs, True), fillColor=MUTED, fontSize=8))
    drawing.add(String(4, bottom - 3, _axis_label(-max_abs, True), fillColor=MUTED, fontSize=8))
    return drawing


def _label_indexes(count: int) -> list[int]:
    if count <= 8:
        return list(range(count))
    step = max(1, math.ceil(count / 8))
    indexes = list(range(0, count, step))
    if count - 1 not in indexes:
        indexes.append(count - 1)
    return indexes


def _axis_label(value: float, currency: bool) -> str:
    if currency:
        sign = "-" if value < 0 else ""
        value = abs(value)
        if value >= 1_000_000:
            return f"{sign}${value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{sign}${value / 1_000:.0f}K"
        return f"{sign}${value:.0f}"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f}K"
    return f"{value:.0f}"


def _missing(value) -> bool:
    if value is None:
        return True
    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False
