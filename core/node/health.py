"""
core/node/health.py

Pure scoring logic for evaluating DigiByte node health.

Design goals:
    - deterministic and testable
    - monotonic score (more problems → lower score)
    - simple health states:
        UNKNOWN / HEALTHY / DEGRADED / UNHEALTHY

Tests expect three public entry points:

    - NodeMetrics            – raw node measurements
    - NodeHealth             – evaluated health result
    - score_node_health()    – helper metrics -> health (returns status)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union


# ---------------------------------------------------------------------------
# Input model – raw metrics collected from a node
# ---------------------------------------------------------------------------


@dataclass
class NodeMetrics:
    """
    Simple container for raw node metrics.

    Tests construct this as:

        NodeMetrics(
            latency_ms=...,
            failure_ratio=...,
            height_drift=...,
        )

    where:

        latency_ms    – round-trip latency in milliseconds
        failure_ratio – fraction of recent RPC calls that failed (0.0–1.0)
        height_drift  – how many blocks this node is behind (or ahead) of
                        the best known height (0 = perfectly in sync)
    """

    latency_ms: Optional[float] = None
    failure_ratio: float = 0.0
    height_drift: int = 0


# ---------------------------------------------------------------------------
# Result model – evaluated health
# ---------------------------------------------------------------------------


@dataclass
class NodeHealth:
    """
    Evaluated health of a single node.

    Attributes
    ----------
    latency_ms : float | None
        Raw latency from metrics.
    failure_ratio : float
        Raw failure ratio from metrics.
    height_drift : int
        Raw height drift from metrics.
    score : float
        Normalised score in [0, 100].
    status : str
        One of: "unknown", "healthy", "degraded", "unhealthy".
    """

    # Class-level constants used by tests and callers
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

    latency_ms: Optional[float]
    failure_ratio: float
    height_drift: int
    score: float
    status: str

    # Convenience helpers used by tests / callers
    def is_unknown(self) -> bool:
        return self.status == self.UNKNOWN

    def is_healthy(self) -> bool:
        return self.status == self.HEALTHY

    def is_degraded(self) -> bool:
        return self.status == self.DEGRADED

    def is_unhealthy(self) -> bool:
        return self.status == self.UNHEALTHY


# Backwards-compatibility alias if older code imported this name.
NodeHealthResult = NodeHealth


# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------


class NodeHealthScorer:
    """
    Pure scorer that turns NodeMetrics into a 0–100 score and a simple status.
    """

    MAX_SCORE = 100.0
    MIN_SCORE = 0.0

    @staticmethod
    def _score_latency(latency_ms: Optional[float]) -> float:
        """
        Map latency into [0, 1].

        Thresholds are chosen to match the intent of tests:

            - < 500 ms      → perfect (1.0)
            - 500–2000 ms   → mildly degraded (0.7)
            - 2000–4000 ms  → worse (0.4)
            - >= 4000 ms    → unhealthy (0.1)
            - None          → unknown (treated as neutral 0.5)
        """
        if latency_ms is None:
            return 0.5

        if latency_ms < 500:
            return 1.0
        if latency_ms < 2000:
            return 0.7
        if latency_ms < 4000:
            return 0.4
        return 0.1

    @staticmethod
    def _score_failure_ratio(ratio: float) -> float:
        """
        Map failure ratio (0.0–1.0) into [0, 1].

            - 0.0–0.1   → healthy (1.0)
            - 0.1–0.5   → degraded (0.6)
            - > 0.5     → unhealthy (0.2)
        """
        if ratio <= 0.1:
            return 1.0
        if ratio <= 0.5:
            return 0.6
        return 0.2

    @staticmethod
    def _score_height_drift(drift: int) -> float:
        """
        Map height drift in blocks into [0, 1].

            - 0–1 blocks   → healthy (1.0)
            - 2–5 blocks   → degraded (0.6)
            - > 5 blocks   → unhealthy (0.2)
        """
        d = abs(drift)
        if d <= 1:
            return 1.0
        if d <= 5:
            return 0.6
        return 0.2

    @classmethod
    def score_metrics(cls, metrics: NodeMetrics) -> NodeHealth:
        """
        Main scoring entrypoint: NodeMetrics -> NodeHealth.
        """

        # Special case: "no data" → UNKNOWN
        if (
            metrics.latency_ms is None
            and metrics.failure_ratio == 0.0
            and metrics.height_drift == 0
        ):
            return NodeHealth(
                latency_ms=metrics.latency_ms,
                failure_ratio=metrics.failure_ratio,
                height_drift=metrics.height_drift,
                score=50.0,
                status=NodeHealth.UNKNOWN,
            )

        latency_score = cls._score_latency(metrics.latency_ms)
        failure_score = cls._score_failure_ratio(metrics.failure_ratio)
        height_score = cls._score_height_drift(metrics.height_drift)

        # Simple average; everything in [0,1]
        composite = (latency_score + failure_score + height_score) / 3.0
        score = max(cls.MIN_SCORE, min(cls.MAX_SCORE, composite * 100.0))

        # Derive status from score
        if score >= 80.0:
            status = NodeHealth.HEALTHY
        elif score >= 50.0:
            status = NodeHealth.DEGRADED
        else:
            status = NodeHealth.UNHEALTHY

        return NodeHealth(
            latency_ms=metrics.latency_ms,
            failure_ratio=metrics.failure_ratio,
            height_drift=metrics.height_drift,
            score=score,
            status=status,
        )

    @classmethod
    def score_node(
        cls,
        reachable: bool,
        latency_ms: Optional[float],
        failure_ratio: float,
        height_drift: int,
    ) -> NodeHealth:
        """
        Legacy convenience: accept raw primitives instead of NodeMetrics.

        If `reachable` is False, we treat the node as very unhealthy.
        """
        if not reachable:
            # Completely unreachable → terrible score.
            return NodeHealth(
                latency_ms=None,
                failure_ratio=1.0,
                height_drift=height_drift,
                score=0.0,
                status=NodeHealth.UNHEALTHY,
            )

        metrics = NodeMetrics(
            latency_ms=latency_ms,
            failure_ratio=failure_ratio,
            height_drift=height_drift,
        )
        return cls.score_metrics(metrics)


# ---------------------------------------------------------------------------
# Public helper – what tests import
# ---------------------------------------------------------------------------


def score_node_health(
    metrics_or_reachable: Union[NodeMetrics, bool],
    latency_ms: Optional[float] | None = None,
    failure_ratio: float = 0.0,
    height_drift: int = 0,
) -> str:
    """
    Convenience wrapper used by tests.

    It supports two call patterns and always returns the **status string**
    (one of NodeHealth.UNKNOWN / HEALTHY / DEGRADED / UNHEALTHY):

    1) With NodeMetrics (preferred):

        m = NodeMetrics(latency_ms=200, failure_ratio=0.0, height_drift=0)
        status = score_node_health(m)

    2) With raw primitives (legacy):

        status = score_node_health(
            True,              # reachable
            latency_ms=200.0,
            failure_ratio=0.1,
            height_drift=2,
        )
    """

    if isinstance(metrics_or_reachable, NodeMetrics):
        health = NodeHealthScorer.score_metrics(metrics_or_reachable)
        return health.status

    reachable = bool(metrics_or_reachable)
    health = NodeHealthScorer.score_node(
        reachable=reachable,
        latency_ms=latency_ms,
        failure_ratio=failure_ratio,
        height_drift=height_drift,
    )
    return health.status
