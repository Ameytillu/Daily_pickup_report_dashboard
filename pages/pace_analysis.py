import pandas as pd
import streamlit as st

from utils.charts import line_chart
from utils.helpers import format_by_metric, page_title


METRICS = {
    "Rooms Pace": "rooms",
    "Revenue Pace": "revenue",
    "ADR Pace": "adr",
    "Occupancy Pace": "occupancy_pct",
    "RevPAR Pace": "revpar",
}


def render(context):
    page_title("Pace Analysis", "Side-by-side previous and current report comparison.")
    metric_label = st.selectbox("Pace Metric", list(METRICS.keys()))
    metric = METRICS[metric_label]

    previous = context.previous_pace[["date", metric]].rename(columns={metric: "Previous Report"})
    current = context.current_pace[["date", metric]].rename(columns={metric: "Current Report"})
    compare = current.merge(previous, on="date", how="left")
    compare["Difference"] = compare["Current Report"] - compare["Previous Report"].fillna(0)
    compare["Variance %"] = (compare["Difference"] / compare["Previous Report"].replace(0, pd.NA)) * 100

    previous_value = _aggregate_compare(compare, "Previous Report", metric)
    current_value = _aggregate_compare(compare, "Current Report", metric)
    pickup_value = current_value - previous_value

    c1, c2, c3 = st.columns(3)
    c1.metric("Previous Report", format_by_metric(metric, previous_value))
    c2.metric("Current Report", format_by_metric(metric, current_value))
    c3.metric("Pickup Generated", format_by_metric(metric, pickup_value))

    st.plotly_chart(line_chart(compare, ["Previous Report", "Current Report"], metric_label), use_container_width=True)
    st.dataframe(compare, use_container_width=True)


def _aggregate_compare(compare: pd.DataFrame, column: str, metric: str) -> float:
    if metric in {"adr", "occupancy_pct", "revpar"}:
        return compare[column].mean()
    return compare[column].sum()

