# Hostel Management System (Django)

Hostel Management System is a Django 3.2 web app for managing hostel rooms, student registrations, and course information. It provides separate flows for students (self‑registration, bookings, profile management) and administrators (room/course CRUD, booking oversight, dashboard).

## Features
- Student side: sign up/sign in, browse rooms, submit hostel booking, view booking details, edit profile, change password.
- Admin side: staff login, dashboard with counts, create/edit/delete courses and rooms (fees, capacity, metadata), register students on behalf of walk‑ins, view booking details with computed costs, delete registrations, change password.
- Media uploads for profile pictures; static assets served from the `hostel/static/` directory.

## Tech Stack
- Python 3.10+ (tested with Django 3.2.10)
- Django 3.2.10
- SQLite (default `db.sqlite3`)
- Bootstrap/vanilla JS on the front end

## Project Layout
- `HostelManagementSystem/` – Django project root (settings, URLs, WSGI/ASGI).
- `HostelManagementSystem/hostel/` – main app with models, views, templates, static assets.
- `HostelManagementSystem/media/` – uploaded user files (profile images, etc.).
- `HostelManagementSystem/db.sqlite3` – development database with sample data (optional).
- `HostelManagementSystem/requirements.txt` – Python dependencies.

## Getting Started (Development)
1. Move into the Django project folder:
   ```bash
   cd HostelManagementSystem
   ```
2. Create & activate a virtual environment (Windows PowerShell):
   ```bash
   python -m venv .venv
   .\\.venv\\Scripts\\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Database setup:
   - To start fresh: delete `db.sqlite3` (optional) and run `python manage.py migrate`.
   - Or use the provided `db.sqlite3` to keep the sample data.
5. Create an admin/staff user for the custom admin portal:
   ```bash
   python manage.py createsuperuser --staff
   ```
6. Run the development server:
   ```bash
   python manage.py runserver
   ```
7. Access the app:
   - Student portal: `http://127.0.0.1:8000/`
   - Student login: `http://127.0.0.1:8000/user_login`
   - Admin portal: `http://127.0.0.1:8000/admin_login`
   - Django admin: `http://127.0.0.1:8000/admin/`

## Configuration Notes
- `DEBUG` is enabled by default (`settings.py`); disable for production.
- Static files are served automatically in development. For production, run `python manage.py collectstatic` and configure a static files host.
- Media uploads are written to `HostelManagementSystem/media`; ensure this path is writable in your environment.
- All URLs are defined in `HostelManagementSystem/HostelManagementSystem/urls.py`.

## Running Migrations
If you modify models, apply migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Tests
Placeholder `tests.py` exists in the app; no automated tests are currently implemented.

## Troubleshooting
- Authentication failing on admin pages: ensure you created a staff/superuser (`createsuperuser --staff`) and that you log in via `/admin_login`.
- CSRF issues on custom forms: some endpoints are marked `@csrf_exempt`; ensure you keep them protected if you harden the app for production.
- If you see missing table errors, recreate the database with `migrate` after deleting `db.sqlite3`.

## License
Not specified. Add a license before distributing or deploying.
