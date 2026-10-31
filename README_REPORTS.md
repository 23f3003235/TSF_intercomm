# TSF Directory — Reports and monthly email

## Files
Replace `backend/app.py`, `frontend/src/App.vue`, `frontend/src/style.css` and add `backend/monthly_report.py`. Back up your files and `backend/directory.db` first. Keep your existing `.env` and database.

## Dashboard
Sign in as a department admin or super-admin, then open **Reports**. Department admins see only their own department; super-admins see all department-admin changes. Counts include **created**, **updated** and **deleted** contact records; super-admin edits are excluded. Switch between daily, ISO-weekly, monthly, department and administrator breakdowns. Choose a month to filter or leave blank for all history. Download a detailed CSV from Reports.

Dates and month boundaries use **Asia/Kolkata (IST)**. Prior audit rows are backfilled from the *current* user role; if an account's role was changed or deleted, historic records may not be attributed correctly. New audit rows store the role at the time of the change.

## Automatic monthly report — Mac
The Flask development server does not run scheduled jobs. Configure a persistent system scheduler on the computer/server running the backend. Example with macOS `crontab -e` (replace the absolute path with your project path):

```
CRON_TZ=Asia/Kolkata
0 9 1 * * cd /Users/YOURNAME/Documents/projects/TSF_telephone_directory/backend && /Users/YOURNAME/Documents/projects/TSF_telephone_directory/backend/.venv/bin/python monthly_report.py >> /Users/YOURNAME/Documents/projects/TSF_telephone_directory/backend/monthly_report.log 2>&1
```

**Important:** `CRON_TZ` is not supported by every macOS cron implementation; set the Mac's system time zone to Asia/Kolkata or use launchd with local-time scheduling. The task must run on a powered-on, awake computer. For guaranteed delivery use an always-on server with cron/systemd timer. Running `python monthly_report.py` sends the *previous* month, and `python monthly_report.py --month 2026-10` sends a specific completed month. Never run the manual command just to preview: it actually emails recipients.

The script checks for a successfully sent month in the `monthly_report_delivery` database table, preventing ordinary duplicate runs. A process failure between Gmail accepting the email and recording success can still result in a duplicate if retried. SMTP configuration is taken from your existing `.env` (`SMTP_USER`, `SMTP_APP_PASSWORD`). Monthly email includes totals, department/admin/day breakdowns and the full before/after change log. Sent status appears under **Reports** for super-admins.

## Restart
Backend: `python app.py`; frontend: `npm run dev -- --host 0.0.0.0`.

## Limitations
Email delivery is not guaranteed when the Mac is sleeping/offline or SMTP rejects the message. Reports reflect only stored audit records, not changes made outside the app. If reports are large, Gmail may reject the message for exceeding size limits; CSV export remains available.
