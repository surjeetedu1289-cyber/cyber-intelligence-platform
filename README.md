# Cyber Intelligence Platform

A modern, enterprise-grade cyber intelligence platform built with FastAPI, React, TypeScript, TailwindCSS, and SQLite. The platform aggregates cybersecurity-related intelligence, stores deduplicated articles in a database, supports search and filtering, and provides a responsive executive dashboard for CISO-style monitoring.

## What is included

- Backend API with FastAPI
- SQLite-backed article storage with deduplication
- Daily collection workflow for automated intelligence ingestion
- React + TypeScript frontend with dark mode and search
- Recharts-based trend visualization
- GitHub Actions workflow for CI and deployment preparation

## Architecture

- Backend: [backend](backend)
- Frontend: [frontend](frontend)
- Data and storage: [data](data)
- Automation: [.github/workflows](.github/workflows)
- Dashboard guide: [docs/dashboard-how-it-works.md](docs/dashboard-how-it-works.md)
- GitHub Pages deployment: [docs/github-pages-deployment.md](docs/github-pages-deployment.md)

## GitHub Pages Deployment

The dashboard is deployed as a static site and does not require a running backend server.

- Deployment URL format: `https://<github-username>.github.io/cyber-intelligence-platform/`
- Static dashboard data path: `frontend/public/data/*.json`
- Daily automation workflow: `.github/workflows/daily-update.yml`
- Pull request validation workflow: `.github/workflows/deploy.yml`

## Run locally

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the backend:
   ```bash
   python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
   ```
3. In a second terminal, start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Open http://localhost:3000

## Automated collection

The daily collector can be run manually with:

```bash
python -m backend.collectors.daily_collector
```

## Testing

```bash
python -m pytest -q
```
