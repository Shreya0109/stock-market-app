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
        """Return mock OHLCV data."""
        # Placeholder: return empty list for now
        return []

    def get_symbol_metadata(self, symbol: str) -> SymbolMetadata:
        """Return mock metadata."""
        return SymbolMetadata(
            symbol=symbol,
            name=f"{symbol} Inc",
            market_cap=5_000_000_000,
            avg_volume_90d=2_000_000
        )

    def get_symbols_list(self) -> List[str]:
        """Return mock symbol list."""
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]


# Factory function to get provider
def get_provider(provider_type: str = "mock") -> MarketDataProvider:
    """Get market data provider by type."""
    if provider_type == "mock":
        return MockMarketDataProvider()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
