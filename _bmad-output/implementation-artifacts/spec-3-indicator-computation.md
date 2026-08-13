---
title: 'Epic 3 Indicator Computation'
type: 'feature'
created: '2026-08-12'
status: 'draft'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The application has an initial indicator pipeline, but it does not fully document/configure its lookbacks or reliably distinguish insufficient, invalid, and unavailable source data. Its results also lack deterministic numerical fixture tests for all required MVP indicators.

**Approach:** Harden the existing pure indicator helpers and `indicator_values` upsert pipeline so persisted daily bars yield deterministic EMA9/21/50/200, ATR14, RSI14, ADX14, relative volume, and breakout reference levels, with clear per-symbol availability outcomes and exhaustive fixed-fixture coverage.

## Boundaries & Constraints

**Always:** Read OHLCV only from `daily_bars`; retain the current `indicator_values` table and idempotent symbol/date upsert; keep all calculation paths deterministic and independent of API presentation or provider calls; use explicit configuration constants for all required periods; record a symbol and indicator-specific reason when data cannot support a required calculation; allow another symbol to complete even if one fails; use documented floating-point tolerances in tests.

**Ask First:** Add a new persistence table, change the existing market-data ingestion validation contract, change gate/scoring/recommendation behavior, or choose a different technical-analysis formula/library than the existing pandas implementation.

**Never:** Implement Epic 4 gates, scoring/ranking, setups, risk levels, recommendations, APIs, or dashboard work; fabricate missing volume/indicator values; use live Yahoo data in tests; overwrite the user-owned database or flow-document modifications.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Complete history | Ordered, valid persisted OHLCV with at least the longest required lookback | Values for every requested indicator are persisted by symbol/date, and the latest record has no ineligibility reason | N/A |
| Short history | A symbol has fewer bars than its longest required calculation | Existing/latest indicator row is persisted with null unavailable fields and a clear `SYMBOL: insufficient history for EMA200`-style reason | Continue calculating other symbols |
| Invalid OHLC | Missing/non-finite/inconsistent price data in a symbol's rows | No invalid numeric indicator is persisted for that symbol/date | Persist an explainable symbol/indicator reason and continue |
| Volume unavailable | Volume is missing, non-finite, or no usable historical baseline exists | Relative volume is null; price-based indicators remain persisted where possible | Persist an explicit relative-volume unavailable reason recognizable by later stages |
| Mixed run | One valid symbol and one unusable symbol | Valid symbol's rows persist; failed symbol records its reason | Batch returns a summary instead of raising for the individual symbol |

</frozen-after-approval>

## Code Map

- `services/indicators.py` -- Existing pandas-based, pure technical indicator functions.
- `services/pipeline/indicators.py` -- Existing historical-bar loading, calculation orchestration, result reporting, and `IndicatorValue` upsert logic.
- `apps/api/config.py` -- Existing environment/config constants, appropriate home for explicit calculation lookbacks.
- `apps/api/app/models.py` -- Existing `DailyBar` source and `IndicatorValue` persistence schema.
- `apps/api/tests/test_indicator_pipeline.py` -- In-memory SQLite integration tests and deterministic OHLCV fixtures.
- `apps/api/tests/test_market_data_pipeline.py` -- Existing ingestion/freshness/pipeline conventions.

## Tasks & Acceptance

**Execution:**
- [ ] `apps/api/config.py` and `services/pipeline/indicators.py` -- Define and consume named EMA, ATR, RSI, ADX, relative-volume, and breakout periods, retaining defaults of 9/21/50/200, 14/14/14, 20, and 20 respectively, so calculation behavior is explicit and centrally configurable.
- [ ] `services/indicators.py` -- Validate numerical source series and make calculation minimum-history semantics explicit while preserving the current pandas formulas; make relative-volume calculation use the current day's volume against the preceding configured baseline (avoiding self-inclusion).
- [ ] `services/pipeline/indicators.py` -- Compute/upsert all indicators from ordered persisted bars; model availability independently enough that missing volume does not discard valid price indicators; persist clear indicator-aware ineligible/unavailable reasons and isolate unexpected per-symbol exceptions so a batch continues.
- [ ] `apps/api/app/models.py` and `apps/api/database.py` -- Only if necessary, add compatible fields/migrations for availability or calculation provenance using the existing `indicator_values` model, never a second table.
- [ ] `apps/api/tests/test_indicator_pipeline.py` -- Add fixed OHLCV fixtures and tolerance-documented assertions for EMA9/21/50/200, ATR14, RSI, ADX, relative volume, and breakout high/low; cover insufficient history, invalid/missing data, unavailable volume, idempotency, and mixed-symbol batch continuation.
- [ ] `apps/api/tests/test_market_data_pipeline.py` -- Add/adjust a deterministic integration test proving indicator computation is invoked after successful ingestion/freshness without introducing provider calls inside calculation.

**Acceptance Criteria:**
- Given fixed, valid daily bars, when the indicator job is rerun, then each persisted indicator value is numerically stable within the test's documented tolerance and the second run updates rather than duplicates records.
- Given 200 or more adequate historical bars, when the job runs, then EMA9, EMA21, EMA50, EMA200, ATR14, RSI, ADX, relative volume, and 20-bar prior high/low are available on the latest applicable record.
- Given insufficient data for a calculation, when the job runs, then it writes no zero/NaN/infinite substitute and records a clear reason naming the symbol and unavailable indicator.
- Given volume is unavailable while price data is valid, when the job runs, then relative volume is explicitly unavailable and price-derived values remain usable for later consumers.
- Given a batch with an invalid symbol and a valid symbol, when the job runs, then the valid symbol persists successfully and the result exposes the invalid symbol's reason.
- Given market-data freshness passes, when the existing pipeline runs, then it calls the indicator job against persisted bars only; no Epic 4 or Epic 5 behavior changes.

## Spec Change Log

## Design Notes

Use the project’s existing pandas formulas and table shape. The retention of daily rows provides auditability and lets the latest record be queried by later epics. Relative volume will use the previous 20 trading days as its baseline: `current_volume / mean(previous 20 volumes)`. This makes a real current-volume spike observable (unlike a window that includes the current bar) and requires 21 usable volume bars for its first value. Breakout high and low likewise remain the prior 20-day references.

The batch result may retain a symbol-level reason map, but reasons should state the affected indicator when that is knowable (for example, `AAPL: insufficient history for EMA200 (20 bars available, 200 required)` or `GOOG: relative volume unavailable: volume missing`). A missing relative-volume value alone is an unavailable state, not a reason to erase otherwise valid trend/risk indicators.

## Verification

**Commands:**

- `pytest -q apps/api/tests/test_indicator_pipeline.py` -- expected: all deterministic calculation and persistence cases pass.
- `pytest -q apps/api/tests` -- expected: complete backend suite passes with no regression in ingestion, health, or model tests.
