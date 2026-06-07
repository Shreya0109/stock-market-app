"""
Technical indicators calculation module.

Computes EMA, RSI, ADX, ATR, and other indicators for the recommendation engine.
"""

import pandas as pd
import numpy as np


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index."""
    # Placeholder implementation
    return pd.Series(0, index=close.index)


def calculate_relative_volume(volume: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Relative Volume (current volume / average volume)."""
    avg_volume = volume.rolling(window=period).mean()
    relative_volume = volume / avg_volume
    return relative_volume
