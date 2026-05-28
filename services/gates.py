"""
Filtering gates module.

Implements liquidity gates and momentum gates for candidate selection.
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class GateConfig:
    """Configuration for filtering gates."""

    # Liquidity Gates
    min_market_cap: float = 2_000_000_000  # $2B
    min_avg_volume_90d: float = 1_000_000  # 1M shares
    min_price: float = 10.0

    # Momentum Gates
    min_rsi: float = 60
    max_rsi: float = 75
    min_adx: float = 25
    min_relative_volume: float = 2.0

    # Sentiment Gates
    max_put_call_ratio: float = 1.20
    min_put_call_ratio: float = 0.0


def apply_liquidity_gate(candidate: Dict, config: GateConfig) -> bool:
    """Check if candidate passes liquidity filters."""
    market_cap = candidate.get('market_cap', 0)
    avg_volume = candidate.get('avg_volume_90d', 0)
    price = candidate.get('price', 0)

    return (
        market_cap >= config.min_market_cap
        and avg_volume >= config.min_avg_volume_90d
        and price >= config.min_price
    )


def apply_momentum_gate(candidate: Dict, config: GateConfig) -> bool:
    """Check if candidate passes momentum filters."""
    rsi = candidate.get('rsi', 0)
    adx = candidate.get('adx', 0)
    relative_volume = candidate.get('relative_volume', 0)
    ema_5 = candidate.get('ema_5', 0)
    ema_50 = candidate.get('ema_50', 0)
    ema_200 = candidate.get('ema_200', 0)
    close = candidate.get('close', 0)

    # Trend confirmation
    trend_ok = (close > ema_5) and (ema_5 > ema_50) and (ema_50 > ema_200)

    # RSI check
    rsi_ok = config.min_rsi <= rsi <= config.max_rsi

    # ADX check
    adx_ok = adx > config.min_adx

    # Relative volume check
    rvol_ok = relative_volume > config.min_relative_volume

    return trend_ok and rsi_ok and adx_ok and rvol_ok


def apply_sentiment_gate(candidate: Dict, config: GateConfig) -> bool:
    """Check if candidate passes sentiment filters."""
    put_call_ratio = candidate.get('put_call_ratio', 0.8)

    # Bullish: low put/call ratio
    if put_call_ratio < config.min_put_call_ratio:
        return True

    # Warning: high put/call ratio (possible trap)
    if put_call_ratio > config.max_put_call_ratio:
        return False

    # Neutral zone: acceptable
    return True


def filter_candidates(
    candidates: List[Dict],
    config: GateConfig = None
) -> List[Dict]:
    """
    Apply all gates to filter candidates.

    Returns:
        List of candidates that pass all gates
    """
    if config is None:
        config = GateConfig()

    filtered = []

    for candidate in candidates:
        if (
            apply_liquidity_gate(candidate, config)
            and apply_momentum_gate(candidate, config)
            and apply_sentiment_gate(candidate, config)
        ):
            filtered.append(candidate)

    return filtered
