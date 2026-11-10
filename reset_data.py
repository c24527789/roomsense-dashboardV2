"""Clear all stored readings (e.g. to drop simulated data before using the ESP32).

STOP app.py, auto_export.py and powerbi_push.py first, then run: python reset_data.py
A timestamped backup of readings.db is saved in the backups/ folder before anything is deleted.
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / 'readings.db'
BACKUPS = ROOT / 'backups'
GENERATED = [ROOT / 'powerbi_data.csv', ROOT / '.powerbi_push_state']  # ids restart at 1, so these are stale


def main():
    if not DATABASE.exists():
        sys.exit('No readings.db found, nothing to reset.')
    with sqlite3.connect(DATABASE, timeout=10) as conn:
        count = conn.execute('SELECT COUNT(*) FROM readings').fetchone()[0]
    if input(f'Delete {count} readings (a backup is kept)? Type yes to continue: ').strip().lower() != 'yes':
        sys.exit('Cancelled.')
    BACKUPS.mkdir(exist_ok=True)
    backup = BACKUPS / f'readings-{datetime.now():%Y%m%d-%H%M%S}.db'
    shutil.copy2(DATABASE, backup)
    conn = sqlite3.connect(DATABASE, timeout=10)
    try:
        conn.execute('DELETE FROM readings')
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'readings'")
        conn.commit()
        conn.execute('VACUUM')
    finally:
        conn.close()
    for path in GENERATED:
        path.unlink(missing_ok=True)
    print(f'Done. Backup: {backup}')
    print('Start python app.py again; readings restart at id 1. Refresh Power BI after the next export.')


if __name__ == '__main__':
    main()
