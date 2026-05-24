---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
inputDocuments:
  - 'stock-market-app/_bmad-output/planning-artifacts/prd.md'
  - 'stock-market-app/_bmad-output/planning-artifacts/ux-design-specification.md'
  - 'stock-market-app/_bmad-output/planning-artifacts/architecture.md'
  - 'docs/alphamomentum_bmad_markdown_bundle.md'
workflowType: 'epics-and-stories'
project_name: 'Trade_analytics'
date: '2026-05-23'
---

# Trade_analytics - Epic Breakdown

## Overview

This document breaks AlphaMomentum Recommender into MVP-prioritized epics and stories, using the PRD, UX specification, lean architecture blueprint, and uploaded AlphaMomentum bundle.

The MVP implementation principle is: prove the daily recommendation workflow before adding scale infrastructure. PostgreSQL-backed reads, a lightweight scheduled Python job, and basic monitoring are sufficient for MVP unless measured usage triggers Redis, TimescaleDB, object storage, managed orchestration, or managed auth.

## Requirements Inventory

### Functional Requirements

- FR-1: Ingest daily OHLCV market data for screened equities.
- FR-2: Compute EMA9, EMA21, EMA50, EMA200, ATR14, RSI, ADX, relative volume, and breakout levels.
- FR-3: Apply MVP liquidity gates, momentum gates, and MQS ranking to select candidates.
- FR-4: Produce 4-5 final recommendations daily when at least 4 candidates pass validation gates.
- FR-5: Output entry zone, stop-loss, profit target, risk amount, and risk/reward ratio for each recommendation.
- FR-6: Generate concise deterministic explanation text for each recommendation.
- FR-7: Calculate stop-loss as `entry - (2 x ATR14)` unless a documented strategy override exists.
- FR-8: Calculate first target as `entry + (3 x ATR14)` unless a documented strategy override exists.
- FR-9: Provide recommended maximum risk per trade as a percentage of account balance when supplied.
- FR-10: Annotate invalidation criteria for each setup.
- FR-11: Support a configurable baseline universe of symbols.
- FR-12: Track indicator values, score components, gate results, and data freshness for each candidate.
- FR-13: Store recommendation history and outcome status for analysis.
- FR-14: Expose the logic summary used for each selected recommendation.
- FR-15: Present recommendation cards with ticker, setup type, score, entry, stop, target, risk/reward, invalidation, and rationale.
- FR-16: Clearly label entry, stop, target, risk, and invalidation values.
- FR-17: Display trend strength and sentiment using defined labels and unavailable states.
- FR-18: Indicate when a recommendation is no longer valid due to failed conditions.
- FR-19: Expose retrieval for today's recommendations, recommendation details, recommendation history, and data freshness status.
- FR-20: Block recommendation publishing when required market data fails freshness or completeness checks.

### Non-Functional Requirements

- NFR-1: Daily recommendation generation must complete by 8:00 AM US Eastern time on trading days.
- NFR-2: Today's recommendation retrieval must respond under 500ms p95 under normal MVP load.
- NFR-3: Dashboard recommendation cards must render within 2 seconds p95 after API response.
- NFR-4: Freshness checks must detect missing OHLCV fields, stale trading dates, and incomplete symbol coverage.
- NFR-5: Pipeline failures must log failed source, failure reason, timestamp, and affected recommendation run.
- NFR-6: Data freshness or pipeline failure alerts must be available to the operator within 15 minutes.
- NFR-7: Indicator thresholds, liquidity gates, momentum gates, and scoring weights must be configurable without changing presentation code.
- NFR-8: Ingestion, signal computation, recommendation generation, API serving, and dashboard presentation must remain separately testable.
- NFR-9: User-specific preferences, watchlists, and account-balance inputs must be protected by authenticated access when enabled.
- NFR-10: Published recommendation records, score inputs, rationale, and outcome status must be retained for at least 12 months.
- NFR-11: Dashboard must meet WCAG 2.1 AA contrast for recommendation cards and support keyboard navigation for core review flows.

### Architecture Requirements

