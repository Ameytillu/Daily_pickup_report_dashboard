from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from utils.data_loader import HOTEL_INVENTORY, WorkbookData


@dataclass
class DashboardContext:
    previous_sheet: str
    current_sheet: str
    previous_pace: pd.DataFrame
    current_pace: pd.DataFrame
    workbook_pickup: pd.DataFrame
    calculated_pickup: pd.DataFrame
    pickup: pd.DataFrame
    summary: dict
    metrics: dict
    forecast_table: pd.DataFrame


def build_dashboard_context(workbook: WorkbookData, previous_sheet: str, current_sheet: str) -> DashboardContext:
    previous = workbook.reports[previous_sheet]
    current = workbook.reports[current_sheet]
    calculated_pickup = compare_reports(previous.pace, current.pace)
    pickup = current.pickup.copy()
    if pickup.empty or pickup.select_dtypes("number").abs().sum().sum() == 0:
        pickup = calculated_pickup

    metrics = calculate_month_metrics(current.pace, pickup, current.summary)
    forecast_table = build_forecast_table(metrics, current.summary)
    return DashboardContext(
        previous_sheet=previous_sheet,
        current_sheet=current_sheet,
        previous_pace=previous.pace,
        current_pace=current.pace,
        workbook_pickup=current.pickup,
        calculated_pickup=calculated_pickup,
        pickup=pickup,
        summary=current.summary,
        metrics=metrics,
        forecast_table=forecast_table,
    )


