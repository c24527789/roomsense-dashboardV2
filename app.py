"""RoomSense Flask demo: SQLite history, simulated data, and ESP32-ready API."""
import csv
import io
import os
import random
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, Response, jsonify, render_template, request

BASE = Path(__file__).resolve().parent
DB = BASE / 'readings.db'
app = Flask(__name__)
API_KEY = os.environ.get('ROOMSENSE_API_KEY', 'demo-key-change-me')
SIMULATE = os.environ.get('ROOMSENSE_SIMULATE', '1') == '1'


def connect():
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def initialize():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            occupancy INTEGER NOT NULL,
            lights INTEGER NOT NULL,
            source TEXT NOT NULL
        )''')


def save_reading(payload, source):
    if not isinstance(payload, dict):
        raise ValueError('Expected JSON object')
    try:
        temperature = float(payload['temperature'])
        humidity = float(payload['humidity'])
        occupancy = int(payload['occupancy'])
        lights = payload['lights']
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError('Required: temperature, humidity, occupancy, lights') from exc
    if not (-40 <= temperature <= 85 and 0 <= humidity <= 100 and 0 <= occupancy <= 100):
        raise ValueError('Reading outside permitted range')
    if not isinstance(lights, bool):
        raise ValueError('lights must be true or false')
    timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    with connect() as db:
        cursor = db.execute('INSERT INTO readings (timestamp, temperature, humidity, occupancy, lights, source) VALUES (?, ?, ?, ?, ?, ?)',
                          (timestamp, temperature, humidity, occupancy, int(lights), source))
        row_id = cursor.lastrowid
    return {'id': row_id, 'timestamp': timestamp, 'temperature': temperature,
            'humidity': humidity, 'occupancy': occupancy, 'lights': lights, 'source': source}


def utc_text(timestamp):
    """ISO timestamp from the database -> 'YYYY-MM-DD HH:MM:SS' in UTC."""
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def row_to_dict(row):
    result = dict(row)
    result['lights'] = bool(result['lights'])
    return result


@app.get('/')
def home():
    return render_template('index.html')


@app.get('/api/sensors/latest')
def latest():
    with connect() as db:
        row = db.execute('SELECT * FROM readings ORDER BY id DESC LIMIT 1').fetchone()
    if row is None:
        return jsonify({'error': 'No readings yet'}), 404
    return jsonify(row_to_dict(row))


@app.get('/api/sensors/history')
def history():
    try:
        limit = min(max(int(request.args.get('limit', 60)), 1), 500)
    except ValueError:
        return jsonify({'error': 'limit must be an integer'}), 400
    with connect() as db:
        rows = db.execute('SELECT * FROM (SELECT * FROM readings ORDER BY id DESC LIMIT ?) ORDER BY id ASC',
                          (limit,)).fetchall()
    return jsonify([row_to_dict(row) for row in rows])


@app.get('/api/sensors/export.csv')
def export_csv():
    """All readings as CSV, same columns as export_powerbi.py. Power BI: Get data > Web > this URL."""
    with connect() as db:
        rows = db.execute('SELECT id, timestamp, temperature, humidity, occupancy, lights, source FROM readings ORDER BY id ASC').fetchall()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['id', 'timestamp_utc', 'temperature', 'humidity', 'occupancy', 'lights', 'source'])
    for r in rows:
        writer.writerow([r['id'], utc_text(r['timestamp']), r['temperature'], r['humidity'],
                         r['occupancy'], r['lights'], r['source']])
    return Response(out.getvalue(), mimetype='text/csv', headers={'Cache-Control': 'no-store'})


@app.post('/api/sensors')
def ingest():
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Invalid API key'}), 401
    try:
        reading = save_reading(request.get_json(silent=True), 'device')
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    return jsonify(reading), 201


def simulator():
    temperature, humidity = 22.4, 48.0
    while True:
        temperature = max(19, min(27, temperature + random.uniform(-0.25, 0.25)))
        humidity = max(35, min(65, humidity + random.uniform(-1.5, 1.5)))
        save_reading({'temperature': round(temperature, 1), 'humidity': round(humidity, 1),
                      'occupancy': random.randint(0, 4), 'lights': random.random() > 0.2}, 'simulation')
        time.sleep(3)


initialize()
if __name__ == '__main__':
    if SIMULATE:
        threading.Thread(target=simulator, name='simulator', daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
