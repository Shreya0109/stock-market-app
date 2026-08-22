"""Daily market data ingestion and publish-readiness checks."""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence

from sqlalchemy.orm import Session

from apps.api.app.models import DailyBar, PipelineRun, Symbol
from apps.api.config import FRESHNESS_MAX_STALE_DAYS, SYMBOL_UNIVERSE_FILE
from services.provider import MarketDataProvider, OHLCV, ProviderError, SymbolMetadata

logger = logging.getLogger(__name__)

_SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


@dataclass
class IngestionFailure:
    """A source failure or validation failure for one symbol."""

    symbol: str
    source: str
    reason: str


@dataclass
class IngestionResult:
    """Summary of one market data ingestion attempt."""

    symbols_requested: int = 0
    symbols_processed: int = 0
    bars_inserted: int = 0
    bars_updated: int = 0
    metadata_updated: int = 0
    failures: list[IngestionFailure] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return not self.failures


@dataclass
class FreshnessReport:
    """Publish-readiness report for market data."""

    publish_ready: bool
    checked_at: datetime
    symbols_checked: int
    latest_required_date: date
    reasons: list[str] = field(default_factory=list)


def load_symbol_universe(path: str | Path = SYMBOL_UNIVERSE_FILE) -> list[str]:
    """Load and validate the configured symbol universe."""
    universe_path = Path(path)
    if not universe_path.exists():
        raise FileNotFoundError(f"Symbol universe file not found: {universe_path}")

    symbols: list[str] = []
    seen: set[str] = set()
    for line in universe_path.read_text(encoding="utf-8").splitlines():
        symbol = line.split("#", 1)[0].strip().upper()
        if not symbol:
            continue
        if not _SYMBOL_PATTERN.match(symbol):
            logger.warning("Ignoring malformed symbol in universe: %s", symbol)
            continue
        if symbol not in seen:
            symbols.append(symbol)
            seen.add(symbol)
    return symbols


def ingest_market_data(
    db: Session,
    provider: MarketDataProvider,
    symbols: Sequence[str] | None = None,
    days: int = 252,
) -> IngestionResult:
    """Fetch OHLCV and metadata, normalize them, and persist idempotently."""
    active_symbols = list(symbols) if symbols is not None else load_symbol_universe()
    result = IngestionResult(symbols_requested=len(active_symbols))

    for symbol in active_symbols:
        normalized_symbol = symbol.upper()
        try:
            metadata = provider.get_symbol_metadata(normalized_symbol)
            bars = provider.get_historical_bars(normalized_symbol, days=days)
            _validate_metadata(metadata)
            complete_bars = [_normalize_bar(bar) for bar in bars]
            if not complete_bars:
                raise ProviderError("provider returned no bars")

            _upsert_symbol(db, metadata)
            result.metadata_updated += 1
            for bar in complete_bars:
                inserted = _upsert_daily_bar(db, bar)
                if inserted:
                    result.bars_inserted += 1
                else:
                    result.bars_updated += 1
            result.symbols_processed += 1
        except Exception as exc:
            result.failures.append(
                IngestionFailure(
                    symbol=normalized_symbol,
                    source=getattr(provider, "source", provider.__class__.__name__),
                    reason=str(exc),
                )
            )
            logger.exception("Market data ingestion failed for %s", normalized_symbol)

    db.commit()
    return result


def validate_data_freshness(
    db: Session,
    symbols: Iterable[str] | None = None,
    max_stale_days: int = FRESHNESS_MAX_STALE_DAYS,
    checked_at: datetime | None = None,
) -> FreshnessReport:
    """Validate completeness and freshness before recommendations can publish."""
    now = checked_at or _utc_now_naive()
    latest_required_date = (now - timedelta(days=max_stale_days)).date()
    active_symbols = list(symbols) if symbols is not None else load_symbol_universe()
    reasons: list[str] = []

    for symbol in active_symbols:
        normalized_symbol = symbol.upper()
        db_symbol = db.query(Symbol).filter(Symbol.symbol == normalized_symbol, Symbol.is_active.is_(True)).first()
        if db_symbol is None:
            reasons.append(f"{normalized_symbol}: symbol metadata missing")
            continue
        if db_symbol.market_cap is None:
            reasons.append(f"{normalized_symbol}: market cap missing")
        if db_symbol.avg_volume_90d is None:
            reasons.append(f"{normalized_symbol}: 90-day average volume missing")
        if db_symbol.last_close is None:
            reasons.append(f"{normalized_symbol}: last close metadata missing")
        if db_symbol.metadata_updated_at is None or db_symbol.metadata_updated_at.date() < latest_required_date:
            reasons.append(f"{normalized_symbol}: metadata stale")

        latest_bar = (
            db.query(DailyBar)
            .filter(DailyBar.symbol == normalized_symbol)
            .order_by(DailyBar.date.desc())
            .first()
        )
        if latest_bar is None:
            reasons.append(f"{normalized_symbol}: OHLCV data missing")
            continue
        if latest_bar.date.date() < latest_required_date:
            reasons.append(f"{normalized_symbol}: OHLCV data stale at {latest_bar.date.date().isoformat()}")
        missing_fields = [
            field_name
            for field_name in ("open", "high", "low", "close", "volume")
            if getattr(latest_bar, field_name) is None
        ]
        if missing_fields:
            reasons.append(f"{normalized_symbol}: incomplete OHLCV fields {', '.join(missing_fields)}")

    return FreshnessReport(
        publish_ready=not reasons,
        checked_at=now,
        symbols_checked=len(active_symbols),
        latest_required_date=latest_required_date,
        reasons=reasons,
    )