- Use a lean modular monolith with a web dashboard, FastAPI backend, scheduled Python recommendation job, PostgreSQL database, and basic monitoring.
- Defer Redis, TimescaleDB, object storage, managed orchestration, and managed auth until scale-up triggers are met.
- Use deterministic calculations and deterministic rationale templates.
- Store formula/config versions, provider data context, score components, gate results, and recommendation outcome states.
- Use database-backed reads for today's recommendations first; add cache only if measured p95 latency exceeds target.
- Keep recommendation logic separate from API presentation and dashboard UI.

### UX Design Requirements

- UX-DR1: Daily 5 recommendations must be the first and primary dashboard view.
- UX-DR2: Recommendation cards or rows must clearly separate setup, score, entry, stop, target, risk/reward, rationale, status, and invalidation.
- UX-DR3: Recommendation detail must open without losing dashboard context, preferably as a sliding panel.
- UX-DR4: Risk, stop-loss, target, stale-data state, and invalidation must be visually prominent.
- UX-DR5: Interface must remain calm, simple, desktop-first, and non-terminal-like.
- UX-DR6: Recent history must support review of prior recommendations, outcomes, stale warnings, and invalidations.
- UX-DR7: Dashboard must avoid unexplained abbreviations and support beginner learning through clear labels.
- UX-DR8: Core dashboard review must support keyboard navigation and mobile-safe layout at 390px width.
- UX-DR9: Educational/non-advisory posture must be visible in appropriate dashboard and detail contexts.

## MVP Epic List

1. Epic 1: MVP Foundation and Local Development
2. Epic 2: Market Data Ingestion and Freshness
3. Epic 3: Indicator Computation
4. Epic 4: Filtering, Scoring, and Candidate Ranking
5. Epic 5: Recommendation Engine and Explanation Layer
6. Epic 6: Recommendation API
7. Epic 7: Daily 5 Dashboard UX
8. Epic 8: Outcome Tracking and MVP Operations

## Epic 1: MVP Foundation and Local Development

Goal: Establish the project structure, local runtime, database migrations, and test foundation needed for the MVP.

### Story 1.1: Repository Structure

As a developer, I want a clear MVP project structure, so that frontend, API, scheduled job, and infrastructure work are easy to implement and test.

**Acceptance Criteria:**

- Given the repository is initialized, when a developer inspects the project, then `apps/web`, `apps/api`, `services/pipeline`, and `infra` exist.
- Given the MVP architecture, when backend code is added, then API entrypoints and recommendation-domain logic are separated into clear modules.
- Given future scale plans, when deferred infrastructure is documented, then Redis, TimescaleDB, object storage, managed orchestration, and managed auth are listed as backlog/scale items rather than MVP dependencies.

### Story 1.2: FastAPI Skeleton

As a developer, I want a FastAPI backend skeleton, so that MVP APIs can be added behind a consistent application structure.

**Acceptance Criteria:**

- Given the API app starts locally, when `/health` is requested, then it returns a successful health response.
- Given the API app starts locally, when `/docs` is opened, then OpenAPI documentation is available.
- Given the app logs requests or failures, when an error occurs, then structured logs include timestamp, route, and error context.

### Story 1.3: Next.js Dashboard Skeleton

As a developer, I want a Next.js dashboard skeleton, so that the Daily 5 interface can be built on a modern UI foundation.

**Acceptance Criteria:**

- Given the web app starts locally, when the dashboard route is opened, then a placeholder Daily 5 dashboard loads.
- Given Tailwind and shadcn/ui are initialized, when basic UI components are used, then styling is consistent and accessible.
- Given desktop-first UX, when viewed on a desktop viewport, then the primary content area supports recommendation card or row layout.

### Story 1.4: PostgreSQL and Migrations

As a developer, I want PostgreSQL and migrations configured locally, so that data models evolve safely during MVP implementation.

**Acceptance Criteria:**

- Given local development starts, when Docker Compose runs, then PostgreSQL is available to the API and pipeline.
- Given a migration command runs, when migrations are applied, then base schema tables are created.
- Given the schema changes, when CI runs, then migration validation is included in build checks.

### Story 1.5: MVP Test Harness

As a developer, I want a basic test harness, so that deterministic trading logic can be verified from the start.

**Acceptance Criteria:**

