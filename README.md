# RoomSense Flask demo

This is your original dark RoomSense website connected to a **real Flask API and SQLite database**. Simulated sensor readings are saved every three seconds and the website polls the API every three seconds. The dashboard now has **live Chart.js charts** (Overview and Analytics tabs). Chart.js loads from the cdnjs CDN, so the browser needs internet access. Power BI is optional: see `POWERBI_SETUP.md`.

## Start (Windows PowerShell)

```powershell
cd roomsense-flask-demo
python -m venv .venv
.venv\Scripts\Activate.ps1   # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in a browser. Leave the terminal running.

macOS/Linux: use `python3 -m venv .venv`, `source .venv/bin/activate`, and `python app.py`.

## Project files

- `app.py` Flask app, API and simulator; `templates/index.html` dashboard
- `export_powerbi.py`, `auto_export.py` CSV export for Power BI; `powerbi_push.py` live streaming push
- `reset_data.py` back up and clear stored readings (stop everything first)
- `POWERBI_SETUP.md` Power BI routes

## API

- `GET /api/sensors/latest` — latest reading
- `GET /api/sensors/history?limit=60` — last 60 readings (up to 500)
- `GET /api/sensors/export.csv` — every reading as CSV (Power BI Web connector)
- `POST /api/sensors` — submit a real reading with `X-API-Key` header

To test a POST from PowerShell:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/sensors -Method Post -Headers @{ 'X-API-Key'='demo-key-change-me' } -ContentType 'application/json' -Body '{"temperature":23.1,"humidity":51,"occupancy":2,"lights":true}'
```

## Switch from simulation to ESP32

Stop the app, then set environment variables before starting it:

PowerShell:
```powershell
$env:ROOMSENSE_SIMULATE='0'
$env:ROOMSENSE_API_KEY='choose-a-long-secret-key'
python app.py
```

Send POST requests from your ESP32 to `http://YOUR_COMPUTER_LAN_IP:5000/api/sensors`, with JSON body and `X-API-Key` header. **Note:** For ESP32 access on your local network, change `host='127.0.0.1'` to `host='0.0.0.0'` in `app.py` and permit the port through your computer firewall. Only use on a trusted local network; this demo uses plain HTTP and is not production-ready. Don't expose it directly to the internet.

The occupancy number in simulation is illustrative. A basic PIR sensor detects motion, **not the exact number of people** in a room; use an appropriate counting sensor/algorithm for real occupancy numbers.

## Power BI later

Three routes (web connector, CSV auto-export, live streaming push) are explained in `POWERBI_SETUP.md`. Your historical data is stored in `readings.db` (SQLite). For a larger deployment, migrate to PostgreSQL, which Power BI can query using supported connection modes. Power BI refresh intervals depend on its mode and licensing.
