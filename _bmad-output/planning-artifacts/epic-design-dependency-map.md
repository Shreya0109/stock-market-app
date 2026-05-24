---
workflowType: 'epic-design-dependency-map'
project_name: 'Trade_analytics'
date: '2026-05-23'
inputDocuments:
  - 'stock-market-app/_bmad-output/planning-artifacts/epics.md'
  - 'stock-market-app/_bmad-output/planning-artifacts/architecture.md'
  - 'docs/alphamomentum_bmad_markdown_bundle.md'
externalReferences:
  - 'https://docs.alpaca.markets/us/v1.4.2/docs/about-market-data-api'
  - 'https://polygon.io/docs'
  - 'https://www.alphavantage.co/documentation/'
  - 'https://docs.data.nasdaq.com/docs/getting-started'
---

# AlphaMomentum Epic Design and Dependency Map

## Purpose

This document expands the MVP epics into implementation design notes and maps the external dependencies required by each epic. It is intended to be used before sprint planning so stories can be sequenced with realistic provider, API, data, and infrastructure assumptions.

## MVP Dependency Posture

For MVP, use the smallest dependency set that proves the recommendation workflow:

- Market data provider for daily OHLCV and recent historical bars.
- Metadata/fundamental source for market cap and symbol quality filters.
- PostgreSQL for persistence.
- Basic scheduled job runner for the daily pipeline.
- API/UI libraries already selected in the architecture.

Do not require Redis, TimescaleDB, object storage, managed workflow orchestration, broker execution, or full managed auth for MVP. Keep those in backlog unless scale triggers are met.

## Recommended External Data Strategy

### MVP Primary Provider Choice

Use one primary market-data provider behind an internal `MarketDataProvider` interface.

Recommended MVP candidates:

| Provider | MVP Use | Notes |
|---|---|---|
| Alpaca Market Data API | Historical and latest stock bars; possible simple MVP provider if plan coverage is sufficient | Alpaca docs describe real-time and historical market data for equities and options, with stock bar support through its API/SDK. |
| Polygon.io | Historical aggregates and ticker/reference data | Strong fit for OHLCV aggregates and broad market data coverage; likely a better production-grade market data choice if budget allows. |
| Alpha Vantage | Backup/secondary source for daily time series, company overview, listing status, options/put-call features | Useful for MVP experimentation and later sentiment/options enrichment, but rate limits and entitlement should be validated. |
| Nasdaq Data Link | Backlog/premium data source | Better suited once premium datasets or institutional-grade sources are justified. |

### MVP Recommendation

Start with `Alpaca` or `Polygon` for OHLCV behind a provider abstraction, and use `Alpha Vantage` or a provider-supported fundamentals endpoint for market cap and listing status only if the primary provider does not cover those fields cleanly.

The code should not assume a single vendor shape. All external responses should be normalized into internal tables before indicators or scoring run.

## Cross-Epic External Dependency Matrix

| Epic | External Dependencies | MVP Required? | How It Is Used |
|---|---|---:|---|
| Epic 1: Foundation | Next.js, FastAPI, PostgreSQL, Docker, Python/Node package registries | Yes | Local app/runtime setup, migrations, test harness |
| Epic 2: Market Data Ingestion | Alpaca or Polygon; optional Alpha Vantage/Finnhub-style fundamentals source | Yes | Fetch OHLCV, symbol universe/metadata, market cap, avg volume, last close |
| Epic 3: Indicators | Python indicator library or internal calculations; no external API | Yes | Compute EMA, ATR, RSI, ADX, RVOL from persisted OHLCV |
| Epic 4: Filtering and Scoring | Optional Put/Call/sentiment source | Partial | Use MQS when available; fallback score when unavailable |
| Epic 5: Recommendation Engine | No new external API | Yes | Generate entry/stop/target/rationale from internal data |
| Epic 6: Recommendation API | No third-party API required for MVP | Yes | Serve persisted recommendation data from PostgreSQL |
| Epic 7: Dashboard UX | shadcn/ui, browser APIs; optional chart library | Yes | Render Daily 5, detail panel, history, warnings |
| Epic 8: Outcomes and Ops | Market data provider for post-publication bars; optional alert channel | Yes/Partial | Evaluate target/stop/invalidation; alert operator on failures |

## Epic 1 Design: MVP Foundation and Local Development

### Scope

Establish the codebase and local environment for web, API, scheduled pipeline, database, migrations, and tests.

### External Dependencies

- Node package registry for Next.js, React, Tailwind, shadcn/ui.
- Python package registry for FastAPI, SQLAlchemy, Alembic, pytest, pandas/numpy.
- PostgreSQL Docker image for local development.

### How We Use Them

- Next.js hosts the dashboard shell and later consumes the FastAPI endpoints.
- FastAPI exposes health, recommendation, detail, history, and pipeline-status APIs.
- PostgreSQL is the single MVP source of truth.
- Docker Compose starts only the minimum local dependencies: PostgreSQL and API/web services as needed.

### Key Design Decisions

