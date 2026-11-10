# Power BI + RoomSense: three routes

The **website itself now has live charts** (Overview and Analytics tabs, every 3 s, no Power BI needed).
Power BI is for long-term reporting. Pick the route that fits:

| Route | How live? | Needs |
|---|---|---|
| A. Web connector (recommended for Desktop) | Click Refresh, or auto-refresh on a timer | Flask running |
| B. CSV file + auto_export.py | Click Refresh after each export | Flask + 2 scripts |
| C. Streaming push (`powerbi_push.py`) | Truly live dashboard tiles (a few seconds) | Power BI Service account |

> **Power BI Desktop never live-updates an imported dataset by itself.** Routes A and B reload
> only when you press Refresh (A can be put on a timer, see below). Only route C is genuinely live.

## Route A: Web connector (no export script)

1. Run `python app.py`.
2. Power BI Desktop → **Get data → Web** → `http://127.0.0.1:5000/api/sensors/export.csv` → OK → **Transform Data**.
3. Set `timestamp_utc` to **Date/Time**, `temperature`/`humidity` to **Decimal Number**, `occupancy`/`lights` to **Whole Number**. **Close & Apply**.
4. Build line charts with `timestamp_utc` (not Date Hierarchy) on the X-axis. Set aggregation to **Average**.
5. Refresh: **Home → Refresh**. For automatic refresh, publish the report to the Power BI Service and set a scheduled refresh (this needs an on-premises data gateway, because the URL is localhost).

## Route B: CSV file with auto-export

1. Terminal 1: `python app.py`
2. Terminal 2: `python auto_export.py` (rewrites `powerbi_data.csv` every 30 s; edit `INTERVAL` to change).
3. Power BI Desktop → **Get data → Text/CSV** → `powerbi_data.csv`, then types as in route A.
4. Press **Refresh** in Power BI to load the latest export.

If Power BI says the file is in use, the next export is skipped and retried 30 s later. That is normal.

## Route C: Streaming dataset (truly live tiles)

One-time setup in the Power BI Service (app.powerbi.com):

1. **New → Streaming dataset → API → Next.**
2. Dataset name `RoomSense`. Add these fields:
   `timestamp` (DateTime), `temperature` (Number), `humidity` (Number), `occupancy` (Number), `lights` (Number), `source` (Text).
3. Turn **Historic data analysis** ON (lets you build reports on it too). Click **Create**.
4. Copy the **Push URL**. It contains a secret key; treat it like a password.

Run it (third terminal, with `python app.py` running):

```powershell
$env:POWERBI_PUSH_URL='PASTE-PUSH-URL-HERE'
python powerbi_push.py
```

5. In the Service: **New dashboard → Add a tile → Custom streaming data → RoomSense**. Add a **Line chart**
   (axis `timestamp`, values `temperature` and `humidity`, time window e.g. 5 minutes). Tiles update within seconds.
6. First run starts from the newest reading and pushes only new ones; progress is kept in `.powerbi_push_state`.

Note: this sends your readings to Microsoft's cloud, which is what makes it live. Skip route C if you want data to stay local.

## Notes
- All timestamps are **UTC**. Convert to local time in Power Query if you want.
- The simulated `occupancy` is illustrative; a PIR sensor detects motion, not people counts.
