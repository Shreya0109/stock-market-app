# AlphaMomentum Project Flow And File Map

Last reviewed: 2026-06-07

This document explains how the application currently runs, how data moves through it, how to build and test it, and what each meaningful project file does.

## 1. What This Project Is

AlphaMomentum is an MVP stock-market recommendation application.

The intended product flow is:

1. Load a configured stock symbol universe.
2. Fetch daily OHLCV bars and symbol metadata.
3. Store normalized market data in SQLite for local MVP development.
4. Validate data completeness and freshness.
5. Block recommendation generation/publishing when data cannot be trusted.
6. Later epics compute indicators, filter candidates, score them, generate recommendations, expose recommendation APIs, and show them in the web dashboard.

Current implementation status:

- Implemented: FastAPI app, health endpoint, SQLite models, market-data provider abstraction, mock provider, Yahoo Finance provider, symbol universe file, market-data ingestion, freshness validation, pipeline status/run endpoints, scheduled pipeline job, Next.js dashboard shell, backend tests.
- Partially implemented: indicators, liquidity/momentum gates, MQS scoring, recommendation card UI.
- Not yet implemented: actual recommendation generation endpoint at `/api/recommendations/today`, full indicator persistence pipeline, candidate ranking pipeline, recommendation publishing flow, frontend tests.

## 2. Local Runtime Flow

### Backend API

Run from the repository root:

```bash
cd /home/shubhankar/stock-market-app
python -m pip install -r requirements.txt
MARKET_DATA_PROVIDER=mock python -m uvicorn apps.api.app.main:app --reload
```

For live Yahoo Finance data:

```bash
MARKET_DATA_PROVIDER=yahoo python -m uvicorn apps.api.app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Useful backend endpoints:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/pipeline/status
curl -X POST http://127.0.0.1:8000/api/pipeline/run
```

What happens on backend startup:

1. `apps.api.app.main` creates the FastAPI app.
2. Lifespan startup calls `init_db()`.
3. `init_db()` creates missing SQLite tables in `alphamomentum.db`.
4. A narrow SQLite compatibility migration adds newer `symbols` columns if needed.
5. APScheduler starts.
6. The daily market-data pipeline job is registered using `PIPELINE_HOUR` and `PIPELINE_MINUTE`.
7. Routers are mounted: `/health` and `/api/pipeline/*`.

### Frontend Web App

Run from the web app folder:

```bash
cd /home/shubhankar/stock-market-app/apps/web
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

Frontend API base URL:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

If needed, create `apps/web/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Current frontend behavior:

1. `apps/web/app/page.tsx` renders the Daily 5 dashboard.
2. It calls `getRecommendations()` from `apps/web/lib/api.ts`.
3. That client attempts to fetch `GET /api/recommendations/today`.
4. That backend endpoint does not exist yet.
5. The page catches the failure and displays built-in mock recommendations.

## 3. Build, Test, And Verification

### Backend Tests

Run from repository root:

```bash
pytest apps/api/tests
```

Current result from this review:

```text
5 passed
```

Tests covered:

- `/health` ASGI response.
- Market-data ingestion persists metadata and daily bars.
- Re-running ingestion is idempotent for the same symbol/date.
- Freshness blocks missing data.
- Freshness passes after complete ingestion.
- Freshness blocks stale OHLCV data.

### Frontend Development

```bash
cd apps/web
npm run dev
```

### Frontend Production Build

```bash
cd apps/web
npm run build
```

Current result from this review:

```text
Compiled successfully
Route: /
```

Note: the first build attempt inside the restricted sandbox failed because Turbopack needed to create a worker process and bind to a port. Running the same build with normal permissions succeeded.

### Frontend Lint

Configured command:

```bash
npm run lint
```

Current result:

```text
Invalid project directory provided, no such directory: .../apps/web/lint
```

Reason: `package.json` still uses `next lint`, but the installed Next.js version is `16.2.6`, where this command path is no longer valid in this setup. This script needs to be replaced with an ESLint command and explicit ESLint config if linting is required.

## 4. Market Data Pipeline Flow

Manual trigger:

```bash
curl -X POST http://127.0.0.1:8000/api/pipeline/run
```

Runtime flow:

1. `apps/api/routers/pipeline.py` handles `POST /api/pipeline/run`.
2. It reads `MARKET_DATA_PROVIDER` from `apps/api/config.py`.
3. It calls `get_provider()` in `services/provider.py`.
4. Provider options:
   - `mock`: deterministic local data, used by default and by tests.
   - `yahoo`, `yfinance`, `yahoo_finance`: live Yahoo Finance through `yfinance`.
