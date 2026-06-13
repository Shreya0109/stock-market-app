"""
SQLAlchemy database models for AlphaMomentum.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, UniqueConstraint
from datetime import UTC, datetime
from apps.api.database import Base


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Symbol(Base):
    """Tradable equity symbol."""

    __tablename__ = "symbols"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(255))
    market_cap = Column(Float, nullable=True)
    avg_volume_90d = Column(Float, nullable=True)
    last_close = Column(Float, nullable=True)
    metadata_updated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class DailyBar(Base):
    """OHLCV market data."""

    __tablename__ = "daily_bars"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now_naive)

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_daily_bars_symbol_date"),
    )


class IndicatorValue(Base):
    """Computed technical indicator values."""

    __tablename__ = "indicator_values"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    ema_5 = Column(Float, nullable=True)
    ema_9 = Column(Float, nullable=True)
    ema_21 = Column(Float, nullable=True)
    ema_50 = Column(Float, nullable=True)
    ema_200 = Column(Float, nullable=True)
    rsi = Column(Float, nullable=True)
    adx = Column(Float, nullable=True)
    atr_14 = Column(Float, nullable=True)
    relative_volume = Column(Float, nullable=True)
    breakout_high_20 = Column(Float, nullable=True)
    breakout_low_20 = Column(Float, nullable=True)
    ineligible_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_indicator_values_symbol_date"),
    )


class Recommendation(Base):
    """Daily recommendation."""

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), index=True, nullable=False)
    recommendation_date = Column(DateTime, index=True, nullable=False)
    setup_type = Column(String(50))  # breakout, continuation, pullback
    entry_low = Column(Float, nullable=False)
    entry_high = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target = Column(Float, nullable=False)
    mqs_score = Column(Float, nullable=False)
    put_call_ratio = Column(Float, nullable=True)
    rationale = Column(Text)
    status = Column(String(50), default="open")  # open, target_hit, stop_hit, invalidated, expired
    risk_reward = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class PipelineRun(Base):
    """Pipeline execution record."""

    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(50), unique=True, index=True, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    symbols_processed = Column(Integer, default=0)
    recommendations_count = Column(Integer, default=0)
    status = Column(String(50), default="running")  # running, success, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
