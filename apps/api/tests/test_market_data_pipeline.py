from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.models import Base, DailyBar
from services.pipeline import ingest_market_data, validate_data_freshness
from services.provider import MockMarketDataProvider, OHLCV


def make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def test_ingestion_persists_metadata_and_bars_idempotently():
    db = make_db()
    provider = MockMarketDataProvider()

    first = ingest_market_data(db, provider, symbols=["AAPL"], days=3)
    second = ingest_market_data(db, provider, symbols=["AAPL"], days=3)

    assert first.succeeded
    assert first.symbols_processed == 1
    assert first.bars_inserted == 3
    assert second.succeeded
    assert second.bars_inserted == 0
    assert second.bars_updated == 3
    assert db.query(DailyBar).filter(DailyBar.symbol == "AAPL").count() == 3


def test_freshness_blocks_missing_symbol_data():
    db = make_db()

    report = validate_data_freshness(db, symbols=["AAPL"])

    assert not report.publish_ready
    assert "AAPL: symbol metadata missing" in report.reasons


def test_freshness_passes_after_complete_ingestion():
    db = make_db()
    provider = MockMarketDataProvider()

    ingest_market_data(db, provider, symbols=["AAPL"], days=3)
    report = validate_data_freshness(db, symbols=["AAPL"])

    assert report.publish_ready
    assert report.reasons == []


def test_freshness_blocks_stale_ohlcv_data():
    db = make_db()
    stale_provider = MockMarketDataProvider()

    def stale_bars(symbol: str, days: int = 252):
        stale_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=20)
        return [
            OHLCV(
                symbol=symbol,
                date=stale_date,
                open=100.0,
                high=102.0,
                low=99.0,
                close=101.0,
                volume=2_000_000,
            )
        ]

    stale_provider.get_historical_bars = stale_bars
    ingest_market_data(db, stale_provider, symbols=["AAPL"], days=1)

    report = validate_data_freshness(db, symbols=["AAPL"], max_stale_days=5)

    assert not report.publish_ready
    assert any(reason.startswith("AAPL: OHLCV data stale") for reason in report.reasons)
