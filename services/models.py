"""
Shared data models for AlphaMomentum.

Core domain models used across the application.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class RecommendationStatus(str, Enum):
    """Status of a recommendation."""

    OPEN = "open"
    TARGET_HIT = "target_hit"
    STOP_HIT = "stop_hit"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"


class SetupType(str, Enum):
    """Type of trading setup."""

    BREAKOUT = "breakout"
    CONTINUATION = "continuation"
    PULLBACK = "pullback"


@dataclass
class Recommendation:
    """A daily recommendation."""

    symbol: str
    date: datetime
    setup_type: SetupType
    entry_low: float
    entry_high: float
    stop_loss: float
    target: float
    mqs_score: float
    rationale: str
    put_call_ratio: Optional[float] = None
    status: RecommendationStatus = RecommendationStatus.OPEN

    @property
    def risk_reward(self) -> float:
        """Calculate risk/reward ratio."""
        if self.entry_high == self.stop_loss:
            return 0.0
        risk = self.entry_high - self.stop_loss
        reward = self.target - self.entry_high
        return reward / risk if risk != 0 else 0.0


@dataclass
class PipelineRun:
    """Record of a pipeline execution."""

    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    symbols_processed: int = 0
    recommendations_count: int = 0
    status: str = "running"  # running, success, failed
    error_message: Optional[str] = None
