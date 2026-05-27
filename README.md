# Breathe ESG Ingestion Prototype

A Django REST + React prototype for ingesting SAP fuel/procurement, utility electricity, and corporate travel data, normalizing it into auditable emission activity rows, and giving analysts a review dashboard.

## Tech Stack

- Backend: Django, Django REST Framework, SQLite locally, Postgres-ready on Render
- Frontend: React + Vite
- Deployment: Render single web service serving Django API and built React assets

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py seed_demo
python backend/manage.py runserver
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` to Django at `http://localhost:8000`.

## Demo Flow

1. Open the dashboard.
2. Use the sample selector to load SAP, utility, or travel sample CSV.
3. Click Import.
4. Review suspicious/failed rows.
5. Approve valid rows. Approved rows become locked for audit.

## Deployment

Render can deploy this repository as one service using `render.yaml`.

Build command:

```bash
pip install -r requirements.txt && cd frontend && npm install && npm run build && cd .. && python backend/manage.py collectstatic --noinput && python backend/manage.py migrate && python backend/manage.py seed_demo
```

Start command:

```bash
gunicorn config.wsgi:application --chdir backend
```

Set `SECRET_KEY`, `DEBUG=False`, and a Render Postgres `DATABASE_URL`.

## API

- `GET /api/summary/`
- `GET /api/activities/`
- `POST /api/ingest/{sap|utility|travel}/`
- `POST /api/activities/{id}/approve/`
- `GET /api/audit/`

## Submission Docs

- [MODEL.md](MODEL.md)
- [DECISIONS.md](DECISIONS.md)
- [TRADEOFFS.md](TRADEOFFS.md)
- [SOURCES.md](SOURCES.md)