5. `run_market_data_pipeline()` in `services/pipeline/market_data.py` creates a `PipelineRun`.
6. It loads symbols from `config/symbol_universe.txt`.
7. For each symbol, `ingest_market_data()` fetches:
   - metadata: name, market cap, 90-day average volume, last close.
   - historical bars: daily open, high, low, close, volume.
8. Bars are normalized to uppercase symbols and midnight dates.
9. Symbols are upserted into `symbols`.
10. Bars are upserted into `daily_bars`.
11. `validate_data_freshness()` checks each configured symbol.
12. If any required data is missing, stale, or incomplete, the pipeline run status becomes `blocked`.
13. If every symbol passes, status becomes `success`.
14. `GET /api/pipeline/status` returns current publish readiness, reasons, and latest run.

Freshness rules:

- Every configured symbol must have active metadata.
- Required metadata: `market_cap`, `avg_volume_90d`, `last_close`, `metadata_updated_at`.
- Every configured symbol must have at least one OHLCV bar.
- Latest OHLCV date must be no older than `FRESHNESS_MAX_STALE_DAYS`.
- OHLCV fields cannot be missing.

Important environment variables:

```bash
DATABASE_URL=sqlite:///./alphamomentum.db
MARKET_DATA_PROVIDER=mock
SYMBOL_UNIVERSE_FILE=config/symbol_universe.txt
PIPELINE_HOUR=16
PIPELINE_MINUTE=0
FRESHNESS_MAX_STALE_DAYS=5
```

## 5. Database Flow

Local database:

```text
alphamomentum.db
```

ORM tables:

- `symbols`: one row per tradable equity symbol and its metadata.
- `daily_bars`: normalized OHLCV bars; uniqueness is symbol/date.
- `indicator_values`: planned persisted indicators.
- `recommendations`: planned daily recommendation records.
- `pipeline_runs`: pipeline execution status, timing, counts, and error/block reasons.

Current persistence path:

```text
Yahoo/mock provider
  -> services.provider.OHLCV / SymbolMetadata
  -> services.pipeline.ingest_market_data()
  -> SQLAlchemy models
  -> SQLite alphamomentum.db
```

## 6. Web Flow

Current page route:

```text
/
```

Current page flow:

1. `apps/web/app/layout.tsx` defines global metadata and HTML shell.
2. `apps/web/app/globals.css` defines dashboard styles.
3. `apps/web/app/page.tsx` runs as a client component.
4. It initializes with mock recommendation cards.
5. It calls `apps/web/lib/api.ts -> getRecommendations()`.
6. The client requests `GET /api/recommendations/today`.
7. Since that endpoint is not implemented, the frontend keeps mock recommendations and shows an error notice.
8. `apps/web/components/RecommendationCard.tsx` renders each card.

What the frontend currently shows:

- Header: AlphaMomentum / Daily 5.
- Loading/data-ready status pill.
- Error warning if API recommendations are unavailable.
- Three mock recommendation cards.
- Educational disclaimer.

## 7. Repository Map

### Root Files

`DEVELOPMENT.md`

- Existing quick-start guide.
- Explains backend/frontend run commands, project structure, environment variables, tests, and troubleshooting.
- Some details are now stale: it says Python 3.14+, but the current environment used Python 3.12.3 successfully.

`requirements.txt`

- Python dependencies for the API and services.
- Includes FastAPI, Uvicorn, pytest, SQLAlchemy, Alembic, pandas, numpy, APScheduler, python-dotenv, and yfinance.

`pytest.ini`

- Configures pytest.
- Adds repo root to `pythonpath`.
- Sets test path to `apps/api/tests`.

`alphamomentum.db`

- Local SQLite database.
- Generated/updated by backend startup and pipeline runs.
- Should usually be treated as local runtime state, not application source.

`basic_info`

- Tiny note with the uvicorn command:
  `trade-env/bin/uvicorn apps.api.app.main:app --reload`.

`.gitignore`

- Git ignore rules.

### `apps/api`

`apps/api/app/main.py`

- FastAPI entrypoint.
- Initializes DB during lifespan startup.
- Starts APScheduler.
- Registers the daily market-data pipeline job.
- Includes health and pipeline routers.

`apps/api/app/models.py`

- SQLAlchemy ORM models.
- Defines `Symbol`, `DailyBar`, `IndicatorValue`, `Recommendation`, and `PipelineRun`.
- Also defines `utc_now_naive()` for timestamp defaults.

`apps/api/app/__init__.py`

- Marks `apps.api.app` as a Python package.

`apps/api/database.py`

- Creates SQLAlchemy engine and session factory.
- Defaults to SQLite at `sqlite:///./alphamomentum.db`.
- Exposes `init_db()` and FastAPI dependency `get_db()`.
- Contains a narrow SQLite schema compatibility helper for recently added symbol metadata columns.

