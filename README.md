# Corporate Telephone Directory (local prototype)

## Requirements
- Python 3.10+
- Node.js 20+

## Start Flask API
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env      # Windows: copy .env.example .env
```
Edit `.env` with a unique `SECRET_KEY`, your real `INITIAL_ADMIN_EMAIL`, and a strong `INITIAL_ADMIN_PASSWORD` (at least 10 characters). Set `SMTP_USER` and `SMTP_APP_PASSWORD` to enable Gmail notification emails. Then:
```bash
python app.py
```

## Start Vue frontend (second terminal)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 and sign in with your initial super-admin email and password. The public directory requires no sign-in.

## Roles
- Super admin: full contact, account, branding and audit control.
- Department admin: contact CRUD within assigned department; can create/manage general-user accounts in that department.
- General user: public directory search only.

## Notifications
Contact CRUD performed by department admins creates an audit record and attempts to send an email via Gmail SMTP to active super admins. Configure a Google App Password where available. Sending is rate-limited by Google and is not unlimited. Failed notifications are recorded in audit history, but this prototype does not yet provide a durable retry queue.

## Notes before production / LAN exposure
This is a functional local-first starter, not yet production hardened. Add CSRF-resistant cookie-based auth, HTTPS, API rate limiting, audit coverage for user/setting changes, durable Celery/Redis email queue, database migrations, backups, email retry controls, and security review before deployment to a corporate network. Local session tokens expire after 12 hours. Do not enable Flask debug mode on a shared network. Do not publish this local prototype directly to the internet.