- Given backend tests run, then unit tests can execute for indicator, gate, score, risk, and explanation modules.
- Given frontend tests run, then recommendation card rendering can be validated.
- Given fixed fixture inputs, when deterministic logic tests run, then identical inputs produce identical outputs.

## Epic 2: Market Data Ingestion and Freshness

Goal: Load the MVP symbol universe, ingest daily market data and metadata, and block publishing when data is stale or incomplete.

### Story 2.1: Market Data Provider Interface

As a developer, I want a provider interface with a mock provider, so that ingestion can be tested without depending on live APIs.

**Acceptance Criteria:**

- Given the provider module, when a market data provider is implemented, then it exposes methods for OHLCV and symbol metadata retrieval.
- Given tests run, when the mock provider is used, then deterministic OHLCV and metadata fixtures are returned.
- Given provider errors occur, when ingestion handles them, then failures are captured with source and reason.

### Story 2.2: Configurable Symbol Universe

As an operator, I want a configurable baseline universe of symbols, so that the MVP scan target can be adjusted without code changes.

**Acceptance Criteria:**

- Given a universe configuration exists, when the pipeline runs, then configured symbols are loaded.
- Given inactive or malformed symbols exist, when validation runs, then invalid symbols are excluded or reported.
- Given the universe changes, when the next run starts, then the updated universe is used.

### Story 2.3: Daily OHLCV Ingestion

As the system, I want to ingest daily OHLCV data, so that indicators and recommendations use current market information.

**Acceptance Criteria:**

- Given a valid provider response, when ingestion runs, then daily OHLCV bars are normalized and persisted.
- Given existing bars are present, when ingestion reruns for the same symbol/date, then duplicate records are avoided.
- Given missing OHLCV fields, when validation runs, then the affected symbol/date is marked incomplete.

### Story 2.4: Symbol Metadata Ingestion

As the system, I want to ingest market cap, average volume, and price metadata, so that liquidity gates can be applied.

**Acceptance Criteria:**

- Given metadata is available, when ingestion runs, then market cap, average volume, and last close are persisted or updated.
- Given metadata is missing for a symbol, when freshness validation runs, then the missing metadata is reported.
- Given metadata is stale, when the run is evaluated, then stale data prevents publishing if it affects required gates.

### Story 2.5: Freshness and Completeness Gate

As an operator, I want publish blocking for stale or incomplete data, so that users never see recommendations based on invalid inputs.

**Acceptance Criteria:**

- Given OHLCV data is missing, stale, or incomplete, when the pipeline reaches publish readiness, then publishing is blocked.
- Given publishing is blocked, when the API exposes pipeline status, then stale/incomplete reasons are visible.
- Given a successful run, when freshness checks pass, then the run can proceed to indicator computation and recommendation generation.

## Epic 3: Indicator Computation

Goal: Compute and persist all MVP indicators required by the momentum gates, ranking, risk engine, and dashboard explanation.

### Story 3.1: EMA Computation

As the system, I want EMA9, EMA21, EMA50, and EMA200 calculated, so that trend, entry zone, and setup logic can run.

**Acceptance Criteria:**

- Given sufficient OHLCV history, when indicator computation runs, then EMA9, EMA21, EMA50, and EMA200 are calculated and persisted.
- Given insufficient lookback history, when computation runs, then the symbol is marked ineligible with a clear reason.
- Given fixed fixture bars, when tests run, then EMA outputs match expected values within tolerance.

### Story 3.2: ATR14 Computation

As the system, I want ATR14 calculated, so that stop-loss and target formulas can be generated.

**Acceptance Criteria:**

- Given sufficient OHLCV history, when indicator computation runs, then ATR14 is calculated and persisted.
- Given ATR14 is unavailable, when risk calculation runs, then the candidate is blocked with an explainable reason.
- Given fixed fixture bars, when tests run, then ATR14 output matches expected values within tolerance.

### Story 3.3: RSI and ADX Computation

As the system, I want RSI and ADX calculated, so that momentum gates can evaluate trend strength.

**Acceptance Criteria:**

