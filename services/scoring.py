"""
Scoring and ranking module.

Implements Momentum-Quality Score (MQS) formula and ranking logic.
"""

import pandas as pd
from typing import Dict, List, Tuple


def calculate_mqs(
    six_month_return: float,
    volatility: float,
    put_call_ratio: float
) -> float:
    """
    Calculate Momentum-Quality Score.

    MQS = (six_month_return / volatility) * (1 / put_call_ratio)
    """
    if volatility == 0 or put_call_ratio == 0:
        return 0.0

    return (six_month_return / volatility) * (1 / put_call_ratio)


def rank_candidates(candidates: List[Dict]) -> List[Dict]:
    """
    Rank candidates by MQS score in descending order.

    Args:
        candidates: List of candidate dicts with 'symbol' and 'mqs' keys

    Returns:
        Sorted list with 'rank' added to each candidate
    """
    sorted_candidates = sorted(candidates, key=lambda x: x.get('mqs', 0), reverse=True)

    for rank, candidate in enumerate(sorted_candidates, 1):
        candidate['rank'] = rank

    return sorted_candidates
