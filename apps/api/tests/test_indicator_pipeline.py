from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.models import Base, DailyBar, IndicatorValue
from services.pipeline import compute_and_persist_indicators
from services.indicators import calculate_atr

TOLERANCE = 1e-9


def make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def seed_bars(db, symbol="AAPL", count=220):
    start = datetime(2025, 1, 1)
    for offset in range(count):
        base = 100.0 + (offset * 0.5)
        db.add(
            DailyBar(
                symbol=symbol,
                date=start + timedelta(days=offset),
                open=base,
                high=base + 2.0,
                low=base - 1.0,
                close=base + 1.0,
                volume=1_000_000 + (offset * 10_000),
            )
        )
    db.commit()


def test_indicator_computation_persists_expected_values_idempotently():
    db = make_db()
    seed_bars(db)

    first = compute_and_persist_indicators(db, symbols=["AAPL"])
    second = compute_and_persist_indicators(db, symbols=["AAPL"])

    assert first.succeeded
    assert first.symbols_processed == 1
    assert first.rows_inserted == 220
    assert second.succeeded
    assert second.rows_inserted == 0
    assert second.rows_updated == 220

    latest = db.query(IndicatorValue).filter(IndicatorValue.symbol == "AAPL").order_by(IndicatorValue.date.desc()).first()
    assert latest.ema_9 is not None
    assert latest.ema_21 is not None
    assert latest.ema_50 is not None
    assert latest.ema_200 is not None
    assert latest.atr_14 is not None
    assert latest.rsi is not None
    assert latest.adx is not None
    assert latest.relative_volume is not None
    assert latest.breakout_high_20 is not None
    assert latest.breakout_low_20 is not None
    assert latest.ineligible_reason is None


def test_indicator_computation_marks_insufficient_history_ineligible():
    db = make_db()
    seed_bars(db, count=20)

    result = compute_and_persist_indicators(db, symbols=["AAPL"])

    assert not result.succeeded
    assert result.symbols_processed == 0
    assert "AAPL" in result.ineligible
    assert "insufficient OHLCV history" in result.ineligible["AAPL"]

    latest = db.query(IndicatorValue).filter(IndicatorValue.symbol == "AAPL").one()
    assert latest.ineligible_reason == result.ineligible["AAPL"]
    assert latest.ema_200 is None


def test_ema_and_atr_values_are_persisted_from_deterministic_bars():
    """Expected values use pandas' adjust=False EMA and 14-bar simple ATR conventions."""
    db = make_db()
    seed_bars(db, count=220)

    result = compute_and_persist_indicators(db, symbols=["AAPL"])
    latest = db.query(IndicatorValue).filter(IndicatorValue.symbol == "AAPL").order_by(IndicatorValue.date.desc()).first()

    assert result.succeeded
    assert latest.ema_9 == pytest.approx(208.50000000000006, abs=TOLERANCE)
    assert latest.ema_21 == pytest.approx(205.50000000430495, abs=TOLERANCE)
    assert latest.ema_50 == pytest.approx(198.2519195925225, abs=TOLERANCE)
    assert latest.ema_200 == pytest.approx(166.3177566297026, abs=TOLERANCE)
    assert latest.atr_14 == pytest.approx(3.0, abs=TOLERANCE)


def test_atr_uses_previous_close_gaps_in_true_range():
    high = pytest.importorskip("pandas").Series([10.0, 15.0, 12.0])
    low = pytest.importorskip("pandas").Series([8.0, 14.0, 7.0])
    close = pytest.importorskip("pandas").Series([9.0, 14.5, 8.0])

    # True ranges are 2.0, 6.0 (high-to-previous-close gap), and 7.5
    # (low-to-previous-close gap), not merely high minus low.
    atr = calculate_atr(high, low, close, period=3)

    assert atr.iloc[-1] == pytest.approx((2.0 + 6.0 + 7.5) / 3.0, abs=TOLERANCE)


def test_insufficient_ema_or_atr_history_does_not_stop_other_symbols():
    db = make_db()
    seed_bars(db, symbol="AAPL", count=220)
    seed_bars(db, symbol="MSFT", count=10)

    result = compute_and_persist_indicators(db, symbols=["AAPL", "MSFT"])
    valid = db.query(IndicatorValue).filter(IndicatorValue.symbol == "AAPL").order_by(IndicatorValue.date.desc()).first()
    invalid = db.query(IndicatorValue).filter(IndicatorValue.symbol == "MSFT").one()

    assert result.symbols_processed == 1
    assert valid.ema_200 is not None
    assert valid.atr_14 is not None
    assert "EMA200" in result.ineligible["MSFT"]
    assert "ATR14" in result.ineligible["MSFT"]
    assert invalid.ema_200 is None
    assert invalid.atr_14 is None
    assert invalid.ineligible_reason == result.ineligible["MSFT"]


def test_invalid_ohlcv_for_one_symbol_does_not_stop_ema_or_atr_processing():
    db = make_db()
    seed_bars(db, symbol="AAPL", count=220)
    seed_bars(db, symbol="MSFT", count=220)
    invalid_bar = db.query(DailyBar).filter(DailyBar.symbol == "MSFT").first()
    invalid_bar.close = float("inf")
    db.commit()

    result = compute_and_persist_indicators(db, symbols=["AAPL", "MSFT"])
    valid = db.query(IndicatorValue).filter(IndicatorValue.symbol == "AAPL").order_by(IndicatorValue.date.desc()).first()
    invalid = db.query(IndicatorValue).filter(IndicatorValue.symbol == "MSFT").one()

    assert result.symbols_processed == 1
    assert valid.ema_200 is not None
    assert valid.atr_14 is not None
    assert "EMA/ATR unavailable: invalid OHLCV fields close" in result.ineligible["MSFT"]
    assert invalid.ema_200 is None
    assert invalid.atr_14 is None