- Given sufficient OHLCV history, when computation runs, then RSI and ADX are calculated and persisted.
- Given RSI or ADX is missing, when gates run, then the candidate fails eligibility with recorded reason.
- Given fixed fixtures, when tests run, then RSI and ADX outputs match expected values within tolerance.

### Story 3.4: Relative Volume and Breakout Levels

As the system, I want relative volume and breakout levels calculated, so that setup classification and rationale can use volume and breakout context.

**Acceptance Criteria:**

- Given volume history exists, when computation runs, then relative volume is calculated.
- Given breakout lookback data exists, when computation runs, then breakout reference levels are calculated.
- Given volume data is unavailable, when scoring runs, then the candidate receives a documented unavailable/fallback state.

## Epic 4: Filtering, Scoring, and Candidate Ranking

Goal: Apply liquidity gates, momentum gates, MQS/fallback scoring, and deterministic ranking to create a candidate set.

### Story 4.1: Liquidity Gates

As the system, I want liquidity gates applied, so that low-quality symbols are excluded before scoring.

**Acceptance Criteria:**

- Given symbol metadata exists, when liquidity gates run, then symbols must pass market cap greater than 2B, 90-day average daily volume greater than 1M, and last close greater than 10.
- Given a symbol fails a gate, when candidate scoring is reviewed, then the failed gate and value are recorded.
- Given thresholds change in configuration, when gates run again, then new thresholds are used without UI code changes.

### Story 4.2: Momentum Gates

As the system, I want momentum gates applied, so that candidates match the MVP strategy rules.

**Acceptance Criteria:**

- Given indicators exist, when gates run, then candidates must pass close above EMA50, EMA50 above EMA200, RSI between 60 and 75, ADX greater than 25, and relative volume greater than 2.0 when available.
- Given a candidate fails a momentum gate, when audit data is reviewed, then the failed gate and input values are stored.
- Given relative volume is unavailable, when fallback rules apply, then the behavior is documented in score components.

### Story 4.3: MQS and Fallback Score

As the system, I want MQS and fallback scoring, so that candidates can be ranked even when sentiment data is unavailable.

**Acceptance Criteria:**

- Given Put/Call ratio is available, when scoring runs, then MQS uses `(six_month_price_change / volatility) * (1 / put_call_ratio)`.
- Given Put/Call ratio is unavailable, when scoring runs, then fallback score uses configured price momentum, volatility, trend confirmation, and relative volume components.
- Given scoring completes, when candidate records are inspected, then formula version and score components are persisted.

### Story 4.4: Deterministic Ranking and Tie Handling

As the system, I want deterministic ranking, so that identical inputs always produce the same Daily 5 order.

**Acceptance Criteria:**

- Given scored candidates exist, when ranking runs, then candidates are ordered by score and documented tie-breakers.
- Given identical fixture inputs, when ranking runs multiple times, then output order is identical.
- Given fewer than four candidates pass, when publish readiness is checked, then the system publishes a no-recommendation/insufficient-candidates state instead of forcing output.

## Epic 5: Recommendation Engine and Explanation Layer

Goal: Generate complete, auditable Daily 5 recommendation records with entry, stop, target, risk, invalidation, and deterministic rationale.

### Story 5.1: Setup Classification

As the system, I want setup type classification, so that each recommendation has a clear trading context.

**Acceptance Criteria:**

- Given a ranked candidate, when classification runs, then setup type is assigned as breakout, continuation, or pullback.
- Given setup type is assigned, when rationale is generated, then the setup type appears in the explanation.
- Given classification cannot be determined, when recommendation generation runs, then the candidate is excluded or marked with a documented reason.

### Story 5.2: Entry Zone, Stop, Target, and Risk/Reward

As the system, I want risk plan values calculated, so that each recommendation includes an actionable educational trade plan.

**Acceptance Criteria:**

- Given EMA9 and EMA21 exist, when recommendation generation runs, then entry zone is calculated as the EMA21 to EMA9 range.
- Given ATR14 exists, when risk calculation runs, then stop is `entry - (2 x ATR14)` and first target is `entry + (3 x ATR14)`.
- Given entry, stop, and target exist, when risk/reward is calculated, then the ratio is persisted and exposed through the API.

### Story 5.3: Invalidation Rules