`apps/api/config.py`

- Loads `.env` values via `python-dotenv`.
- Centralizes backend settings: DB URL, provider, symbol universe path, scheduler time, freshness threshold, gate thresholds, risk multipliers, feature flags.

`apps/api/routers/health.py`

- Defines `GET /health`.
- Returns `{"status": "UP"}`.

`apps/api/routers/pipeline.py`

- Defines `GET /api/pipeline/status`.
- Defines `POST /api/pipeline/run`.
- Serializes latest `PipelineRun`.
- Exposes freshness reasons to operators.

`apps/api/routers/__init__.py`

- Marks routers folder as a Python package.

`apps/api/tests/test_health.py`

- Tests the FastAPI app directly as an ASGI callable.
- Verifies `/health` returns HTTP 200 and `{"status": "UP"}`.

`apps/api/tests/test_market_data_pipeline.py`

- Uses in-memory SQLite.
- Tests ingestion idempotency.
- Tests missing-data, complete-data, and stale-data freshness behavior.

`apps/api/__init__.py`

- Marks `apps.api` as a Python package.

### `apps/web`

`apps/web/package.json`

- Frontend package metadata and scripts.
- Scripts:
  - `npm run dev`
  - `npm run build`
  - `npm run start`
  - `npm run lint` currently needs repair.
- Dependencies include Next.js, React, Tailwind-related packages, Radix Slot, axios, clsx utilities.

`apps/web/package-lock.json`

- Locked npm dependency graph.
- Ensures repeatable frontend installs.

`apps/web/app/layout.tsx`

- Root Next.js app layout.
- Defines metadata and imports global CSS.

`apps/web/app/page.tsx`

- Main dashboard page.
- Client component.
- Fetches recommendations from backend but falls back to mock recommendation data.

`apps/web/app/globals.css`

- Global dashboard styling.
- Defines CSS variables, layout, card styling, responsive behavior.

`apps/web/components/RecommendationCard.tsx`

- Presentation component for one recommendation.
- Formats price values.
- Displays symbol, setup type, MQS score, entry zone, stop, target, risk/reward, rationale, and optional put/call ratio.

`apps/web/lib/api.ts`

- Browser API client.
- Defines frontend `Recommendation` and `HealthResponse` TypeScript interfaces.
- Implements `getRecommendations()` and `getHealth()`.
- Defaults API base to `http://localhost:8000/api`.

`apps/web/next.config.ts`

- Next.js config.
- Currently empty/default.

`apps/web/tsconfig.json`

- TypeScript config.
- Strict mode enabled.
- Defines `@/*` path alias to project root inside `apps/web`.

`apps/web/postcss.config.mjs`

- PostCSS config.
- Uses `@tailwindcss/postcss` and `autoprefixer`.

`apps/web/tailwind.config.ts`

- Tailwind content paths and theme extension.
- Adds a slate color scale.

`apps/web/next-env.d.ts`

- Next.js generated TypeScript declarations.

### `services`

`services/provider.py`

- Market-data provider abstraction.
- Defines `OHLCV`, `SymbolMetadata`, `ProviderError`, and `MarketDataProvider`.
- Implements `MockMarketDataProvider`.
- Implements `YahooFinanceProvider` using `yfinance`.
- Provides `get_provider()` factory.

`services/pipeline/market_data.py`

- Core Epic 2 market-data pipeline.
- Loads symbol universe.
- Ingests provider OHLCV and metadata.
- Upserts symbols and bars.
- Validates freshness/completeness.
- Persists pipeline run status.

`services/pipeline/__init__.py`

- Exports pipeline functions and dataclasses for simpler imports.

`services/indicators.py`

- Indicator calculation helpers.
- Implements EMA, RSI, ATR, and relative volume.
- `calculate_adx()` is currently a placeholder that returns zero.

`services/gates.py`

- Candidate filtering logic.
- Defines liquidity, momentum, and sentiment gate thresholds.
- Applies gates to candidate dictionaries.
- Not yet wired into the pipeline/API.

`services/scoring.py`

- MQS scoring helper.
- Ranks candidates by `mqs`.
- Not yet wired into the pipeline/API.

`services/models.py`

- Domain dataclasses and enums independent from SQLAlchemy.
- Defines recommendation status, setup type, recommendation dataclass, and pipeline run dataclass.
- Includes `risk_reward` calculation on the recommendation dataclass.

`services/__init__.py`

- Marks services as a Python package.

### `config`

`config/symbol_universe.txt`

