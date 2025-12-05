"""
core/node/node_health.py

Pure scoring logic for evaluating DigiByte node health.
NodeClient performs RPC calls; NodeManager collects measurements.
This module turns raw observations into a normalized 0–100 score.

Design goals:
    - deterministic and testable
    - monotonic score (more problems → lower score)
    - wallet can treat scores <40 as unhealthy, <20 as failing
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

@dataclass
class NodeHealthResult:
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
    ) -> NodeHealthResult:
        """
        Score a node using weighted, monotonic rules.

        Parameters
        ----------
        reachable : bool
            Whether the node responded to RPC.
        latency_ms : float | None
            Round-trip time. None = unreachable or not measured.
        node_height : int | None
            Reported node block height.
        network_height : int | None
            Chain tip from reference (remote API, DQSN consensus, or other node).
        error_count : int
            Number of RPC failures in recent window.
        """

        if not reachable:
            return NodeHealthResult(
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

        return NodeHealthResult(
            reachable=True,
            block_height=node_height,
            latency_ms=latency_ms,
            error_count=error_count,
            score=score,
        )
