# Torres-Perez Family Tree Phase 2

A private interactive family tree web app with:
- Admin login
- Family member login by first and last name
- Add/edit your own profile, spouse, and children
- Upload profile photos
- Search, birthday list, and interactive tree

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000

## Admin login

Username: `julianm`
Password: set in `.env` or initial default from app.py. Change it before publishing publicly.

## Notes

- The database is SQLite and is created automatically at `instance/family_tree.db`.
- Uploaded photos are stored in `static/uploads`.
- Family users login using their exact first and last name from the tree.

## Windows one-click run
Double-click `run-windows.bat`. It will create the virtual environment, install requirements, and start the app.

## Publish safely
Before putting this on the public internet, set these environment variables:

```powershell
$env:SECRET_KEY="make-this-a-long-random-value"
$env:ADMIN_USERNAME="julianm"
$env:ADMIN_PASSWORD="your-new-strong-password"
python app.py
```

If the database already exists, changing ADMIN_PASSWORD will not update the stored admin password. Delete `instance/family_tree.db` before first public launch, or add a password-reset screen later.
