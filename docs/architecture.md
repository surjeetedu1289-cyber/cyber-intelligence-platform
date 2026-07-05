# Architecture Overview

## Backend

The backend is organized into the following layers:

- `backend/api.py`: FastAPI entrypoint exposing health, dashboard, and article endpoints.
- `backend/services/article_service.py`: Article persistence, deduplication, and dashboard aggregation logic.
- `backend/collectors/daily_collector.py`: Automated ingestion workflow with retry handling.
- `backend/database/db.py`: SQLAlchemy engine and session factory.
- `backend/config.py`: Environment-based application configuration.
- `backend/logging_config.py`: Central logging setup.
- `backend/exceptions.py`: Domain-specific exception classes.

## Frontend

The frontend is a React + TypeScript + TailwindCSS application with:

- responsive layout,
- dark mode,
- search and filtering,
- charts for trend analysis.

## Data

The platform uses SQLite initially for local persistence and can be migrated to PostgreSQL by changing `DATABASE_URL`.

## Deployment

The GitHub Actions workflow in `.github/workflows/deploy.yml` builds the frontend and runs the backend tests.
