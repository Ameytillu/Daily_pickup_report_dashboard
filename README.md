# Hotel Revenue Management Pickup & Forecast Dashboard

Production-style Streamlit dashboard for a 433-room full-service resort revenue meeting. The app reads every worksheet in an uploaded Daily Pickup workbook, lets users select previous and current report days, and calculates pickup, pace, segment, forecast, projection, alert, PDF, and Excel outputs.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Upload an `.xlsx` or `.xlsm` workbook where each worksheet is one report day. Worksheet names are detected dynamically and are never hardcoded.

## Expected Workbook Layout

- Daily Pace table in columns `A:M`
- Pickup table in columns `O:Z`
- Monthly summary values near the top of each worksheet
- Summary labels such as `Budget Revenue`, `Forecast Revenue`, `Budget Transient Revenue`, `Forecast Transient Revenue`, `Budget Group Revenue`, and `Forecast Group Revenue`

The loader also scans for optional `Forecast Rooms` and `Budget Rooms` labels. If room forecast values are not present, room forecast achievement fields remain blank instead of fabricating a value.

## Streamlit Cloud Deployment

1. Push this project to GitHub.
2. In Streamlit Community Cloud, choose **New app**.
3. Select the repository, branch, and `app.py`.
4. Confirm `requirements.txt` is in the repository root.
5. Deploy, then upload the Daily Pickup workbook from the sidebar.

## Pages

- Executive Dashboard
- Pickup Analysis
- Pace Analysis
- Transient Business Dashboard
- Group Business Dashboard
- Forecast Tracker
- Month-End Projection
- Pickup Calendar Heatmap
- Top Opportunities & Alerts
- Export Center

## Exports

The Export Center generates:

- Executive PDF report through ReportLab
- Excel summary workbook with KPI, forecast, pickup, current pace, and calculated pickup sheets

## Mockups

See `assets/dashboard_mockup.svg` for a sample executive dashboard mockup. The first screen is an executive upload view with a resort background image and three capability panels. After upload, each dashboard page uses a left control sidebar, KPI cards, Plotly charts, tables, tabs, and export buttons with a restrained revenue-management color palette:

- Revenue: green
- ADR: blue
- Occupancy: orange
- Transient: purple
- Group: teal
- Forecast gap: red
- Achievement: green
