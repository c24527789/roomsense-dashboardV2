"""Push new RoomSense readings to a Power BI streaming dataset (near real-time tiles).

Setup: see POWERBI_SETUP.md, route C. Then run (second terminal, alongside app.py):

    PowerShell:  $env:POWERBI_PUSH_URL='<push URL from Power BI>'; python powerbi_push.py

Only readings newer than the last one pushed are sent; progress is stored in
.powerbi_push_state so a restart does not re-send old rows. Treat the push URL
like a password (it contains a key).
"""
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / 'readings.db'
STATE = ROOT / '.powerbi_push_state'
URL = os.environ.get('POWERBI_PUSH_URL', '').strip()
INTERVAL = float(os.environ.get('POWERBI_PUSH_INTERVAL', '5'))
BATCH = 500


def last_pushed():
    try:
        return int(STATE.read_text().strip())
    except (OSError, ValueError):
        return None


def new_rows(after_id):
    with sqlite3.connect(DATABASE, timeout=15) as conn:
        if after_id is None:  # first run: start from the latest reading, not the whole history
            row = conn.execute('SELECT COALESCE(MAX(id), 0) FROM readings').fetchone()
            return None, row[0]
        rows = conn.execute('SELECT id, timestamp, temperature, humidity, occupancy, lights, source '
                            'FROM readings WHERE id > ? ORDER BY id ASC LIMIT ?', (after_id, BATCH)).fetchall()
    return rows, after_id


def to_payload(row):
    rid, ts, temperature, humidity, occupancy, lights, source = row
    return {'timestamp': ts.replace('+00:00', 'Z'), 'temperature': temperature, 'humidity': humidity,
            'occupancy': occupancy, 'lights': int(lights), 'source': source}


def post(rows):
    body = json.dumps([to_payload(r) for r in rows]).encode()
    req = urllib.request.Request(URL, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status


def main():
    if not URL:
        sys.exit('Set POWERBI_PUSH_URL first (see POWERBI_SETUP.md, route C).')
    if not DATABASE.exists():
        sys.exit('No readings.db found. Start Flask (python app.py) first.')
    print(f'Pushing new readings to Power BI every {INTERVAL:g}s. Ctrl+C to stop.')
    while True:
        try:
            after = last_pushed()
            rows, after = new_rows(after)
            if rows is None:
                STATE.write_text(str(after))
                print(f'First run: starting from reading id {after}.')
            elif rows:
                status = post(rows)
                STATE.write_text(str(rows[-1][0]))
                print(f'Pushed {len(rows)} reading(s) up to id {rows[-1][0]} (HTTP {status}).')
        except urllib.error.HTTPError as err:
            print(f'Power BI rejected the push: HTTP {err.code}. Check the URL and the dataset fields.')
        except (urllib.error.URLError, sqlite3.Error, OSError) as err:
            print('Will retry:', err)
        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
