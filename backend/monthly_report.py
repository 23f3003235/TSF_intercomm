"""Send the previous calendar month's admin change report (IST).
Usage: python monthly_report.py [--month YYYY-MM]
Schedule on the 1st of each month after 00:00 IST using cron/launchd.
"""
import argparse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app import app, send_monthly_report

parser=argparse.ArgumentParser()
parser.add_argument('--month',help='YYYY-MM; defaults to previous month in IST')
args=parser.parse_args()
previous=(datetime.now(ZoneInfo('Asia/Kolkata')).replace(day=1)-timedelta(days=1)).strftime('%Y-%m')
with app.app_context():
    print(f'Monthly report {args.month or previous}: {send_monthly_report(args.month or previous)}')