def compare_reports(previous: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    merged = current.merge(previous, on="date", how="left", suffixes=("", "_previous"))
    pickup = pd.DataFrame({"date": merged["date"], "day": merged.get("day", "")})
    mappings = {
        "rooms": "rooms_pickup",
        "occupancy_pct": "occupancy_pickup",
        "revenue": "revenue_pickup",
        "transient_rooms": "transient_rooms_pickup",
        "transient_revenue": "transient_revenue_pickup",
        "group_rooms": "group_rooms_pickup",
        "group_revenue": "group_revenue_pickup",
    }
    for source, target in mappings.items():
        pickup[target] = merged[source].fillna(0) - merged[f"{source}_previous"].fillna(0)

    pickup["adr_pickup"] = _safe_divide(pickup["revenue_pickup"], pickup["rooms_pickup"])
    pickup["transient_adr_pickup"] = _safe_divide(pickup["transient_revenue_pickup"], pickup["transient_rooms_pickup"])
    pickup["group_adr_pickup"] = _safe_divide(pickup["group_revenue_pickup"], pickup["group_rooms_pickup"])
    return pickup


def calculate_month_metrics(pace: pd.DataFrame, pickup: pd.DataFrame, summary: dict) -> dict:
    days = max(int(pace["date"].nunique()), 1)
    otb_rooms = pace["rooms"].sum()
    otb_revenue = pace["revenue"].sum()
    transient_rooms = pace["transient_rooms"].sum()
    transient_revenue = pace["transient_revenue"].sum()
    group_rooms = pace["group_rooms"].sum()
    group_revenue = pace["group_revenue"].sum()
    other_revenue = max(0, otb_revenue - transient_revenue - group_revenue)

    forecast_revenue = summary.get("forecast_revenue", np.nan)
    forecast_rooms = summary.get("forecast_rooms", np.nan)
    if pd.isna(forecast_rooms):
        forecast_rooms = np.nan

    metrics = {
        "otb_rooms": otb_rooms,
        "otb_revenue": otb_revenue,
        "adr": _scalar_divide(otb_revenue, otb_rooms),
        "occupancy_pct": _scalar_divide(otb_rooms, HOTEL_INVENTORY * days),
        "revpar": _scalar_divide(otb_revenue, HOTEL_INVENTORY * days),
        "rooms_pickup": pickup["rooms_pickup"].sum() if not pickup.empty else 0,
        "revenue_pickup": pickup["revenue_pickup"].sum() if not pickup.empty else 0,
        "adr_pickup": _scalar_divide(pickup["revenue_pickup"].sum(), pickup["rooms_pickup"].sum()) if not pickup.empty else 0,
        "transient_rooms": transient_rooms,
        "transient_revenue": transient_revenue,
        "transient_adr": _scalar_divide(transient_revenue, transient_rooms),
        "transient_rooms_pickup": pickup["transient_rooms_pickup"].sum() if not pickup.empty else 0,
        "transient_revenue_pickup": pickup["transient_revenue_pickup"].sum() if not pickup.empty else 0,
        "group_rooms": group_rooms,
        "group_revenue": group_revenue,
        "group_adr": _scalar_divide(group_revenue, group_rooms),
        "group_rooms_pickup": pickup["group_rooms_pickup"].sum() if not pickup.empty else 0,
        "group_revenue_pickup": pickup["group_revenue_pickup"].sum() if not pickup.empty else 0,
        "other_revenue": other_revenue,
        "forecast_revenue": forecast_revenue,
        "forecast_rooms": forecast_rooms,
        "forecast_transient_revenue": summary.get("forecast_transient_revenue", np.nan),
        "forecast_group_revenue": summary.get("forecast_group_revenue", np.nan),
    }

    metrics["revenue_gap"] = _gap(otb_revenue, forecast_revenue)
    metrics["rooms_gap"] = _gap(otb_rooms, forecast_rooms)
    metrics["transient_revenue_gap"] = _gap(transient_revenue, metrics["forecast_transient_revenue"])
    metrics["group_revenue_gap"] = _gap(group_revenue, metrics["forecast_group_revenue"])
    metrics["forecast_achievement_pct"] = _scalar_divide(otb_revenue, forecast_revenue) * 100
    metrics["rooms_achievement_pct"] = _scalar_divide(otb_rooms, forecast_rooms) * 100
    metrics["revenue_needed"] = _gap(forecast_revenue, otb_revenue)
    metrics["rooms_needed"] = _gap(forecast_rooms, otb_rooms)
    metrics["transient_revenue_needed"] = _gap(metrics["forecast_transient_revenue"], transient_revenue)
    metrics["group_revenue_needed"] = _gap(metrics["forecast_group_revenue"], group_revenue)
    return metrics


def build_forecast_table(metrics: dict, summary: dict) -> pd.DataFrame:
    rows = [
        ("Rooms", metrics["forecast_rooms"], metrics["otb_rooms"]),
        ("Revenue", metrics["forecast_revenue"], metrics["otb_revenue"]),
        ("ADR", _safe_forecast_adr(metrics), metrics["adr"]),
        ("Transient Revenue", metrics["forecast_transient_revenue"], metrics["transient_revenue"]),
        ("Group Revenue", metrics["forecast_group_revenue"], metrics["group_revenue"]),
    ]
    table = pd.DataFrame(rows, columns=["Metric", "Forecast", "Current OTB"])
    table["Gap"] = table["Current OTB"] - table["Forecast"]
    table["Achievement %"] = _safe_divide(table["Current OTB"], table["Forecast"]) * 100
    table["Needed"] = table["Forecast"] - table["Current OTB"]
    table.loc[table["Forecast"].isna(), ["Gap", "Achievement %", "Needed"]] = np.nan
    return table


def _safe_forecast_adr(metrics: dict) -> float:
    return _scalar_divide(metrics.get("forecast_revenue"), metrics.get("forecast_rooms"))


def _gap(left, right):
    if pd.isna(left) or pd.isna(right):
        return np.nan
    return left - right


def _safe_divide(numerator, denominator):
    result = numerator / denominator.replace(0, np.nan) if hasattr(denominator, "replace") else numerator / denominator
    return result.replace([np.inf, -np.inf], np.nan).fillna(0) if hasattr(result, "fillna") else result


def _scalar_divide(numerator, denominator) -> float:
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return np.nan
    return numerator / denominator
