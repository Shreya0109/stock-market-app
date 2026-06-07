---
title: Epic 2 	6 Market Data Ingestion and Freshness (One-Page Checklist)
date: 2026-06-07
project: Trade_analytics
---

# Epic 2 	6 Market Data Ingestion and Freshness (One-Page Checklist)

- Goal: Load the MVP symbol universe, ingest daily OHLCV and metadata, validate freshness/completeness, and block publishing when data is invalid.

- Core Deliverables: provider interface + mock, universe config, daily OHLCV ingestion, symbol metadata ingestion, freshness & completeness gate, pipeline status endpoint, alerts.

- Minimum Acceptance (MVP):
  - Provider exposes OHLCV and metadata methods and a deterministic mock fixture.
  - Config-driven symbol universe loads; invalid symbols are validated and reported.
  - Daily OHLCV normalized, persisted, deduplicated; missing fields flagged.
  - Metadata (market cap, avg volume, last close) persisted and validated.
  - Freshness/completeness gate blocks publishing; pipeline status surfaces reasons.

- Implementation Checklist:
  - Provider module
    - Define interface: `get_ohlcv(symbol, start, end)`, `get_metadata(symbol)`.
    - Add a deterministic mock provider + fixtures for tests.
  - Config
    - Add `symbols.yml`/`symbols.json` loader with validation and exclusion reporting.
  - Ingestion job
    - Scheduled runner that fetches, normalizes, validates, and persists OHLCV.
    - Idempotent writes (upsert or dedupe) to avoid duplicate bars.
  - Metadata ingestion
    - Upsert market cap, 90-day avg vol, last close; mark stale/missing.
  - Freshness checks
    - Required fields, date recency rules, and symbol coverage thresholds.
    - Run-level aggregate pass/fail and per-symbol reasons.
  - Publish gating
    - Block publish when run-level freshness fails; store & expose blocking reasons.
  - Persistence
    - Tables: `raw_bars`, `normalized_bars`, `symbol_metadata`, `pipeline_runs` (status, reasons, timestamps).
  - API / Status
    - Add `/pipeline/status` endpoint returning last run, state, blocked reasons, and data timestamps.
  - Alerts & logging
    - Emit operator alert (record/email/Slack) within 15 minutes on freshness failure.
    - Structured logs include provider source and failure reason.
  - Tests & fixtures
    - Unit tests for provider, normalization, dedupe, and freshness logic using the mock provider.

- Critical Config / Thresholds to Decide:
  - Symbol coverage threshold (%) required to proceed (e.g., 95%).
  - Allowed staleness window for OHLCV (e.g., latest trading date by EOD or same trading date as run).
  - Required metadata fields for publishing (market cap, avg vol, last close).

- Quick "Done" Criteria:
  - A pipeline run ingests the configured universe, persists bars & metadata, freshness checks pass, and `/pipeline/status` returns `OK`.
  - Unit tests for ingestion and freshness rules pass with mock fixtures.

- Suggested Next Steps:
  1. Create DB migration for `normalized_bars`, `symbol_metadata`, and `pipeline_runs`.
  2. Scaffold provider interface and mock provider in `services/pipeline`.
  3. Implement basic ingestion runner with idempotent writes and one end-to-end test.
