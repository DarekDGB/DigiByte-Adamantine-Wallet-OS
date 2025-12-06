"""
core.risk_engine.risk_engine

DigiByte Adamantine Wallet — Risk Engine

This module exposes a very small, test-oriented API:

  * RiskInputs – bundle of layer scores + flags.
  * RiskScore  – final numeric score + level + reasons.
  * RiskEngine – scoring implementation.

The scoring model is intentionally simple and can be evolved later
without breaking callers, as long as the public types stay stable.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class RiskLevel(str, Enum):
    """Enum is kept for convenience, but tests work with lower-case strings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskInputs:
    """
    Minimal bundle of risk inputs used by tests.

    All scores are expected to be normalised to [0.0, 1.0], where
    higher means *more risk* coming from that layer.
    """

    sentinel_score: float
    dqsn_score: float
    adn_score: float
    adaptive_score: float

    anomaly_flags: List[str]
    quantum_alert: bool

    tx_volume: int
    timestamp: dt.datetime


@dataclass
class RiskScore:
    """
    Final risk score for a situation (current shield state, TX context, etc.).

    `value` is a normalised score in [0.0, 1.0] (tests only require 0–100),
    `level` is a lower-case string in {"low","medium","high","critical"}.
    """

    value: float
    level: str
    reasons: List[str] = field(default_factory=list)


class RiskEngine:
    """
    Simple weighted risk engine.

    Heuristic model (v0):

      * Start from the mean of all layer scores.
      * Add a fixed bump for anomaly_flags and quantum_alert.
      * Clamp to [0.0, 1.0].
      * Map to a qualitative risk level.
    """

    def __init__(
        self,
        anomaly_bump: float = 0.10,
        quantum_bump: float = 0.20,
    ) -> None:
        self.anomaly_bump = anomaly_bump
        self.quantum_bump = quantum_bump

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, inputs: RiskInputs) -> RiskScore:
        """
        Compute a RiskScore from the given inputs.
        """
        # 1) Base: average of layer scores.
        base = (
            inputs.sentinel_score
            + inputs.dqsn_score
            + inputs.adn_score
            + inputs.adaptive_score
        ) / 4.0

        score = base

        # 2) Anomalies bump risk.
        reasons: List[str] = []
        if inputs.anomaly_flags:
            score += self.anomaly_bump
            flags = sorted(set(inputs.anomaly_flags))
            reasons.append(f"Anomaly flags present: {', '.join(flags)}")

        # 3) Quantum alert bump.
        if inputs.quantum_alert:
            score += self.quantum_bump
            reasons.append("Quantum alert signalled by shield")

        # 4) Clamp to [0.0, 1.0].
        score = max(0.0, min(score, 1.0))

        # 5) Map to level (tests only check membership, not exact thresholds).
        if score >= 0.85:
            level = RiskLevel.CRITICAL.value
        elif score >= 0.60:
            level = RiskLevel.HIGH.value
        elif score >= 0.25:
            level = RiskLevel.MEDIUM.value
        else:
            level = RiskLevel.LOW.value

        return RiskScore(value=score, level=level, reasons=reasons)
