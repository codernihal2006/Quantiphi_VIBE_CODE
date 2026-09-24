# Evently — Quantiphi Vibe Coding

A small, viva-friendly event discovery platform built around the assessment brief.

## Stack

- FastAPI + Pydantic backend
- Optional MongoDB via Motor; an in-memory repository keeps the demo runnable without secrets
- React + Vite + TypeScript frontend
- Native WebSockets for live friend counts
- Optional Ticketmaster API integration with deterministic demo fallback

## Run locally

```bash
cp backend/.env.example backend/.env
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The default demo user is created automatically by the UI.

## Notes for the viva

- Routers are intentionally thin: request parsing and HTTP concerns live there; business rules live in services.
- The share click update uses an idempotent visitor set, so refreshes do not inflate the count.
- `X-User-Id` is a deliberately lightweight assessment auth substitute. JWT/session auth is the production upgrade.
- When `TICKETMASTER_API_KEY` or `MONGO_URI` is absent, the app uses local demo data so the calendar is never blank.

## Assessment brief

The attached brief is a source document for the feature requirements. Its proctoring, timing, and submission guidance are operational instructions for the candidate, not application requirements.
