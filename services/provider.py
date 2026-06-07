"""
Market data provider interface.

Abstraction for fetching market data from external sources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import pandas as pd


@dataclass
class OHLCV:
    """OHLCV bar data."""

    symbol: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class SymbolMetadata:
    """Symbol metadata."""

    symbol: str
    name: str
    market_cap: Optional[float] = None
    avg_volume_90d: Optional[float] = None
    last_close: Optional[float] = None


class ProviderError(RuntimeError):
    """Raised when a market data provider cannot return trusted data."""


class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_historical_bars(
        self,
        symbol: str,
        days: int = 252
    ) -> List[OHLCV]:
        """Fetch historical OHLCV bars."""
        pass

    @abstractmethod
    def get_symbol_metadata(self, symbol: str) -> SymbolMetadata:
        """Fetch symbol metadata."""
        pass

    @abstractmethod
    def get_symbols_list(self) -> List[str]:
        """Fetch list of tradable symbols."""
        pass


class MockMarketDataProvider(MarketDataProvider):
    """Mock provider for testing without API keys."""

    def get_historical_bars(self, symbol: str, days: int = 252) -> List[OHLCV]:
        """Return deterministic OHLCV data."""
        end = pd.Timestamp.now(tz="UTC").normalize()
        bars = []
        for offset in range(days):
            day = end - pd.Timedelta(days=days - offset - 1)
            base = 100 + offset
            bars.append(
                OHLCV(
                    symbol=symbol.upper(),
                    date=day.to_pydatetime().replace(tzinfo=None),
                    open=float(base),
                    high=float(base + 2),
                    low=float(base - 1),
                    close=float(base + 1),
                    volume=float(1_500_000 + offset),
                )
            )
        return bars

    def get_symbol_metadata(self, symbol: str) -> SymbolMetadata:
        """Return mock metadata."""
        return SymbolMetadata(
            symbol=symbol.upper(),
            name=f"{symbol} Inc",
            market_cap=5_000_000_000,
            avg_volume_90d=2_000_000,
            last_close=125.0,
        )

    def get_symbols_list(self) -> List[str]:
        """Return mock symbol list."""
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]


# Factory function to get provider
def get_provider(provider_type: str = "mock") -> MarketDataProvider:
    """Get market data provider by type."""
    provider_type = provider_type.lower()
    if provider_type == "mock":
        return MockMarketDataProvider()
    if provider_type in {"yahoo", "yfinance", "yahoo_finance"}:
        return YahooFinanceProvider()
    raise ValueError(f"Unknown provider type: {provider_type}")


class YahooFinanceProvider(MarketDataProvider):
    """Yahoo Finance provider backed by the yfinance package."""

    source = "yahoo_finance"

    def get_historical_bars(self, symbol: str, days: int = 252) -> List[OHLCV]:
        """Fetch daily OHLCV bars from Yahoo Finance."""
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ProviderError("yfinance is not installed") from exc

        ticker = yf.Ticker(symbol)
        try:
            history = ticker.history(period=f"{days}d", interval="1d", auto_adjust=False)
        except Exception as exc:
            raise ProviderError(f"Yahoo Finance history request failed for {symbol}: {exc}") from exc

        if history.empty:
            raise ProviderError(f"Yahoo Finance returned no OHLCV data for {symbol}")

        bars: List[OHLCV] = []
        for index, row in history.iterrows():
            try:
                values = {
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                }
            except (KeyError, TypeError, ValueError) as exc:
                raise ProviderError(f"Yahoo Finance returned malformed OHLCV data for {symbol}") from exc

            if pd.isna(list(values.values())).any():
                raise ProviderError(f"Yahoo Finance returned missing OHLCV fields for {symbol}")

            timestamp = pd.Timestamp(index).to_pydatetime().replace(tzinfo=None)
            bars.append(OHLCV(symbol=symbol.upper(), date=timestamp, **values))

        return bars

    def get_symbol_metadata(self, symbol: str) -> SymbolMetadata:
        """Fetch required symbol metadata from Yahoo Finance."""
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ProviderError("yfinance is not installed") from exc

        ticker = yf.Ticker(symbol)
        try:
            fast_info = getattr(ticker, "fast_info", {}) or {}
            info = ticker.info or {}
        except Exception as exc:
            raise ProviderError(f"Yahoo Finance metadata request failed for {symbol}: {exc}") from exc

        name = info.get("shortName") or info.get("longName") or symbol.upper()
        market_cap = _first_number(
            _get_mapping_value(fast_info, "market_cap"),
            info.get("marketCap"),
        )
        avg_volume_90d = _first_number(
            info.get("threeMonthAverageVolume"),
            info.get("averageVolume"),
            _get_mapping_value(fast_info, "three_month_average_volume"),
        )
        last_close = _first_number(
            _get_mapping_value(fast_info, "last_price"),
            _get_mapping_value(fast_info, "lastPrice"),
            info.get("currentPrice"),
            info.get("regularMarketPreviousClose"),
        )

        return SymbolMetadata(
            symbol=symbol.upper(),
            name=name,
            market_cap=market_cap,
            avg_volume_90d=avg_volume_90d,
            last_close=last_close,
        )

    def get_symbols_list(self) -> List[str]:
        """Yahoo Finance does not provide a default universe endpoint."""
        raise ProviderError("Yahoo Finance provider requires a configured symbol universe")


def _first_number(*values) -> Optional[float]:
    for value in values:
        if value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if pd.notna(number):
            return number
    return None


def _get_mapping_value(mapping, key):
    try:
        return mapping.get(key)
    except AttributeError:
        try:
            return mapping[key]
        except (KeyError, TypeError):
            return None