As a beginner trader, I want clear invalidation criteria, so that I know what would make a recommendation no longer valid.

**Acceptance Criteria:**

- Given a recommendation is generated, when invalidation rules are attached, then stop breach and trend failure conditions are included.
- Given a recommendation becomes invalid, when status is evaluated, then invalid state and reason are persisted.
- Given the dashboard displays a recommendation, then invalidation is visible on card or detail view.

### Story 5.4: Deterministic Explanation Templates

As a user, I want clear rationale for each recommendation, so that I can understand why the setup qualified without receiving personalized advice.

**Acceptance Criteria:**

- Given recommendation data exists, when rationale is generated, then the explanation uses deterministic templates and only supported facts.
- Given sentiment is unavailable, when rationale is generated, then sentiment is labeled unavailable rather than invented.
- Given financial safety requirements, when recommendation details are shown, then educational/non-advisory language is present in the appropriate context.

### Story 5.5: Publish Daily 5

As the system, I want to publish immutable recommendation records, so that the dashboard and history use auditable outputs.

**Acceptance Criteria:**

- Given at least four valid candidates pass, when publish runs, then 4-5 recommendations are stored as published for the trading day.
- Given recommendations are published, when records are inspected, then score inputs, gate results, formula/config versions, rationale, and freshness context are retained.
- Given a run is already published for a day, when the pipeline reruns, then duplicate publication is prevented or versioned explicitly.

## Epic 6: Recommendation API

Goal: Expose database-backed MVP endpoints for today's recommendations, details, history, and pipeline freshness status.

### Story 6.1: Today's Recommendations Endpoint

As a dashboard user, I want to retrieve today's recommendations, so that I can review the current Daily 5.

**Acceptance Criteria:**

- Given today's recommendations are published, when the endpoint is called, then it returns 4-5 recommendation summaries.
- Given no recommendations are available, when the endpoint is called, then it returns an explicit no-recommendation state and reason.
- Given data is stale or blocked, when the endpoint is called, then freshness status is included.

### Story 6.2: Recommendation Detail Endpoint

As a dashboard user, I want recommendation details, so that I can inspect triggers, risk plan, invalidation, and rationale.

**Acceptance Criteria:**

- Given a valid recommendation ID, when details are requested, then full recommendation data is returned.
- Given a recommendation includes gate and score context, when details are requested, then key logic summary is exposed.
- Given the recommendation does not exist, when details are requested, then a clear not-found response is returned.

### Story 6.3: Recommendation History Endpoint

As a learner, I want recommendation history, so that I can review recent outcomes and patterns.

**Acceptance Criteria:**

- Given historical recommendations exist, when history is requested, then paginated or bounded recent records are returned.
- Given outcome status exists, when history is returned, then outcome state is included.
- Given no history exists, when history is requested, then an empty state is returned cleanly.

### Story 6.4: Pipeline Status Endpoint

As an operator or dashboard user, I want pipeline freshness status, so that stale data or failures are transparent.

**Acceptance Criteria:**

- Given the latest pipeline run exists, when status is requested, then last successful refresh time, current state, and failure reason are returned.
- Given publish was blocked, when status is requested, then blocked reason is visible.
- Given no run has occurred, when status is requested, then an explicit not-run state is returned.

## Epic 7: Daily 5 Dashboard UX

Goal: Build the desktop-first MVP dashboard for reviewing today's recommendations, details, history, stale states, and educational risk context.

### Story 7.1: Daily 5 Dashboard View

As a beginner trader, I want the Daily 5 to be the primary dashboard view, so that I can immediately review today's curated ideas.

**Acceptance Criteria:**

- Given today's recommendations load, when the dashboard opens, then the Daily 5 are visible without requiring configuration.
- Given each recommendation appears, then ticker, setup type, score, entry, stop, target, risk/reward, invalidation, and short rationale are visible in card or row form.
- Given the viewport is desktop, then the layout supports easy comparison across recommendations.

### Story 7.2: Recommendation Detail Panel

As a beginner trader, I want a focused detail panel, so that I can inspect a recommendation without losing dashboard context.

**Acceptance Criteria:**

