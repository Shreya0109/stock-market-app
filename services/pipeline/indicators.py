"""Indicator computation and persistence pipeline."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

import pandas as pd
from sqlalchemy.orm import Session

from apps.api.app.models import DailyBar, IndicatorValue
from services.indicators import (
    calculate_adx,
    calculate_atr,
    calculate_breakout_high,
    calculate_breakout_low,
    calculate_ema,
    calculate_relative_volume,
    calculate_rsi,
)
from services.pipeline.market_data import load_symbol_universe

EMA_PERIODS = (9, 21, 50, 200)
ATR_PERIOD = 14
RSI_PERIOD = 14
ADX_PERIOD = 14
RVOL_PERIOD = 20
BREAKOUT_PERIOD = 20
MIN_REQUIRED_BARS = max(max(EMA_PERIODS), ATR_PERIOD, RSI_PERIOD, ADX_PERIOD * 2 - 1, RVOL_PERIOD, BREAKOUT_PERIOD + 1)


@dataclass
class IndicatorComputationResult:
    """Summary of one indicator computation run."""

    symbols_requested: int = 0
    symbols_processed: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    ineligible: dict[str, str] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return not self.ineligible


def compute_and_persist_indicators(
    db: Session,
    symbols: Iterable[str] | None = None,
) -> IndicatorComputationResult:
    """Compute MVP indicators from persisted daily bars and upsert indicator rows."""
    active_symbols = list(symbols) if symbols is not None else load_symbol_universe()
    result = IndicatorComputationResult(symbols_requested=len(active_symbols))

    for symbol in active_symbols:
        normalized_symbol = symbol.upper()
        bars = _load_bars(db, normalized_symbol)
        if len(bars) < MIN_REQUIRED_BARS:
            result.ineligible[normalized_symbol] = (
                f"insufficient OHLCV history: {len(bars)} bars available, {MIN_REQUIRED_BARS} required"
            )
            _mark_latest_ineligible(db, normalized_symbol, bars, result.ineligible[normalized_symbol], result)
            continue

        frame = _bars_to_frame(bars)
        indicator_frame = _compute_indicator_frame(frame)
        latest_valid = indicator_frame.dropna(subset=["ema_200", "atr_14", "rsi", "adx", "relative_volume"])
        if latest_valid.empty:
            result.ineligible[normalized_symbol] = "indicator computation produced no complete rows"
            _mark_latest_ineligible(db, normalized_symbol, bars, result.ineligible[normalized_symbol], result)
            continue

        for row in indicator_frame.itertuples(index=False):
            inserted = _upsert_indicator_value(db, normalized_symbol, row)
            if inserted:
                result.rows_inserted += 1
            else:
                result.rows_updated += 1
        result.symbols_processed += 1

    db.commit()
    return result


def _load_bars(db: Session, symbol: str) -> list[DailyBar]:
    return (
        db.query(DailyBar)
        .filter(DailyBar.symbol == symbol)
        .order_by(DailyBar.date.asc())
        .all()
    )


def _bars_to_frame(bars: list[DailyBar]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bars
        ]
    )


def _compute_indicator_frame(frame: pd.DataFrame) -> pd.DataFrame:
    close = frame["close"]
    high = frame["high"]
    low = frame["low"]
    volume = frame["volume"]

    computed = frame[["date"]].copy()
    computed["ema_9"] = calculate_ema(close, 9)
    computed["ema_21"] = calculate_ema(close, 21)
    computed["ema_50"] = calculate_ema(close, 50)
    computed["ema_200"] = calculate_ema(close, 200)
    computed["atr_14"] = calculate_atr(high, low, close, ATR_PERIOD)
    computed["rsi"] = calculate_rsi(close, RSI_PERIOD)
    computed["adx"] = calculate_adx(high, low, close, ADX_PERIOD)
    computed["relative_volume"] = calculate_relative_volume(volume, RVOL_PERIOD)
    computed["breakout_high_20"] = calculate_breakout_high(high, BREAKOUT_PERIOD)
    computed["breakout_low_20"] = calculate_breakout_low(low, BREAKOUT_PERIOD)
    return computed


def _mark_latest_ineligible(
    db: Session,
    symbol: str,
    bars: list[DailyBar],
    reason: str,
    result: IndicatorComputationResult,
) -> None:
    if not bars:
        return
    latest = bars[-1]
    inserted = _upsert_indicator_value(
        db,
        symbol,
        _IndicatorRow(date=latest.date, ineligible_reason=reason),
    )
    if inserted:
        result.rows_inserted += 1
    else:
        result.rows_updated += 1


@dataclass
class _IndicatorRow:
    date: datetime
    ema_9: float | None = None
    ema_21: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None
    atr_14: float | None = None
    rsi: float | None = None
    adx: float | None = None
    relative_volume: float | None = None
    breakout_high_20: float | None = None
    breakout_low_20: float | None = None
    ineligible_reason: str | None = None


def _upsert_indicator_value(db: Session, symbol: str, row: object) -> bool:
    existing = db.query(IndicatorValue).filter(IndicatorValue.symbol == symbol, IndicatorValue.date == row.date).first()
    if existing is None:
        existing = IndicatorValue(symbol=symbol, date=row.date)
        db.add(existing)
        inserted = True
    else:
        inserted = False

    existing.ema_9 = _clean_number(getattr(row, "ema_9", None))
    existing.ema_21 = _clean_number(getattr(row, "ema_21", None))
    existing.ema_50 = _clean_number(getattr(row, "ema_50", None))
    existing.ema_200 = _clean_number(getattr(row, "ema_200", None))
    existing.atr_14 = _clean_number(getattr(row, "atr_14", None))
    existing.rsi = _clean_number(getattr(row, "rsi", None))
    existing.adx = _clean_number(getattr(row, "adx", None))
    existing.relative_volume = _clean_number(getattr(row, "relative_volume", None))
    existing.breakout_high_20 = _clean_number(getattr(row, "breakout_high_20", None))
    existing.breakout_low_20 = _clean_number(getattr(row, "breakout_low_20", None))
    existing.ineligible_reason = getattr(row, "ineligible_reason", None)
    return inserted


def _clean_number(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number
