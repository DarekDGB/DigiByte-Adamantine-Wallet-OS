"""
DigiByte Adamantine Wallet — Risk Engine Skeleton
-------------------------------------------------

This module defines a simple, extensible risk-scoring engine used by
the Adamantine Wallet and Shield stack.

It consumes *risk signals* from multiple sources (Sentinel, DQSN,
ADN, Guardian, QWG, etc.) and produces:

- a numeric score (0–100, higher = safer)
- a RiskLevel classification
- human-readable labels

This is a **wallet-side** risk model. It does NOT change consensus
rules or node behaviour by itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class RiskLevel(str, Enum):
    """High-level risk categories for UI and shield logic."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskSignal:
    """
    A single risk signal emitted by some subsystem.

    Examples:
        source = "sentinel"
        code   = "CHAIN_REORG"
        weight = 9

        source = "guardian"
        code   = "RULE_VIOLATION"
        weight = 7
    """

    source: str
    code: str
    weight: int = 1  # 1–10, higher means more impact
    description: Optional[str] = None
    details: Dict[str, str] = field(default_factory=dict)


@dataclass
class RiskResult:
    """
    Final risk assessment for a given context (wallet, account, action).
    """

    score: int                     # 0–100, higher = safer
    level: RiskLevel
    labels: List[str] = field(default_factory=list)
    signals: List[RiskSignal] = field(default_factory=list)

    def add_label(self, label: str) -> None:
        if label not in self.labels:
            self.labels.append(label)


class RiskEngine:
    """
    Simple weighted risk engine.

    Scoring model (initial skeleton):

        base_score = 100
        penalty = sum(signal.weight * per_signal_factor)
        score = clamp(base_score - penalty, 0, 100)

    Thresholds for RiskLevel (configurable via constructor):

        CRITICAL: score <= critical_max
        HIGH    : score <= high_max
        MEDIUM  : score <= medium_max
        LOW     : otherwise
    """

    def __init__(
        self,
        per_signal_factor: int = 5,
        critical_max: int = 25,
        high_max: int = 50,
        medium_max: int = 75,
    ) -> None:
        self.per_signal_factor = per_signal_factor
        self.critical_max = critical_max
        self.high_max = high_max
        self.medium_max = medium_max

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, signals: List[RiskSignal]) -> RiskResult:
        """
        Compute a RiskResult from a list of RiskSignal inputs.
        """

        base_score = 100

        penalty = 0
        for s in signals:
            # Clamp weight to a sane range [0, 10]
            w = max(0, min(s.weight, 10))
            penalty += w * self.per_signal_factor

        score = max(0, min(base_score - penalty, 100))
        level = self._level_for_score(score)

        result = RiskResult(score=score, level=level, signals=list(signals))

        # Auto-label common patterns
        for s in signals:
            self._attach_labels_from_signal(result, s)

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _level_for_score(self, score: int) -> RiskLevel:
        if score <= self.critical_max:
            return RiskLevel.CRITICAL
        if score <= self.high_max:
            return RiskLevel.HIGH
        if score <= self.medium_max:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _attach_labels_from_signal(self, result: RiskResult, signal: RiskSignal) -> None:
        """
        Map known risk codes to UI / shield labels.

        This is intentionally simple; future versions can load mappings
        from config/risk-profiles.yml or similar.
        """

        code = signal.code.upper()

        if code in {"CHAIN_REORG", "DEEP_REORG"}:
            result.add_label("chain_reorg")

        if code in {"PQC_MISSING", "PQC_WEAK"}:
            result.add_label("pqc_attention")

        if code in {"DOUBLE_SPEND_SUSPECT"}:
            result.add_label("double_spend")

        if code in {"GUARDIAN_RULE_VIOLATION"}:
            result.add_label("guardian_violation")

        if code in {"ANOMALOUS_FEE"}:
            result.add_label("fee_anomaly")

        # Generic fallback: include raw code for debug visibility
        result.add_label(f"signal:{code.lower()}")
