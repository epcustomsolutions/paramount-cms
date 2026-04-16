# Paramount CMS (Claims Management System)

A Django-based claims management web app for a public adjusting company. Adjusters can manage clients, file and track insurance claims, log timestamped notes, upload documents, and schedule appointments tied to specific claims.

## Tech Stack

- **Python 3.12+** / **Django 4.2**
- **PostgreSQL** (Neon) via `dj-database-url`
- **Bootstrap 5** (CDN) + custom `app.css` design tokens
- **HTMX** for modal CRUD and dynamic form updates
- **FullCalendar 6** (CDN) for the scheduling calendar
- **DataTables** (CDN) for paginated/searchable/sortable lists
- **WhiteNoise** for static file serving
- **Vercel** for deployment (serverless)

## Features

- **Clients** — full CRUD with contact info, address, alerts
- **Claims** — linked to clients; track claim number, status, insurance company, date of loss, description
  - **Notes** — timestamped notes on each claim, logged by the current user
  - **Documents** — upload/download PDF, Word, Excel files (stored in Postgres)
- **Schedule** — FullCalendar with drag/resize, appointments tied to a client and optionally a claim
- **Tools** — mileage tracker for field visits

## Local Development

1. Clone the repository
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your database URL and secret key
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
6. (Optional) Seed demo data:
   ```bash
   python manage.py seed_demo_data
   ```
7. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Deployment (Vercel)

The project includes `vercel.json`, `build_files.sh`, and `wsgi.py` configured for Vercel deployment. Set environment variables (`SECRET_KEY`, `DATABASE_URL`, `DEBUG=false`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`) in the Vercel dashboard.
