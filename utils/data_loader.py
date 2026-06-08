from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import re
from typing import BinaryIO

import numpy as np
import pandas as pd
import streamlit as st


HOTEL_INVENTORY = 433

PACE_COLUMNS = [
    "date",
    "day",
    "rooms",
    "occupancy_pct",
    "revenue",
    "adr",
    "revpar",
    "transient_rooms",
    "transient_revenue",
    "transient_adr",
    "group_rooms",
    "group_revenue",
    "group_adr",
]

PICKUP_COLUMNS = [
    "date",
    "day",
    "rooms_pickup",
    "occupancy_pickup",
    "revenue_pickup",
    "adr_pickup",
    "transient_rooms_pickup",
    "transient_revenue_pickup",
    "transient_adr_pickup",
    "group_rooms_pickup",
    "group_revenue_pickup",
    "group_adr_pickup",
]

SUMMARY_ALIASES = {
    "budget_revenue": ["budget revenue", "budget total revenue", "total budget revenue"],
    "forecast_revenue": ["forecast revenue", "forecast total revenue", "total forecast revenue"],
    "budget_transient_revenue": ["budget transient revenue", "transient budget revenue"],
    "forecast_transient_revenue": ["forecast transient revenue", "transient forecast revenue"],
    "budget_group_revenue": ["budget group revenue", "group budget revenue"],
    "forecast_group_revenue": ["forecast group revenue", "group forecast revenue"],
    "forecast_rooms": ["forecast rooms", "rooms forecast", "forecast room nights"],
    "budget_rooms": ["budget rooms", "rooms budget", "budget room nights"],
    "vs_budget_revenue": ["vs b revenue", "vs budget revenue"],
    "vs_forecast_revenue": ["vs f revenue", "vs forecast revenue"],
    "vs_budget_transient_revenue": ["vs b transient", "vs budget transient"],
    "vs_forecast_transient_revenue": ["vs f transient", "vs forecast transient"],
    "vs_budget_group_revenue": ["vs b group", "vs budget group"],
    "vs_forecast_group_revenue": ["vs f group", "vs forecast group"],
}


@dataclass
class ReportSheet:
    name: str
    pace: pd.DataFrame
    pickup: pd.DataFrame
    summary: dict


@dataclass
class WorkbookData:
    sheet_names: list[str]
    reports: dict[str, ReportSheet]


def _file_bytes(uploaded_file: BinaryIO) -> bytes:
    uploaded_file.seek(0)
    return uploaded_file.read()


@st.cache_data(show_spinner=False)
def _load_workbook_from_bytes(file_bytes: bytes) -> WorkbookData:
    try:
        xls = pd.ExcelFile(BytesIO(file_bytes), engine="openpyxl")
    except Exception as exc:
        raise ValueError("The uploaded file could not be opened as an Excel workbook.") from exc

    reports: dict[str, ReportSheet] = {}
    for sheet_name in xls.sheet_names:
        raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        if raw.dropna(how="all").empty:
            continue
        report = parse_report_sheet(raw, sheet_name)
        if _is_report_day_sheet(sheet_name, report):
            reports[sheet_name] = report

    if not reports:
        raise ValueError("No usable report worksheets were found.")

    sheet_names = sorted(reports.keys(), key=_sheet_sort_key)
    return WorkbookData(sheet_names=sheet_names, reports=reports)


def load_workbook(uploaded_file: BinaryIO) -> WorkbookData:
    return _load_workbook_from_bytes(_file_bytes(uploaded_file))


def parse_report_sheet(raw: pd.DataFrame, sheet_name: str) -> ReportSheet:
    pace = _extract_table(raw, start_col=0, width=13, columns=PACE_COLUMNS)
    pickup = _extract_table(raw, start_col=14, width=12, columns=PICKUP_COLUMNS)
    pickup = _calculate_pickup_adr(pickup)
    summary = _extract_summary(raw)
    return ReportSheet(name=sheet_name, pace=pace, pickup=pickup, summary=summary)


def has_meaningful_report_data(report: ReportSheet) -> bool:
    if report.pace.empty:
        return False
    numeric_cols = ["rooms", "revenue", "transient_revenue", "group_revenue"]
    available_cols = [col for col in numeric_cols if col in report.pace.columns]
    if not available_cols:
        return False
    return report.pace[available_cols].fillna(0).abs().sum().sum() > 0


def _is_report_day_sheet(sheet_name: str, report: ReportSheet) -> bool:
    if report.pace.empty:
        return False
    return bool(re.fullmatch(r"\d{1,2}", str(sheet_name).strip()))


