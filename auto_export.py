"""Re-run export_powerbi.py on a timer so powerbi_data.csv stays up to date.

Run in a second terminal: python auto_export.py   (Ctrl+C to stop)
Power BI Desktop still needs you to press Refresh to load the new CSV.
"""
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
EXPORT_SCRIPT = BASE_DIR / 'export_powerbi.py'
INTERVAL = 30  # seconds between exports


def export_data():
    try:
        subprocess.run([sys.executable, str(EXPORT_SCRIPT)], cwd=BASE_DIR, check=True)
    except subprocess.CalledProcessError as error:
        print('Export failed (will retry):', error)


def main():
    print(f'Automatic export started: every {INTERVAL}s. Ctrl+C to stop.')
    try:
        while True:
            export_data()
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print('\nStopped.')


if __name__ == '__main__':
    main()