- Keep repository structure simple: `apps/web`, `apps/api`, `services/pipeline`, `infra`.
- Keep domain logic reusable by API and pipeline without introducing a heavy shared-package abstraction too early.
- Add a fixture-based test harness immediately because deterministic output is a core product requirement.

### Outputs

- Local app skeletons.
- Database migration baseline.
- Test commands.
- Local setup documentation.

## Epic 2 Design: Market Data Ingestion and Freshness

### Scope

Fetch and normalize daily OHLCV, recent historical bars, symbol metadata, market cap, average volume, and last close. Block publishing when required data is missing or stale.

### External Dependencies

Primary:

- `Alpaca Market Data API` or `Polygon.io`.

Secondary/optional:

- `Alpha Vantage` company overview/listing status if the primary provider does not provide sufficient market cap or listing metadata.
- `Finnhub` or another fundamentals provider can be evaluated later if Alpha Vantage limits or coverage are insufficient.

### How We Use Market Data

For each configured symbol:

1. Fetch enough historical daily bars to compute EMA200 plus buffer.
2. Persist raw provider payload summary for audit/debug.
3. Normalize bars into `daily_bars`.
4. Upsert symbol metadata.
5. Validate latest trading date, required OHLCV fields, and symbol coverage.
6. Mark each symbol as `READY`, `INCOMPLETE`, `STALE`, or `FAILED`.
7. Block recommendation publication if required coverage falls below MVP threshold.

### Provider Interface

```text
MarketDataProvider
- get_daily_bars(symbols, start_date, end_date) -> list[DailyBarDTO]
- get_symbol_metadata(symbols) -> list[SymbolMetadataDTO]
- get_market_calendar(start_date, end_date) -> list[TradingDayDTO] optional
```

### Internal Normalized Fields

`daily_bars`:

- symbol
- trading_date
- open
- high
- low
- close
- adjusted_close optional
- volume
- provider
- provider_payload_hash
- ingested_at

`symbols`:

- symbol
- name optional
- exchange optional
- asset_type
- active
- market_cap optional
- avg_volume_90d optional
- last_close
- metadata_provider
- metadata_updated_at

### Freshness Rules

- Latest daily bar must match the latest expected completed US trading day.
- Required OHLCV fields must be non-null.
- Metadata required for liquidity gates must be present for a symbol to qualify.
- A provider failure must fail the run loudly, not silently skip affected symbols.

### MVP Open Questions

- Choose primary provider: Alpaca vs Polygon.
- Decide symbol universe seed: static config list, S&P 500-like list, Russell-like list, or provider ticker endpoint.
- Decide whether market cap comes from primary provider or Alpha Vantage-style company overview.

## Epic 3 Design: Indicator Computation

### Scope

Compute all technical indicators required by gates, scoring, risk calculations, and explanations.

### External Dependencies

- No market data API dependency at this stage; it consumes persisted OHLCV.
- Python calculation dependency can be one of:
  - internal pandas/numpy implementation for EMA, ATR, RSI, ADX, RVOL
  - vetted technical analysis library if it is actively maintained and testable

### How We Use It

The indicator job reads `daily_bars`, computes indicators per symbol/date, and persists results in `indicator_values` or equivalent tables.

### Required Outputs

- EMA9
- EMA21
- EMA50
- EMA200
- ATR14
- RSI
- ADX
- relative volume
- breakout reference levels

### Design Notes

- Persist indicator values instead of recomputing them on each API request.
- Mark insufficient lookback as an eligibility failure, not an exception.
- Store calculation version so future formula changes are auditable.
- Unit tests must compare fixed fixtures against expected values.

## Epic 4 Design: Filtering, Scoring, and Candidate Ranking

### Scope

Apply liquidity gates, momentum gates, MQS/fallback scoring, and deterministic ranking.

### External Dependencies

MVP:

- None required beyond persisted market data and metadata.

Optional/backlog:

- Put/Call ratio or options sentiment provider.
- Alpha Vantage documents realtime and historical put-call ratio APIs; this can support Phase 2 or optional MQS enrichment if entitlement is acceptable.

### How We Use It

1. Load eligible symbols with latest metadata and indicators.
2. Apply liquidity gates:
   - market cap greater than 2B
   - 90-day average daily volume greater than 1M
   - last close greater than 10
3. Apply momentum gates:
   - close greater than EMA50
   - EMA50 greater than EMA200
   - RSI between 60 and 75
   - ADX greater than 25
   - relative volume greater than 2.0 when available
4. Score candidates.
5. Rank candidates deterministically.

### MQS Strategy

Use MQS only when Put/Call data is available:

```text
MQS = (six_month_price_change / volatility) * (1 / put_call_ratio)
```

MVP fallback score should be the default path until options data is confirmed:

```text
fallback_score = weighted(price_momentum, volatility_quality, trend_confirmation, relative_volume)
```

### Design Notes

- Every gate result must persist pass/fail, input value, threshold, and reason.
- Tie handling must be explicit, for example score descending, then relative volume descending, then symbol ascending.
- Scoring config must include a version.

## Epic 5 Design: Recommendation Engine and Explanation Layer

### Scope

