# Dashboard How It Works

## Purpose

The dashboard is an executive intelligence interface that turns collected cyber content into prioritized, filterable decision support for two modules:

- Executive Intelligence
- Compliance & Control Intelligence

## High-level flow

1. The frontend app loads and chooses an API base URL.
2. The frontend requests dashboard payloads from backend endpoints.
3. The backend aggregates collected content and enriches it with mappings and scoring.
4. The frontend renders metrics, widgets, trend charts, and feed items.
5. The executive dashboard auto-refreshes every 15 minutes.
6. The compliance module supports user-applied filters and recomputes module widgets.

## Frontend behavior

Main frontend orchestration is in [frontend/src/App.tsx](frontend/src/App.tsx).

### Module switch

The module switch toggles between:

- Executive Intelligence: baseline dashboard metrics, widgets, trends, and feed.
- Compliance & Control Intelligence: framework/regulator/control-centric lens with board report and filter set.

### Data loading

- Initial load runs both:
  - `loadDashboardData(false)`
  - `loadComplianceData({})`
- Background refresh runs only executive dashboard data every 15 minutes.
- The app tracks independent loading and error state for executive and compliance modules.

### Search and category filtering

For the executive module, the frontend applies client-side filtering over `dashboard.articles`:

- Search text checks title, summary, and source.
- Category filter checks exact category match or `All`.

### Compliance filters

Compliance filters are collected in local state and sent as query params to the compliance endpoint.
Supported filter keys include:

- `country`, `framework`, `regulator`, `control`, `industry`
- `risk_level`, `security_domain`
- `identity`, `cloud`, `ai`, `operational_resilience`, `privacy`, `critical_infrastructure`

## API client behavior

API request wrappers are in [frontend/src/api.ts](frontend/src/api.ts).

### Base URL resolution

The frontend resolves the backend URL in this order:

1. `VITE_API_BASE_URL` env var (if provided)
2. Codespaces same-origin proxy (`/api`)
3. localhost fallback (`http://localhost:8000` style)
4. host-derived `:8000` fallback

### Reliability in browser requests

- Per request timeout: 15 seconds
- Retry count: 1 retry after first failure
- Non-2xx responses include backend body text in thrown error

## Backend dashboard endpoints currently used by UI

Current module endpoints consumed by the frontend are in [backend/api.py](backend/api.py):

- `GET /dashboard`
- `GET /compliance-control-intelligence`

`/dashboard` returns an aggregate payload used for summary cards, trends, widgets, and feed display.
`/compliance-control-intelligence` returns compliance-focused records, filter metadata, dashboard aggregates, and board report content.

## Backend v2 executive endpoints available

A richer v2 API surface is also available in [backend/api.py](backend/api.py):

- `GET /v2/source-registry`
- `GET /v2/executive/dashboards`
- `GET /v2/executive/dashboards/{dashboard_id}`
- `GET /v2/executive/widgets/{dashboard_id}/{widget_id}`
- `GET /v2/executive/daily-brief`
- `GET /v2/executive/reports/{report_type}`
- `GET /v2/executive/search`
- `GET /v2/executive/scheduler`

Core v2 enrichment and dashboard composition logic is implemented in [backend/intelligence/engine.py](backend/intelligence/engine.py).
Registry loading and health metadata are implemented in [backend/intelligence/registry.py](backend/intelligence/registry.py).

## Compliance module response shape

The compliance payload includes:

- `module`, `audience`, `generatedAt`, `prioritization`
- `monitorScope` and `availableFilters`
- `filtersApplied`
- `widgets`
- `dashboard` sections:
  - `frameworkUpdates`
  - `regulatorUpdates`
  - `controlsImpacted`
  - `industryImpact`
  - `securityDomains`
- `boardReport`
- `count`, `items`

Type contracts are in [frontend/src/types.ts](frontend/src/types.ts).

## Data model and enrichment

The platform normalizes and stores enriched records using [backend/models/intelligence_record.py](backend/models/intelligence_record.py).
The enrichment engine derives fields such as:

- frameworks and controls
- industry and technology impact
- security domains
- risk level and quality scoring
- executive and operational impact summaries

## Scheduler and timing

Scheduler metadata is available via [backend/intelligence/scheduler.py](backend/intelligence/scheduler.py).
The backend now also runs an in-process daily scheduler that triggers ingestion and enrichment automatically.
Default jobs define intended cadence for:

- source collection
- enrichment
- daily brief generation
- weekly and monthly reporting

### Automatic morning refresh

The FastAPI app starts a daily UTC scheduler at startup and stops it at shutdown.
By default, it runs once per day at `06:00` UTC and refreshes the intelligence pipeline.
Scheduler runtime status is exposed at `GET /v2/executive/scheduler` under `runtime`.

Supported environment variables:

- `EXEC_DAILY_REFRESH_ENABLED` (default `true`)
- `EXEC_DAILY_REFRESH_TIME_UTC` (default `06:00`, format `HH:MM`)
- `EXEC_DAILY_REFRESH_MAX_SOURCES` (optional positive integer)

## Run and validate

Start backend:

```bash
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Run tests:

```bash
python -m pytest -q tests/test_executive_intelligence_v2.py
```

## Troubleshooting

### Backend not reachable from frontend

- Check backend is running on expected host/port.
- If using Codespaces, prefer same-origin `/api` routing.
- If setting custom backend URL, verify `VITE_API_BASE_URL`.

### Empty or stale dashboard

- Confirm ingestion/collection has populated source data.
- Trigger manual collection if required.
- Verify no API errors in frontend network logs.

### Compliance filters return few items

- Clear filters and re-apply one by one.
- Verify source content contains matching framework/control/domain terms.
