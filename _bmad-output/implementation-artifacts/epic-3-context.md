# Epic 3 Context: Indicator Computation

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Create a deterministic, persisted technical-indicator layer from normalized daily OHLCV data. It supplies the inputs needed by later momentum gates, ranking, risk calculations, setup explanation, and dashboard display, while retaining enough provenance to explain unavailable or ineligible results. Indicator work must be independently testable and must not depend on market-data API calls or presentation code.

## Stories

- Story 3.1: EMA Computation
- Story 3.2: ATR14 Computation
- Story 3.3: RSI and ADX Computation
- Story 3.4: Relative Volume and Breakout Levels

## Requirements & Constraints

Compute EMA9, EMA21, EMA50, EMA200, ATR14, RSI, ADX, relative volume, and breakout reference levels for each symbol and calculation date using persisted daily bars. Persist computed outputs so later consumers read indicator data rather than recomputing on API requests.

Calculations must be deterministic: identical market inputs and configuration versions produce identical outputs. Use fixed input fixtures and expected numeric values with an appropriate tolerance in unit tests. The indicator layer must remain separate from ingestion, downstream scoring, recommendation generation, API serving, and dashboard rendering.

Insufficient lookback must be represented as an eligibility failure with a clear reason, rather than as an exception or silently invented value. Missing RSI, ADX, or ATR must leave a later gate or risk calculation able to block the candidate with an explainable reason. Missing volume must produce a documented unavailable/fallback state. The pipeline must preserve auditability for indicator inputs and configuration/formula choices, and operational failures should retain useful context for diagnosis.

Strategy thresholds and formulas need to remain configuration-driven, without coupling to presentation code. This epic only establishes calculations and persisted availability; it does not apply liquidity or momentum gates, score/rank candidates, classify setups, generate entry/stop/target values, publish recommendations, or alter the dashboard/API.

The daily pipeline has an operational publication target of completion by 8:00 AM US Eastern on trading days, so indicator computation should remain suitable for a scheduled batch workflow. Pipeline failures need source, reason, timestamp, and affected run context available to an operator. Data and calculation outcomes are part of the audit trail retained for later recommendation review; the broader system retains published recommendation records and their supporting inputs for at least 12 months.

## Technical Decisions

The indicator job consumes normalized `daily_bars`, whose required fields include symbol, trading date, open, high, low, close, volume, provider provenance, and ingestion timestamp. Persist the resulting values by symbol and date in `indicator_values` or an equivalent existing indicator persistence model. The indicator data must be available to later pipeline stages and should carry a calculation version so formula changes are auditable.

No external market-data request is part of this step. Implementations may use deterministic internal pandas/numpy-style calculations or a maintained, testable technical-analysis library. Preserve the modular-monolith separation: the scheduled Python job performs data processing, SQLAlchemy-backed persistence is the system of record, and FastAPI/UI layers consume persisted data only.

Use formula and configuration versions where the persistence architecture supports them. This gives later audits a way to distinguish values generated under changed periods, thresholds, or formulas. Provider context for the underlying data belongs in the broader provenance trail. Keep calculation behavior pure where feasible, with configuration and ordered historical bars as explicit inputs, so reruns and tests do not rely on current time, hidden mutable state, or network state.

The pipeline flow is normalized market data, freshness/completeness validation, indicator calculation, then later gates and ranking. Freshness validation remains a prerequisite: it detects missing required OHLCV fields, stale trading dates, and incomplete coverage before publication proceeds. Indicator failures associated with a particular symbol should be recorded without unnecessarily preventing valid symbols from continuing through calculation.

## Cross-Story Dependencies

All stories depend on Epic 2 having persisted, fresh, complete daily OHLCV history, including enough history to support EMA200 and other lookbacks. Stories 3.1 through 3.4 share the same per-symbol/date persistence and unavailable/ineligible reporting approach. Epic 4 consumes EMA50, EMA200, RSI, ADX, and relative volume for momentum gates; its intended rules include price above EMA50, EMA50 above EMA200, RSI from 60 to 75, ADX above 25, and relative volume above 2.0 when available. Epic 5 consumes EMA9 and EMA21 for an entry zone and ATR14 for later risk calculations. Breakout and volume context later contribute to setup classification and deterministic rationale.

Relative-volume unavailable handling is a direct dependency for Epic 4's fallback behavior and eventual score-component documentation. Indicator availability and reasons must therefore remain accessible across the pipeline boundary, rather than being reduced to an opaque failure. The current MVP deliberately defers cache, time-series optimization, managed workflow orchestration, and external provider choices for indicator computation; those are not prerequisites for this epic.