- Given a recommendation is selected, when the user opens details, then a sliding panel or equivalent focused view appears.
- Given details are visible, then setup, why now, trade plan, risk, invalidation, freshness, and rationale are shown in a predictable order.
- Given the panel is open, when keyboard navigation is used, then focus remains usable and dismissible.

### Story 7.3: Risk, Warning, and Stale States

As a user, I want risk and stale-data states to be prominent, so that I do not mistake warnings for valid setups.

**Acceptance Criteria:**

- Given a recommendation has warning or invalidation status, when displayed, then the state is visibly distinct.
- Given data is stale or publishing is blocked, when the dashboard loads, then the stale/blocked state is shown instead of stale recommendations.
- Given sentiment is unavailable, when displayed, then the sentiment label reads unavailable.

### Story 7.4: Recommendation History View

As a learner, I want to review recent recommendations and outcomes, so that I can learn from past setups.

**Acceptance Criteria:**

- Given historical recommendations exist, when the user opens history, then recent recommendations are listed with setup type, score, status, and outcome.
- Given outcomes include target hit, stop hit, invalidated, expired, or open, then those states are clearly labeled.
- Given no history exists, then an empty state explains that history will appear after recommendations are published.

### Story 7.5: Accessibility and Mobile-Safe Review

As a user, I want the dashboard to be readable and navigable, so that I can use it comfortably across common devices.

**Acceptance Criteria:**

- Given the dashboard uses recommendation cards, when viewed at 390px width, then cards do not require horizontal scrolling.
- Given keyboard navigation, when moving through cards and details, then core review flows are reachable.
- Given color states are used, then contrast targets meet WCAG 2.1 AA for recommendation cards and labels.

## Epic 8: Outcome Tracking and MVP Operations

Goal: Track recommendation outcomes and provide enough operational visibility to run the MVP reliably.

### Story 8.1: Recommendation Outcome Model

As the system, I want standardized outcome states, so that recommendations can be reviewed consistently.

**Acceptance Criteria:**

- Given a recommendation is published, then it starts with outcome state `OPEN`.
- Given status evaluation runs, then outcomes can become `TARGET_HIT`, `STOP_HIT`, `INVALIDATED`, or `EXPIRED`.
- Given an outcome changes, then timestamp and reason are persisted.

### Story 8.2: Daily Outcome Evaluation

As the system, I want to evaluate open recommendations daily, so that history reflects current outcomes.

**Acceptance Criteria:**

- Given open recommendations exist, when daily evaluation runs, then target, stop, and invalidation conditions are checked.
- Given an outcome condition is met, then the recommendation outcome is updated within one market day.
- Given insufficient data prevents evaluation, then the outcome remains open with a data issue note.

### Story 8.3: Pipeline Run Logging

As an operator, I want pipeline run logs persisted, so that failures and missed deadlines can be diagnosed.

**Acceptance Criteria:**

- Given a pipeline run starts, then run ID, start time, and run type are persisted.
- Given a pipeline run completes or fails, then completion status, end time, and failure reason are persisted.
- Given a run misses the 8:00 AM US Eastern deadline, then the miss is visible in pipeline status.

### Story 8.4: MVP Alerts

As an operator, I want basic alerts, so that stale data, failed jobs, and missed deadlines are noticed quickly.

**Acceptance Criteria:**

- Given freshness validation fails, then an alert is emitted or recorded within 15 minutes.
- Given the pipeline job fails, then the failed source and reason are included in alert context.
- Given the deadline is missed, then an operator-visible alert is available.

### Story 8.5: Production Runbook

As an operator, I want a short MVP runbook, so that common failures can be handled consistently.

**Acceptance Criteria:**

- Given stale data occurs, then the runbook explains how to inspect status and avoid publishing bad recommendations.
- Given provider failure occurs, then the runbook explains retry and fallback expectations.
- Given deployment or scheduled job failure occurs, then the runbook identifies logs, health checks, and recovery steps.

## MVP Coverage Map

