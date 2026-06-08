from __future__ import annotations

import numpy as np
import pandas as pd

from utils.data_loader import HOTEL_INVENTORY


def project_month_end(pace: pd.DataFrame, pickup: pd.DataFrame, method: str) -> dict:
    if pace.empty:
        return {}
    days_in_month = int(pace["date"].dt.days_in_month.max())
    observed_days = max(int(pace["date"].dt.day.max()), 1)
    remaining_days = max(days_in_month - observed_days, 0)

    if method == "Pickup Based Projection" and not pickup.empty:
        trailing = pickup.tail(min(7, len(pickup)))
        projected_rooms = pace["rooms"].sum() + trailing["rooms_pickup"].mean() * remaining_days
        projected_revenue = pace["revenue"].sum() + trailing["revenue_pickup"].mean() * remaining_days
        confidence = "Medium" if len(trailing) >= 5 else "Low"
    else:
        projected_rooms = _linear_projection(pace, "rooms", observed_days, days_in_month)
        projected_revenue = _linear_projection(pace, "revenue", observed_days, days_in_month)
        confidence = "High" if observed_days >= 10 else "Medium"

    projected_adr = projected_revenue / projected_rooms if projected_rooms else np.nan
    projected_occupancy = projected_rooms / (HOTEL_INVENTORY * days_in_month) if days_in_month else np.nan
    projected_revpar = projected_revenue / (HOTEL_INVENTORY * days_in_month) if days_in_month else np.nan
    return {
        "Projected Rooms": projected_rooms,
        "Projected Revenue": projected_revenue,
        "Projected ADR": projected_adr,
        "Projected Occupancy": projected_occupancy,
        "Projected RevPAR": projected_revpar,
        "Confidence": confidence,
    }


def _linear_projection(df: pd.DataFrame, column: str, observed_days: int, days_in_month: int) -> float:
    if len(df) < 2:
        return df[column].sum()
    x = df["date"].dt.day.to_numpy()
    y = df[column].to_numpy()
    slope, intercept = np.polyfit(x, y, 1)
    future_x = np.arange(observed_days + 1, days_in_month + 1)
    future_values = np.maximum(slope * future_x + intercept, 0)
    return float(df[column].sum() + future_values.sum())