def _extract_table(raw: pd.DataFrame, start_col: int, width: int, columns: list[str]) -> pd.DataFrame:
    section = raw.iloc[:, start_col : start_col + width].copy()
    if section.empty:
        return pd.DataFrame(columns=columns)

    start_row = _find_first_data_row(section)
    section = section.iloc[start_row:].copy()
    section = section.dropna(how="all")
    if section.empty:
        return pd.DataFrame(columns=columns)

    section = section.iloc[:, : len(columns)]
    section.columns = columns
    section["date"] = pd.to_datetime(section["date"], errors="coerce")
    section = section.dropna(subset=["date"])
    section = section.sort_values("date").reset_index(drop=True)

    for col in columns:
        if col not in ["date", "day"]:
            section[col] = _to_number(section[col])
            if "occupancy" in col and section[col].abs().max() > 1:
                section[col] = section[col] / 100

    if "day" in section:
        section["day"] = section["day"].astype(str).replace({"nan": ""})
    return section


def _find_first_data_row(section: pd.DataFrame) -> int:
    for idx in range(section.shape[0]):
        first = _normalize_label(section.iat[idx, 0])
        second = _normalize_label(section.iat[idx, 1]) if section.shape[1] > 1 else ""
        third = _normalize_label(section.iat[idx, 2]) if section.shape[1] > 2 else ""
        if first == "date" and second == "day" and "rooms" in third:
            return idx + 1
    first_col = pd.to_datetime(section.iloc[:, 0], errors="coerce")
    valid = np.where(first_col.notna())[0]
    return int(valid[0]) if len(valid) else 0


def _extract_summary(raw: pd.DataFrame) -> dict:
    summary = {key: np.nan for key in SUMMARY_ALIASES}
    top = raw.iloc[:12, : min(raw.shape[1], 14)].copy()

    for r_idx in range(top.shape[0]):
        for c_idx in range(top.shape[1]):
            label = _normalize_label(top.iat[r_idx, c_idx])
            if not label:
                continue
            for key, aliases in SUMMARY_ALIASES.items():
                if any(alias in label for alias in aliases):
                    value = _first_numeric_to_right(top, r_idx, c_idx)
                    if pd.notna(value):
                        summary[key] = value

    # Backward-compatible fallbacks for reports that keep summary values in fixed top cells.
    fallbacks = {
        "budget_revenue": (2, 7),
        "forecast_revenue": (3, 7),
        "vs_budget_revenue": (4, 7),
        "vs_forecast_revenue": (5, 7),
        "budget_transient_revenue": (2, 9),
        "forecast_transient_revenue": (3, 9),
        "vs_budget_transient_revenue": (4, 9),
        "vs_forecast_transient_revenue": (5, 9),
        "budget_group_revenue": (2, 11),
        "forecast_group_revenue": (3, 11),
        "vs_budget_group_revenue": (4, 11),
        "vs_forecast_group_revenue": (5, 11),
    }
    for key, (r_idx, c_idx) in fallbacks.items():
        if pd.isna(summary.get(key)) and r_idx < raw.shape[0] and c_idx < raw.shape[1]:
            summary[key] = _coerce_number(raw.iat[r_idx, c_idx])

    return summary


def _first_numeric_to_right(df: pd.DataFrame, r_idx: int, c_idx: int) -> float:
    for offset in range(1, 5):
        target_col = c_idx + offset
        if target_col >= df.shape[1]:
            break
        value = _coerce_number(df.iat[r_idx, target_col])
        if pd.notna(value):
            return value
    return np.nan


def _calculate_pickup_adr(pickup: pd.DataFrame) -> pd.DataFrame:
    if pickup.empty:
        return pickup
    pickup["adr_pickup"] = np.where(
        pickup["rooms_pickup"].abs() > 0,
        pickup["revenue_pickup"] / pickup["rooms_pickup"],
        pickup["adr_pickup"],
    )
    pickup["transient_adr_pickup"] = np.where(
        pickup["transient_rooms_pickup"].abs() > 0,
        pickup["transient_revenue_pickup"] / pickup["transient_rooms_pickup"],
        pickup["transient_adr_pickup"],
    )
    pickup["group_adr_pickup"] = np.where(
        pickup["group_rooms_pickup"].abs() > 0,
        pickup["group_revenue_pickup"] / pickup["group_rooms_pickup"],
        pickup["group_adr_pickup"],
    )
    return pickup


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip(),
        errors="coerce",
    ).fillna(0)


def _coerce_number(value) -> float:
    if pd.isna(value):
        return np.nan
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").replace("%", "").strip()
    return pd.to_numeric(value, errors="coerce")


def _normalize_label(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _sheet_sort_key(name: str):
    text = str(name)
    numbers = re.findall(r"\d+", text)
    if numbers:
        return (0, int(numbers[-1]), text.lower())
    return (1, text.lower())
