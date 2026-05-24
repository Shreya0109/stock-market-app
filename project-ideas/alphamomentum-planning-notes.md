# AlphaMomentum Planning Notes

Source documents:

- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/planning-artifacts/epics.md` (`epic.md` was not present; this is the matching artifact)
- `_bmad-output/planning-artifacts/epic-design-dependency-map.md`

## Precise Explanation

### Product Shape

AlphaMomentum is a daily swing-trading education product. It scans a configured universe of liquid US equities, applies deterministic momentum and liquidity rules, ranks candidates, and publishes 4-5 "Daily 5" recommendations before the market-open deadline.

The product is intentionally not a broker, execution system, or prediction engine. It should explain why each setup qualified, show the risk plan, and preserve enough data to audit every published recommendation later.

### Architecture

The MVP architecture is a lean modular monolith plus a scheduled batch pipeline.

Core runtime pieces:

- Next.js dashboard for the Daily 5 user experience.
- FastAPI backend for recommendation, detail, history, freshness, and health endpoints.
- Python scheduled pipeline for ingestion, indicators, filtering, scoring, recommendation publishing, and outcome evaluation.
- PostgreSQL as the MVP source of truth.
- Basic structured logs, persisted pipeline runs, freshness/deadline status, and operator-visible alerts.

Deferred pieces:

- Redis only if database-backed recommendation reads exceed 500ms p95.
- TimescaleDB only if OHLCV or indicator query volume justifies time-series optimization.
- Object storage only when raw provider payloads or reports become too large for PostgreSQL.
- Managed workflow orchestration only when cron-style scheduling is not enough.
- Managed auth only when user accounts, watchlists, preferences, or account-balance inputs become real product scope.

Important architecture clarification: the earlier idea document mentioned Spring Boot as a possible backend. The planning artifacts now choose FastAPI for the MVP backend, which keeps the API and Python trading domain closer together.

### Data Flow

The daily flow is:

1. Start a scheduled run before the 8:00 AM US Eastern publication deadline.
2. Load the configured symbol universe.
3. Fetch OHLCV and metadata from a market data provider.
4. Validate freshness, completeness, and required fields.
5. Store raw provider context for audit.
6. Normalize bars and metadata into PostgreSQL.
7. Compute indicators.
8. Apply liquidity and momentum gates.
9. Score and rank candidates deterministically.
10. Generate 4-5 recommendations if enough candidates pass.
11. Generate deterministic explanation text from templates.
12. Persist immutable recommendation records with score inputs, gate results, formula/config versions, freshness context, and rationale.
13. Serve today's published recommendations through the API and dashboard.
14. Track outcomes over time as open, target hit, stop hit, invalidated, or expired.

### Core Domain Model

The architecture identifies these core entities:

- `Symbol`: the tradable equity and its metadata.
- `DailyBar`: normalized OHLCV data by symbol and trading date.
- `IndicatorValue`: computed EMA, ATR, RSI, ADX, relative volume, and breakout values.
- `PipelineRun`: each scheduled ingestion/scoring/publishing run and its status.
- `CandidateScore`: gate results, score components, formula version, and ranking context.
- `Recommendation`: published Daily 5 item with setup, entry, stop, target, risk/reward, invalidation, and rationale.
- `RecommendationOutcome`: later state for a published recommendation.
- `AuditEvent`: supporting provenance and operational trace records.

### Epics

The MVP is split into eight implementation epics:

1. **MVP Foundation and Local Development**: create `apps/web`, `apps/api`, `services/pipeline`, and `infra`; add FastAPI, Next.js, PostgreSQL, migrations, and test harness.
2. **Market Data Ingestion and Freshness**: add provider abstraction, symbol universe config, OHLCV ingestion, metadata ingestion, and publish blocking for stale or incomplete data.
3. **Indicator Computation**: compute and persist EMA9, EMA21, EMA50, EMA200, ATR14, RSI, ADX, relative volume, and breakout levels.
4. **Filtering, Scoring, and Candidate Ranking**: apply liquidity gates, momentum gates, MQS when Put/Call data exists, fallback scoring otherwise, and deterministic tie handling.
5. **Recommendation Engine and Explanation Layer**: classify setup type, calculate entry/stop/target/risk-reward, attach invalidation rules, generate deterministic rationale, and publish immutable Daily 5 records.
6. **Recommendation API**: expose today's recommendations, recommendation detail, recommendation history, and pipeline status.
7. **Daily 5 Dashboard UX**: build the dashboard, detail panel, stale states, warning states, history view, keyboard navigation, and 390px-safe layout.
8. **Outcome Tracking and MVP Operations**: track recommendation outcomes, evaluate open recommendations daily, persist pipeline logs, expose alerts, and write the runbook.

### Trading Logic Boundary

The MVP rules are deliberately simple and auditable:

- Liquidity gates require market cap greater than 2B, 90-day average volume greater than 1M, and last close greater than 10.
- Momentum gates require close greater than EMA50, EMA50 greater than EMA200, RSI between 60 and 75, ADX greater than 25, and relative volume greater than 2.0 when available.
- Entry zone is the EMA21 to EMA9 range.
- Stop loss is `entry - (2 x ATR14)` unless a documented strategy override exists.
- First target is `entry + (3 x ATR14)` unless a documented strategy override exists.
- MQS is used only when Put/Call data is available: `(six_month_price_change / volatility) * (1 / put_call_ratio)`.
- The MVP default should be fallback scoring with weighted price momentum, volatility quality, trend confirmation, and relative volume.

Every gate result should preserve pass/fail state, input value, threshold, and reason. Every scoring result should preserve score components and config/formula version.

### External Dependencies

The dependency map recommends one primary market data provider behind an internal `MarketDataProvider` interface.

Provider options:

- Alpaca: practical MVP candidate for historical/latest bars if plan coverage is sufficient.
- Polygon.io: strong candidate for production-grade OHLCV aggregates and ticker/reference data.
- Alpha Vantage: useful secondary source for company overview, listing status, sentiment, or Put/Call experimentation, but rate limits and entitlement must be checked.
- Nasdaq Data Link: better as a later premium data source.

The implementation should normalize all provider responses before indicator computation or scoring. Nothing downstream should depend on vendor-specific response shapes.

Proposed provider interface:

```text
MarketDataProvider
- get_daily_bars(symbols, start_date, end_date) -> list[DailyBarDTO]
- get_symbol_metadata(symbols) -> list[SymbolMetadataDTO]
- get_market_calendar(start_date, end_date) -> list[TradingDayDTO] optional
```

### API Surface

The MVP API should start with:

```text
GET /health
GET /api/recommendations/today
GET /api/recommendations/{id}
GET /api/recommendations/history
GET /api/pipeline/status
```

The API must return explicit states for stale data, blocked publication, no recommendations, and not-yet-run pipeline status. It should expose user-facing logic summaries, not raw provider payloads.

### UX Direction

The dashboard should be calm, beginner-friendly, and focused on review, not a pro trading terminal.

The first screen should show the Daily 5. Each item needs ticker, setup type, score, entry, stop, target, risk/reward, invalidation, and short rationale. A detail panel should expand the setup, why-now explanation, trade plan, risk, invalidation, freshness, and rationale without losing dashboard context.

Risk, stop-loss, stale data, blocked publication, invalidation, and unavailable sentiment states must be visually clear. The UI must also support keyboard navigation, WCAG 2.1 AA contrast, and a mobile-safe 390px review layout.

## Fast Action Items

### Start Today

1. Decide MVP provider: Alpaca or Polygon for OHLCV.
2. Decide metadata source: primary provider fields or Alpha Vantage company overview.
3. Pick the first symbol universe: static curated US liquid equities list is fastest.
4. Create the repo skeleton: `apps/web`, `apps/api`, `services/pipeline`, `infra`.
5. Add local PostgreSQL with Docker Compose.
6. Add FastAPI `/health`.
7. Add Next.js dashboard placeholder for Daily 5.
8. Add test harness for backend/pipeline deterministic fixtures.

### First Implementation Slice

Build a vertical slice before expanding every indicator or screen:

1. Mock provider returns fixed OHLCV and metadata for 10-20 symbols.
2. Pipeline ingests mock data into PostgreSQL.
3. Freshness check blocks missing/stale mock data.
4. Compute EMA50, EMA200, ATR14, RSI, ADX, and relative volume for fixtures.
5. Apply liquidity and momentum gates.
6. Generate fallback scores.
7. Publish a deterministic Daily 5 record.
8. Serve it from `GET /api/recommendations/today`.
9. Render it on the dashboard.

### Decisions To Lock Before Coding Too Far

1. Primary data provider and paid/free plan constraints.
2. Exact initial symbol universe.
3. Whether MVP runs pre-market using prior completed daily bars or after market close.
4. Tie-breaker order for deterministic ranking, for example score descending, relative volume descending, symbol ascending.
5. Initial fallback scoring weights.
6. Recommendation expiration rule, for example expire after N trading days if neither target nor stop is hit.
7. The exact educational/non-advisory disclaimer text.

### Good First Tickets

1. Scaffold FastAPI app with `/health`, structured logging, and pytest.
2. Scaffold Next.js app with a Daily 5 placeholder route.
3. Add PostgreSQL Docker Compose and Alembic baseline migration.
4. Define SQLAlchemy models for `symbols`, `daily_bars`, `pipeline_runs`, and `recommendations`.
5. Define Pydantic DTOs for market bars, symbol metadata, gate results, candidate scores, and recommendation summaries.
6. Implement `MockMarketDataProvider` with deterministic fixture data.
7. Implement freshness validation with explicit blocked reasons.
8. Write fixture tests proving identical inputs produce identical ranking output.

