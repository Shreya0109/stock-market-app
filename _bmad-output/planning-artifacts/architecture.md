---
stepsCompleted:
  - 1
  - 2
inputDocuments:
  - 'stock-market-app/_bmad-output/planning-artifacts/prd.md'
  - 'stock-market-app/_bmad-output/planning-artifacts/ux-design-specification.md'
  - 'docs/alphamomentum_bmad_markdown_bundle.md'
workflowType: 'architecture'
project_name: 'Trade_analytics'
user_name: 'sameer'
date: '2026-05-23'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

AlphaMomentum Recommender is a hybrid web application, backend API, and data pipeline for producing a daily curated set of 4-5 educational equity momentum recommendations. Architecturally, the product requires separate but coordinated capabilities for market data ingestion, indicator computation, liquidity and momentum filtering, MQS/fallback scoring, risk calculation, recommendation generation, deterministic rationale generation, recommendation history, outcome tracking, API retrieval, and dashboard presentation.

The MVP is batch-oriented. Users consume published recommendations through a private dashboard and API rather than triggering ad hoc scans. The system must block recommendation publication when required market data is stale, missing, or incomplete.

**Non-Functional Requirements:**

The architecture is shaped most strongly by determinism, auditability, data freshness, low-latency reads, and financial safety. Daily generation must complete before the 8:00 AM US Eastern publication deadline. Cached retrieval must meet the 500ms p95 API target, and dashboard cards must render within 2 seconds after cached API response under normal MVP load.

Security and compliance requirements are meaningful even for the MVP: the product must remain educational and informational, preserve recommendation provenance, avoid broker execution, protect user-specific data when enabled, and retain published recommendation records and scoring context for at least 12 months.

**Scale & Complexity:**

- Primary domain: financial trading education, full-stack web app, API backend, and scheduled data pipeline.
- Complexity level: high for domain correctness and auditability, intentionally lean for MVP runtime infrastructure.
- Estimated MVP architectural components: frontend dashboard, backend API, scheduled pipeline job, PostgreSQL database, provider adapters, basic auth boundary, structured logs, and deadline/freshness alerts.
- Deferred scale components: Redis, TimescaleDB, object storage, managed workflow orchestration, and heavier observability should be added when real usage, data volume, or operational pain justifies them.

### Technical Constraints & Dependencies

- MVP universe focuses on liquid US equities.
- Required data includes OHLCV, symbol metadata, market cap, average volume, and optional Put/Call or sentiment data.
- Recommendation logic must remain configuration-driven so thresholds, weights, formulas, and fallback behavior can evolve without changing presentation code.
- The system needs deterministic output from the same market inputs and configuration versions.
- Normalized market data, score components, formula versions, rationale text, and outcome states must be retained for audit and review. Raw provider snapshots can begin as database JSON payloads or local/exported artifacts before moving to object storage.
- The dashboard is desktop-first but must support mobile-safe recommendation review at 390px width.
- Explanations should be template-based for testability, auditability, and financial safety.

### Cross-Cutting Concerns Identified

- Data freshness and publish blocking across ingestion, scoring, API, and UI.
- Auditability across provider snapshots, indicators, gates, scores, recommendations, and outcomes.
- Deterministic scoring and ranking, including tie handling and fallback scoring when sentiment data is unavailable.
- Configuration versioning for thresholds, formulas, and strategy overrides.
- Financial safety language and educational posture across dashboard, API payloads, and generated rationale.
- Lean observability for scheduled jobs, deadline misses, stale data, provider failures, API latency, and frontend errors, with deeper monitoring added after MVP usage patterns are known.
- Separation of concerns between ingestion, indicators, scoring, recommendation generation, explanation generation, API serving, and UI rendering.

## Architecture Blueprint

### Architecture Pattern

AlphaMomentum should use a Lean Modular Monolith + Scheduled Batch Job architecture for the MVP.

Runtime units:

- Web dashboard
- Backend API
- Scheduled recommendation job
- PostgreSQL database
- Basic monitoring and alerting

Deferred runtime units:

- Redis cache when database-backed reads no longer meet latency targets
- TimescaleDB when time-series volume or query performance requires it
- Object storage when raw provider snapshot retention outgrows database JSON/artifact storage
- Managed workflow orchestration when the pipeline needs retries, backfills, dependency graphs, or operator UI beyond a simple scheduled job

### Core Architectural Principles

- Deterministic recommendation outputs
- Auditability-first data model
- Batch-first recommendation generation
- Configuration-driven strategy logic
- Separation between ingestion, indicators, scoring, recommendations, API, and UI
- Template-based explanations for financial safety and reproducibility

### Primary Components

- Frontend: Next.js, React, TypeScript, Tailwind, shadcn/ui
- Backend API: Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- Scheduled Job: Python script or lightweight job runner using pandas/numpy and an indicator library
- Database: PostgreSQL as the MVP source of truth for symbols, market data, indicators, runs, recommendations, outcomes, and audit records
- Cache: database-backed "today" reads first; add Redis only if measured latency requires it
- Storage: database JSON/artifact records first; add object storage for large raw snapshots, exports, and reports after MVP validation
- Auth: simple private-access boundary for MVP; add managed auth when user-specific preferences, watchlists, or account-balance inputs are enabled
- Observability: structured logs, persisted pipeline runs, freshness/deadline alerts, and basic error tracking

### Data Flow

1. Scheduled job starts before the market-open publication deadline.
2. System loads symbol universe.
3. Market data provider adapters fetch OHLCV and metadata.
4. Freshness validation blocks stale or incomplete runs.
5. Raw provider snapshots are stored for provenance.
6. Normalized data is persisted.
7. Indicators are computed.
8. Liquidity and momentum gates are applied.
9. MQS or fallback score ranks candidates.
10. Daily 4-5 recommendations are generated.
11. Template-based rationale is produced.
12. Recommendation audit trail is persisted.
13. Today's recommendations are marked published in PostgreSQL.
14. API and dashboard serve today's published recommendations from indexed database reads.
15. Redis publication can be added later if observed API latency exceeds the MVP target.

### Core Domain Entities

- Symbol
- DailyBar
- IndicatorValue
- PipelineRun
- CandidateScore
- Recommendation
- RecommendationOutcome
- AuditEvent

### Key Decisions To Lock

- Use modular monolith for MVP.
- Use scheduled batch generation, not user-triggered scans.
- Use PostgreSQL as the MVP source of truth.
- Defer TimescaleDB until time-series query volume or retention needs justify it.
- Defer Redis until measured database-backed reads cannot meet the MVP latency target.
- Use deterministic templates for recommendation explanations.
- Preserve formula versions, config versions, provider snapshots, and score inputs for auditability.

### MVP Scale-Up Triggers

Add deferred infrastructure only when one of these signals appears:

- Add Redis when p95 API reads for today's recommendations exceed 500ms under realistic traffic.
- Add TimescaleDB when OHLCV/indicator queries become slow, retention grows materially, or backtesting workloads need time-series optimizations.
- Add object storage when raw provider snapshots, exports, or reports become too large or expensive to keep comfortably in PostgreSQL.
- Add managed workflow orchestration when the scheduled job needs backfills, dependency visualization, retry policies, or operator controls beyond basic cron/task scheduling.
- Add managed auth when the product supports real user accounts, watchlists, preferences, account-balance inputs, or role-based access.

### Implementation Plan Source

The architecture document can seed implementation planning by turning components into epics:

- Foundation
- Market data ingestion
- Indicator computation
- Filtering and scoring
- Recommendation engine
- Explanation layer
- API and cache
- Dashboard UI
- Outcome tracking
- Monitoring and launch