- Configurable baseline symbol universe.
- One ticker per line.
- Comments and blank lines are ignored.
- Current symbols: AAPL, MSFT, GOOGL, AMZN, NVDA.

### `flow`

`flow/application-flow-and-project-map.md`

- This file.
- Intended as the current operator/developer map for returning to the project after time away.

### `docs`

`docs/Product-Inspiration.md`

- Product inspiration/reference notes.

`docs/Product-Inspiration.txt`

- Text version of product inspiration/reference notes.

`docs/Product_vision notes`

- Product vision notes without extension.

`docs/Product_vision notes.md`

- Markdown version of product vision notes.

`docs/Stock-Analytics.code-workspace`

- VS Code workspace file.

### `project-ideas`

`project-ideas/alphamomentum-planning-notes.md`

- Early planning notes for AlphaMomentum.

`project-ideas/swing-trading-intelligence-platform.md`

- Early concept document for the trading intelligence platform.

### `_bmad-output/planning-artifacts`

These are planning outputs, not runtime code.

`prd.md`

- Product requirements document.
- Defines functional/non-functional requirements.

`architecture.md`

- Architecture decision document.
- Describes lean modular monolith, batch pipeline, database-backed MVP, deferred Redis/Timescale/object storage/orchestration.

`epics.md`

- Epic and story breakdown.
- Epic 2 is market-data ingestion and freshness.

`ux-design-specification.md`

- UX requirements for the Daily 5 dashboard.

`interactive-prototype.html`

- HTML prototype for UX exploration.

`epic-design-dependency-map.md`

- Maps design dependencies across epics.

`prd-validation-report.md`

- Validation report for PRD quality/readiness.

`brainstorming/brainstorming-session-2026-04-26-12-00.md`

- Captured brainstorming session.

### `_bmad`

These files configure the BMad planning/workflow system. They are not application runtime code.

`_bmad/bmm/config.yaml`

- BMad module config for project name, artifact locations, language, and user name.

`_bmad/core/config.yaml`, `_bmad/cis/config.yaml`, `_bmad/bmb/config.yaml`

- Additional BMad module configs.

`_bmad/config.toml`, `_bmad/config.user.toml`, `_bmad/custom/config.toml`

- BMad customization/configuration.

`_bmad/scripts/resolve_config.py`

- Helper script to resolve BMad config values.

`_bmad/scripts/resolve_customization.py`

- Helper script to merge BMad skill customizations.

`_bmad/_config/*.csv`, `_bmad/_config/manifest.yaml`, `_bmad/*/module-help.csv`

- BMad manifests and help metadata.

### `apps/backend`

This appears to be a stale/empty earlier backend tree.

- It contains only cache folders in the current working tree scan.
- Active backend code is under `apps/api`.
- Do not add new code to `apps/backend` unless the project intentionally revives that structure.

### Generated/Cache Folders

These are not source-of-truth files:

- `.git/`
- `.pytest_cache/`
- `__pycache__/`
- `apps/web/.next/`
- `apps/web/node_modules/`
- `trade-env/`
- `apps/backend/tests/.pytest_cache/`

## 8. Current Gaps And Next Engineering Steps

Most important gaps:

1. The frontend calls `/api/recommendations/today`, but the backend does not implement it yet.
2. Recommendation generation is not connected to the market-data pipeline.
3. Indicator computation exists as helper functions but is not persisted or orchestrated.
4. `calculate_adx()` is a placeholder.
5. Gates and scoring are not wired into a candidate generation flow.
6. `npm run lint` is broken for the current Next.js version/script.
7. SQLite is fine for local MVP work, but the planning artifacts expect PostgreSQL and Alembic migrations later.
8. `alphamomentum.db` is local runtime state and should be handled deliberately before commits.

Recommended next implementation sequence:

1. Add recommendation API endpoints, starting with `GET /api/recommendations/today`.
2. Add indicator computation pipeline that reads `daily_bars` and writes `indicator_values`.
3. Replace placeholder ADX with a tested implementation.
4. Connect liquidity gates, momentum gates, and MQS scoring.
5. Generate and persist recommendation records.
6. Update frontend to show real API status and recommendation data.
7. Fix frontend lint configuration.
8. Add frontend tests for dashboard rendering and API fallback states.

## 9. Quick Recovery Checklist

Use this when returning to the project after a break:

```bash
cd /home/shubhankar/stock-market-app
git status --short
python -m pip install -r requirements.txt
pytest apps/api/tests
MARKET_DATA_PROVIDER=mock python -m uvicorn apps.api.app.main:app --reload
```

In another terminal:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/api/pipeline/run
curl http://127.0.0.1:8000/api/pipeline/status
```

Frontend:

```bash
cd /home/shubhankar/stock-market-app/apps/web
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

