# TSF themes update

Based on TSF Analytics & Reports release.

## Themes
- Basic: original light/dark interface.
- Studio / Industrial: original orange/graphite hardware-inspired visual design.
- Signal / Pop: original violet/mint/yellow modern design.

The super-admin selects a **global default** in Settings. Department admins and super-admins can switch theme in the header; their choice is saved **per account in that browser's localStorage**, without changing the global default. Visitors see the global default. A local override remains in place even when the super-admin changes the default; clear site storage to remove it.

## General user role
The public directory already supports unauthenticated lookup. New general-user creation is removed from the Accounts form and blocked by the POST /api/users endpoint. Existing general-user accounts are preserved for compatibility and may be managed, but no new ones are created through this update. Existing records are not deleted.

## Installation
Back up backend/app.py, frontend/src/App.vue, frontend/src/style.css, and directory.db.
Replace files preserving paths. Keep backend/monthly_report.py from the ZIP.
Restart Flask and Vite. No DB migration required for themes (new theme_style setting is stored in the existing Setting table).

## Testing
- Sign in as super-admin; set default theme Studio and save.
- Open incognito/public directory: global default should apply.
- Sign in as department admin; choose Signal from header; refresh: preference should persist.
- Verify Contacts, Reports, audit, and intercom call button still function.
- Confirm POST /api/users with role=user is rejected.
- Verify new monthly email scheduler configuration is unchanged.

Note: Frontend build and Android device testing are not performed here.