Convert ranked candidates into immutable Daily 5 recommendation records with risk plan, invalidation, and deterministic rationale.

### External Dependencies

- No new external API dependency.
- Consumes internal outputs from Epics 2-4.

### How We Use It

For each selected candidate:

1. Classify setup as breakout, continuation, or pullback.
2. Calculate entry zone from EMA21 to EMA9.
3. Calculate stop using `entry - (2 x ATR14)`.
4. Calculate target using `entry + (3 x ATR14)`.
5. Calculate risk/reward.
6. Attach invalidation rules.
7. Generate deterministic explanation text from templates.
8. Persist immutable published recommendation record.

### Design Notes

- Explanation templates must not invent unsupported claims.
- Sentiment must display `unavailable` when data is absent.
- Publication should be idempotent by trading date and run ID.

## Epic 6 Design: Recommendation API

### Scope

Expose MVP endpoints for the dashboard and any future consumers.

### External Dependencies

- No external data provider dependency.
- Depends on PostgreSQL.
- Auth is simple/private boundary for MVP; managed auth remains backlog until real user accounts exist.

### API Surface

```text
GET /health
GET /api/recommendations/today
GET /api/recommendations/{id}
GET /api/recommendations/history
GET /api/pipeline/status
```

### How We Use It

- Dashboard calls `today` for the primary Daily 5 view.
- Detail panel calls by recommendation ID or receives enough data from `today` to avoid an extra call.
- History view calls bounded/paginated history.
- Status widgets call pipeline status.

### Design Notes

- Use database indexes before adding Redis.
- Include freshness and stale/no-recommendation states in API responses.
- Expose only user-facing logic summaries, not full raw provider payloads.

## Epic 7 Design: Daily 5 Dashboard UX

### Scope

Build the beginner-friendly dashboard experience for today's recommendations, detail review, stale states, and history.

### External Dependencies

- Next.js/React.
- Tailwind and shadcn/ui.
- Optional lightweight charting library can be deferred unless a story explicitly needs charts.

### How We Use It

- Render Daily 5 as the primary first-screen view.
- Use detail panel for setup/rationale/risk/invalidation.
- Surface data freshness and blocked states.
- Render recent history and outcomes.

### Design Notes

- Do not build a pro trading terminal.
- Prioritize readable cards/rows, clear risk labels, and beginner-friendly wording.
- Mobile support means 390px safe review, not a full mobile trading workflow.
- Educational/non-advisory posture should be visible without overwhelming the UI.

## Epic 8 Design: Outcome Tracking and MVP Operations

### Scope

Track recommendation outcomes and provide enough operational visibility to safely run the MVP.

### External Dependencies

- Market data provider from Epic 2 for post-publication OHLCV bars.
- Optional alert channel:
  - email
  - Slack webhook
  - provider/platform notification

### How We Use It

1. Daily outcome job reads open recommendations.
2. Fetch or reuse latest bars.
3. Evaluate target hit, stop hit, invalidation, expiration, or still-open state.
4. Persist outcome state, timestamp, and reason.
5. Emit alert or operator-visible status for failed jobs, stale data, or missed deadline.

### Design Notes

- Outcome evaluation should reuse the same provider abstraction as ingestion.
- Alerts can start as persisted operator-visible records; Slack/email integration can be added after MVP if needed.
- Runbook should document stale data, provider failure, failed scheduled job, and rerun procedure.

## Backlog Dependency Notes

### Redis

Add only if measured database-backed reads exceed the 500ms p95 target under realistic usage.

### TimescaleDB

Add only when OHLCV/indicator volume, retention, or backtesting query patterns justify time-series optimization.

### Object Storage

Add when raw provider payloads, exports, or reports become too large for comfortable PostgreSQL storage.

### Managed Workflow Orchestration

Add when the scheduled job needs backfills, dependency visualization, retries, or operator controls beyond simple scheduling.

### Managed Auth

Add when real user accounts, watchlists, preferences, account-balance inputs, or role-based access enter scope.

### Options/Sentiment Data

Add when MQS must use Put/Call ratio as a required signal rather than an optional enhancement. Until then, fallback scoring is the MVP default.

## Provider Selection Checklist

Before sprint planning Epic 2, select the MVP provider by answering:

1. Does the provider return daily OHLCV bars with enough history for EMA200?
2. Does the provider support the planned symbol universe size without painful rate limits?
3. Does the provider include market cap and average volume, or do we need a metadata secondary source?
4. Does the license/plan allow our intended usage and display?
5. Can responses be tested with a mock provider and normalized cleanly?
6. Can we detect stale data, missing bars, and provider failures reliably?

## Source Notes

- Alpaca Market Data API documentation describes access to real-time and historical data for equities, options, crypto, and other market data.
- Polygon documentation provides market data REST APIs, including stock data and aggregate bars.
- Alpha Vantage documentation includes core stock time series, company overview, listing status, news/sentiment, and options-related endpoints such as put-call ratio.
- Nasdaq Data Link documentation describes REST/streaming APIs and free/premium datasets, better suited as a later provider evaluation path.
