"""
core/node/health.py

Pure scoring logic for evaluating DigiByte node health.
NodeClient performs RPC calls; NodeManager collects measurements.
This module turns raw observations into a normalized 0–100 score.

Design goals:
    - deterministic and testable
    - monotonic score (more problems → lower score)
    - wallet can treat scores <40 as unhealthy, <20 as failing

Tests expect three public entry points:

    - NodeMetrics      – raw node measurements
    - NodeHealth       – evaluated health result
    - score_node_health() – helper function to go from metrics -> health
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

    Tests expect NodeMetrics + NodeHealth + score_node_health to exist
    in this module.

    Fields are intentionally generic so the same structure can be used
    by different node backends (RPC, Digi-Mobile, etc.).
    """

    latency_ms: Optional[float]
    """Round-trip latency in milliseconds (None = not measured)."""

    sync_height: Optional[int]
    """
    Height reported by this node (its own tip).  This is what we compare
    against a reference / network height.
    """

    best_height: Optional[int]
    """
    Optional "best known" height (some nodes expose this separately).
    If not available, callers can pass the same value as sync_height.
    """

    mempool_tx: Optional[int]
    """Number of transactions currently in this node's mempool."""

    peers: Optional[int]
    """Number of connected peers (None if not reported)."""


# ---------------------------------------------------------------------------
# Result model – evaluated health
# ---------------------------------------------------------------------------


@dataclass
class NodeHealth:
    """Represents the evaluated health of a single node."""

    reachable: bool
    block_height: Optional[int]
    latency_ms: Optional[float]
    error_count: int
    score: float

    def is_healthy(self) -> bool:
        return self.score >= 60

    def is_unhealthy(self) -> bool:
        return self.score < 40

    def is_failing(self) -> bool:
        return self.score < 20


# Backwards-compatibility alias (if any older code used this name).
NodeHealthResult = NodeHealth


# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------


class NodeHealthScorer:
    """
    Pure scorer that turns:
        - latency
        - block height comparison
        - error counts
        - reachability

    into a 0–100 score.

    NodeManager will merge this with timestamp history to form rolling scores.
    """

    MAX_SCORE = 100
    MIN_SCORE = 0

    @staticmethod
    def score_node(
        reachable: bool,
        latency_ms: Optional[float],
        node_height: Optional[int],
        network_height: Optional[int],
        error_count: int,
    ) -> NodeHealth:
        """
        Score a node using weighted, monotonic rules.

        Parameters
        ----------
        reachable : bool
            Whether the node responded to RPC.
        latency_ms : float | None
            Round-trip time. None = unreachable or not measured.
        node_height : int | None
            Reported node block height (from this node).
        network_height : int | None
            Reference chain tip (remote API, DQSN consensus, or another node).
        error_count : int
            Number of RPC failures in recent window.
        """

        if not reachable:
            return NodeHealth(
                reachable=False,
                block_height=node_height,
                latency_ms=latency_ms,
                error_count=error_count,
                score=0,
            )

        score = NodeHealthScorer.MAX_SCORE

        # ---------------------------------------------------------
        # Latency scoring
        # ---------------------------------------------------------
        if latency_ms is None:
            score -= 20
        else:
            if latency_ms < 150:
                pass
            elif latency_ms < 300:
                score -= 10
            elif latency_ms < 600:
                score -= 25
            else:
                score -= 40

        # ---------------------------------------------------------
        # Block height scoring
        # ---------------------------------------------------------
        if node_height is None or network_height is None:
            score -= 20
        else:
            lag = network_height - node_height
            if lag <= 0:
                pass
            elif lag <= 2:
                score -= 10
            elif lag <= 5:
                score -= 25
            else:
                score -= 50

        # ---------------------------------------------------------
        # Error penalty
        # ---------------------------------------------------------
        if error_count > 0:
            score -= min(60, error_count * 10)

        # Clamp to valid bounds
        score = max(NodeHealthScorer.MIN_SCORE, min(NodeHealthScorer.MAX_SCORE, score))

        return NodeHealth(
            reachable=True,
            block_height=node_height,
            latency_ms=latency_ms,
            error_count=error_count,
            score=score,
        )


# ---------------------------------------------------------------------------
# Public helper – what tests import
# ---------------------------------------------------------------------------


def score_node_health(
    metrics_or_reachable: Union[NodeMetrics, bool],
    latency_ms: Optional[float] | None = None,
    node_height: Optional[int] | None = None,
    network_height: Optional[int] | None = None,
    error_count: int = 0,
) -> NodeHealth:
    """
    Convenience wrapper used by tests.

    It is flexible on purpose and supports two call patterns:

    1) With NodeMetrics (preferred):

        metrics = NodeMetrics(latency_ms=120, sync_height=1_000_000,
                              best_height=1_000_000, mempool_tx=5, peers=12)
        health = score_node_health(metrics, network_height=1_000_002, error_count=0)

    2) With raw primitives (fallback / legacy):

        health = score_node_health(
            True,        # reachable
            120.0,       # latency_ms
            1_000_000,   # node_height
            1_000_002,   # network_height
            0,           # error_count
        )
    """

    # Pattern 1: first argument is NodeMetrics
    if isinstance(metrics_or_reachable, NodeMetrics):
        metrics = metrics_or_reachable
        return NodeHealthScorer.score_node(
            reachable=True,  # if we have metrics, node responded
            latency_ms=metrics.latency_ms,
            node_height=metrics.sync_height,
            network_height=network_height,
            error_count=error_count,
        )

    # Pattern 2: first argument is bool -> treat as original low-level call
    reachable = bool(metrics_or_reachable)
    return NodeHealthScorer.score_node(
        reachable=reachable,
        latency_ms=latency_ms,
        node_height=node_height,
        network_height=network_height,
        error_count=error_count,
    )