| Requirement Area | Covered By |
|---|---|
| FR-1, FR-11, FR-20 | Epic 2 |
| FR-2 | Epic 3 |
| FR-3, FR-12 | Epic 4 |
| FR-4 to FR-10, FR-14, FR-18 | Epic 5 |
| FR-13, FR-19 | Epics 6 and 8 |
| FR-15 to FR-17 | Epic 7 |
| NFR-1, NFR-4 to NFR-6 | Epics 2 and 8 |
| NFR-2 | Epic 6 |
| NFR-3, NFR-11 | Epic 7 |
| NFR-7, NFR-8, NFR-10 | Epics 1, 4, 5, and 8 |
| NFR-9 | Epic 7 MVP boundary; backlog for managed auth |

## Backlog Epics

These epics are intentionally not MVP priorities. They should remain in the backlog until real users, data volume, operational pain, or product learning justifies them.

### Backlog Epic B1: Redis Read Cache

Trigger: p95 API reads for today's recommendations exceed 500ms under realistic traffic.

Stories:

- B1.1 Add Redis cache for today's recommendations and pipeline status.
- B1.2 Publish recommendations to Redis after database commit.
- B1.3 Add DB fallback when Redis is unavailable.
- B1.4 Add cache invalidation and monitoring.

### Backlog Epic B2: TimescaleDB and Time-Series Optimization

Trigger: OHLCV or indicator queries become slow, retention grows materially, or backtesting workloads need time-series optimization.

Stories:

- B2.1 Convert appropriate OHLCV/indicator tables to hypertables.
- B2.2 Add time-series indexes and retention policies.
- B2.3 Validate query performance against MVP PostgreSQL baseline.
- B2.4 Update migrations and operational documentation.

### Backlog Epic B3: Object Storage for Raw Snapshots and Reports

Trigger: raw provider snapshots, exports, or reports become too large or expensive to keep comfortably in PostgreSQL.

Stories:

- B3.1 Store raw provider snapshots in object storage.
- B3.2 Persist object references in audit records.
- B3.3 Add report/export artifact storage.
- B3.4 Add retention and access policy controls.

### Backlog Epic B4: Managed Workflow Orchestration

Trigger: scheduled jobs need backfills, retries, dependency visualization, or operator controls beyond simple scheduling.

Stories:

- B4.1 Introduce Prefect or equivalent workflow orchestration.
- B4.2 Split ingestion, validation, scoring, publishing, and outcome evaluation into tasks.
- B4.3 Add retry policy, backfill support, and operator UI.
- B4.4 Migrate run logging into orchestration-aware pipeline state.

### Backlog Epic B5: Managed Auth and User Personalization

Trigger: product supports real user accounts, watchlists, preferences, account-balance inputs, or role-based access.

Stories:

- B5.1 Add managed auth provider integration.
- B5.2 Add user profiles and private watchlists.
- B5.3 Add account-balance input protection.
- B5.4 Add role-based operator/admin access.

### Backlog Epic B6: Quality, Trust, and Validation Expansion

Trigger: MVP recommendation workflow is proven and users need stronger trust/learning features.

Stories:

- B6.1 Add required sentiment and options-flow filters.
- B6.2 Add multi-timeframe confirmation.
- B6.3 Add market regime detection.
- B6.4 Add slippage and transaction-cost modeling.
- B6.5 Add walk-forward validation reports.
- B6.6 Add historical analog explanations.

### Backlog Epic B7: Trading Readiness and Personalization

Trigger: product direction expands beyond educational recommendations toward paper trading or execution readiness.

Stories:

- B7.1 Add paper trading mode.
- B7.2 Add broker abstraction without live execution by default.
- B7.3 Add portfolio exposure controls.
- B7.4 Add intraday refresh and alerts.
- B7.5 Add deeper performance analytics and learning-loop intelligence.

## MVP Definition of Done

- Daily pipeline can ingest market data and generate a publishable Daily 5 when eligible candidates exist.
- Freshness validation blocks stale or incomplete runs.
- Recommendations include entry, stop, target, risk/reward, invalidation, and deterministic rationale.
- Recommendation records preserve inputs, gate results, score components, formula/config versions, and outcome state.
- API serves today's recommendations, details, history, and pipeline status.
- Dashboard presents Daily 5, detail review, stale states, history, and educational posture.
- Outcome tracking updates target, stop, invalidated, expired, and open states.
- Basic operational logs, status, alerts, and runbook exist.
