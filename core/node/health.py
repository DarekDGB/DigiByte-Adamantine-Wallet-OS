"""
Node health scoring utilities.

This module provides a small, self-contained helper for turning
raw node metrics (latency, recent failures, height drift) into a
coarse health label that the rest of the wallet can reason about.

The goal is *not* to be perfect, but to give WalletService /
NodeManager something simple to sort and filter nodes by.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class NodeHealth(Enum):
    """
    Coarse health labels for nodes.

    HEALTHY       - good latency, low error rate, height looks right
    DEGRADED      - usable but worse than our best nodes
    UNHEALTHY     - probably avoid unless no alternatives
    UNKNOWN       - not enough data yet
    """

    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()


@dataclass
class NodeMetrics:
    """
    Minimal set of metrics we care about for health estimation.

    Values are intentionally simple so they can be obtained from
    many different telemetry sources (NodeManager pings, Sentinel,
    external monitors, etc.).
    """

    latency_ms: Optional[float] = None
    """Recent average latency for a simple RPC (e.g. getblockchaininfo)."""

    failure_ratio: float = 0.0
    """
    Fraction of failed RPC calls in a recent sliding window
    (0.0 = no errors, 1.0 = everything failed).
    """

    height_drift: int = 0
    """
    Difference between this node's best-known height and our
    reference height (0 = exactly in sync, positive = behind).
    """


def score_node_health(metrics: NodeMetrics) -> NodeHealth:
    """
    Turn NodeMetrics into a coarse NodeHealth label.

    The thresholds here are conservative and can be tuned later.
    """

    # Not enough data: no latency and no failures → UNKNOWN
    if metrics.latency_ms is None and metrics.failure_ratio == 0.0:
        return NodeHealth.UNKNOWN

    # Hard failure conditions
    if metrics.failure_ratio >= 0.5:
        return NodeHealth.UNHEALTHY

    if metrics.height_drift >= 10:
        # Node is significantly behind the network tip.
        return NodeHealth.UNHEALTHY

    # Latency-based degradation
    if metrics.latency_ms is not None:
        if metrics.latency_ms > 3000:
            return NodeHealth.UNHEALTHY
        if metrics.latency_ms > 1500:
            return NodeHealth.DEGRADED

    # Mild failure ratio → DEGRADED
    if 0.1 <= metrics.failure_ratio < 0.5:
        return NodeHealth.DEGRADED

    # Height slightly behind but otherwise fine → DEGRADED
    if 1 <= metrics.height_drift < 10:
        return NodeHealth.DEGRADED

    # Otherwise, looks healthy.
    return NodeHealth.HEALTHY
