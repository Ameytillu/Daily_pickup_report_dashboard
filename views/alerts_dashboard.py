import streamlit as st

from utils.helpers import fmt_money, fmt_number, page_title


def render(context):
    page_title("Top Opportunities & Alerts", "Automatically generated pickup opportunities and forecast risks.")
    pace = context.current_pace.copy()
    pickup = context.pickup.copy()

    alerts = []
    if context.metrics["revenue_needed"] > 0:
        alerts.append(("Revenue Forecast Risk", f"Revenue is behind forecast by {fmt_money(context.metrics['revenue_needed'])}."))
    if context.metrics["group_revenue_pickup"] < 0:
        alerts.append(("Negative Group Pickup", f"Group revenue pickup is {fmt_money(context.metrics['group_revenue_pickup'])}."))
    if len(pickup) >= 3 and pickup["transient_revenue_pickup"].tail(3).mean() < 0:
        alerts.append(("Transient Pace Slowing", "The latest three-day transient pickup average is negative."))
    if len(pace) >= 3 and pace["adr"].tail(3).is_monotonic_decreasing:
        alerts.append(("ADR Declining", "ADR has declined across the latest three pace rows."))

    if alerts:
        cols = st.columns(2)
        for idx, (title, body) in enumerate(alerts):
            cols[idx % 2].warning(f"{title}: {body}")
    else:
        st.success("No critical revenue alerts were detected for the selected comparison.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Top 10 Pickup Days")
        st.dataframe(pickup.nlargest(10, "rooms_pickup")[["date", "rooms_pickup", "revenue_pickup", "adr_pickup"]], use_container_width=True)
        st.markdown("#### Top 10 Revenue Pickup Days")
        st.dataframe(pickup.nlargest(10, "revenue_pickup")[["date", "rooms_pickup", "revenue_pickup", "adr_pickup"]], use_container_width=True)
    with c2:
        st.markdown("#### Top 10 ADR Days")
        st.dataframe(pace.nlargest(10, "adr")[["date", "rooms", "revenue", "adr"]], use_container_width=True)
        st.markdown("#### Negative Pickup Days")
        st.dataframe(pickup[pickup["revenue_pickup"] < 0][["date", "rooms_pickup", "revenue_pickup", "adr_pickup"]], use_container_width=True)

    st.markdown("#### Revenue Risk Days")
    risk = pickup[(pickup["revenue_pickup"] < 0) | (pickup["rooms_pickup"] < 0)]
    st.dataframe(risk[["date", "rooms_pickup", "revenue_pickup", "group_revenue_pickup", "transient_revenue_pickup"]], use_container_width=True)