def run_market_data_pipeline(
    db: Session,
    provider: MarketDataProvider,
    symbols: Sequence[str] | None = None,
    days: int = 252,
) -> PipelineRun:
    """Run Epic 2 ingestion and persist publish-readiness status."""
    run_id = uuid.uuid4().hex
    pipeline_run = PipelineRun(run_id=run_id, started_at=_utc_now_naive(), status="running")
    db.add(pipeline_run)
    db.commit()

    active_symbols = list(symbols) if symbols is not None else load_symbol_universe()
    try:
        ingestion = ingest_market_data(db, provider, symbols=active_symbols, days=days)
        freshness = validate_data_freshness(db, symbols=active_symbols)
        blocked_reasons = [failure.reason for failure in ingestion.failures] + freshness.reasons
        if not blocked_reasons:
            from services.pipeline.indicators import compute_and_persist_indicators

            indicators = compute_and_persist_indicators(db, symbols=active_symbols)
            blocked_reasons.extend(indicators.ineligible.values())
        pipeline_run.completed_at = _utc_now_naive()
        pipeline_run.symbols_processed = ingestion.symbols_processed
        pipeline_run.status = "success" if not blocked_reasons else "blocked"
        pipeline_run.error_message = None if not blocked_reasons else json.dumps(blocked_reasons)
        db.commit()
    except Exception as exc:
        pipeline_run.completed_at = _utc_now_naive()
        pipeline_run.status = "failed"
        pipeline_run.error_message = str(exc)
        db.commit()
        raise

    return pipeline_run


def _validate_metadata(metadata: SymbolMetadata) -> None:
    required_fields = {
        "market_cap": metadata.market_cap,
        "avg_volume_90d": metadata.avg_volume_90d,
        "last_close": metadata.last_close,
    }
    missing = [name for name, value in required_fields.items() if value is None]
    if missing:
        raise ProviderError(f"metadata missing required fields: {', '.join(missing)}")


def _normalize_bar(bar: OHLCV) -> OHLCV:
    values = {
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume,
    }
    missing = [name for name, value in values.items() if value is None]
    if missing:
        raise ProviderError(f"{bar.symbol}: OHLCV missing fields: {', '.join(missing)}")
    normalized_date = bar.date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    return OHLCV(symbol=bar.symbol.upper(), date=normalized_date, **values)


def _upsert_symbol(db: Session, metadata: SymbolMetadata) -> Symbol:
    db_symbol = db.query(Symbol).filter(Symbol.symbol == metadata.symbol.upper()).first()
    if db_symbol is None:
        db_symbol = Symbol(symbol=metadata.symbol.upper())
        db.add(db_symbol)
    db_symbol.name = metadata.name
    db_symbol.market_cap = metadata.market_cap
    db_symbol.avg_volume_90d = metadata.avg_volume_90d
    db_symbol.last_close = metadata.last_close
    db_symbol.metadata_updated_at = _utc_now_naive()
    db_symbol.is_active = True
    return db_symbol


def _upsert_daily_bar(db: Session, bar: OHLCV) -> bool:
    existing = db.query(DailyBar).filter(DailyBar.symbol == bar.symbol, DailyBar.date == bar.date).first()
    if existing is None:
        db.add(
            DailyBar(
                symbol=bar.symbol,
                date=bar.date,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
            )
        )
        return True

    existing.open = bar.open
    existing.high = bar.high
    existing.low = bar.low
    existing.close = bar.close
    existing.volume = bar.volume
    return False


def _utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
