from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.models import Base, DailyBar, IndicatorValue
from services.pipeline import compute_and_persist_indicators


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
