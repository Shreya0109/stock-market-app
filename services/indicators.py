"""Technical indicator calculations for the recommendation engine."""

from __future__ import annotations

import pandas as pd


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calculate an EMA after a complete lookback window is available."""
    return data.ewm(span=period, adjust=False, min_periods=period).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = data.diff()
    gain = delta.clip(lower=0).rolling(window=period, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period, min_periods=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.mask((loss == 0) & (gain > 0), 100.0)
    rsi = rsi.mask((loss == 0) & (gain == 0), 50.0)
    return rsi


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()
    return atr


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index."""
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = true_range.rolling(window=period, min_periods=period).mean()
    plus_di = 100 * plus_dm.rolling(window=period, min_periods=period).mean() / atr
    minus_di = 100 * minus_dm.rolling(window=period, min_periods=period).mean() / atr

    denominator = plus_di + minus_di
    dx = (100 * (plus_di - minus_di).abs() / denominator).where(denominator != 0)
    return dx.rolling(window=period, min_periods=period).mean()


def calculate_relative_volume(volume: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Relative Volume (current volume / average volume)."""
    avg_volume = volume.rolling(window=period, min_periods=period).mean()
    relative_volume = volume / avg_volume
    return relative_volume


def calculate_breakout_high(high: pd.Series, period: int = 20) -> pd.Series:
    """Calculate prior-period breakout high reference."""
    return high.shift(1).rolling(window=period, min_periods=period).max()


def calculate_breakout_low(low: pd.Series, period: int = 20) -> pd.Series:
    """Calculate prior-period breakout low reference."""
    return low.shift(1).rolling(window=period, min_periods=period).min()
