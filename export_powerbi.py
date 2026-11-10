"""Export the RoomSense SQLite history to a Power BI-friendly CSV.

Run from any directory: python export_powerbi.py
"""
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / 'readings.db'
OUTPUT = ROOT / 'powerbi_data.csv'


def main():
    if not DATABASE.exists():
        raise SystemExit('No readings.db found. Start Flask (python app.py) first to generate readings.')
    with sqlite3.connect(DATABASE, timeout=15) as conn:
        rows = conn.execute('''
            SELECT id, timestamp, temperature, humidity, occupancy, lights, source
            FROM readings ORDER BY id ASC
        ''').fetchall()

    # Write atomically so Power BI never opens a half-written export.
    temporary = OUTPUT.with_suffix('.csv.tmp')
    with temporary.open('w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'timestamp_utc', 'temperature', 'humidity', 'occupancy', 'lights', 'source'])
        for row_id, timestamp, temperature, humidity, occupancy, lights, source in rows:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(timezone.utc)
            writer.writerow([row_id, dt.strftime('%Y-%m-%d %H:%M:%S'), temperature,
                             humidity, occupancy, int(lights), source])
    temporary.replace(OUTPUT)
    print(f'Exported {len(rows)} readings to {OUTPUT}')
    print('Timestamp is UTC; set timestamp_utc to Date/Time in Power BI.')


if __name__ == '__main__':
    main()
