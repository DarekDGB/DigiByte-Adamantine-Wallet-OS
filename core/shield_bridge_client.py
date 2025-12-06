"""
Shield Bridge Client
====================

This module is the **glue** between the DigiByte Quantum Shield layers
(Sentinel, DQSN, ADN, Adaptive Core, QWG) and the Adamantine Wallet.

It does NOT talk directly to the blockchain or change consensus.
Its job is to:

- accept raw metrics / scores from each shield layer,
- normalise them into a simple 0.0–1.0 health score,
- attach a coarse status label: OK / WARN / ALERT,
- expose a single `ShieldSnapshot` object that the wallet / UI / risk
  engine can consume.

Later, this client can be wired to:
- Sentinel AI v2 telemetry streams,
- DQSN v2 distributed confirmations,
- ADN v2 node-level lockdown signals,
- Quantum Wallet Guard (QWG),
- Adaptive Core immune responses.

For now, we keep the implementation intentionally simple and
self-contained, so it can evolve without breaking anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional


# ---------------------------------------------------------------------------
# Basic status enums / models
# ---------------------------------------------------------------------------


class LayerHealthStatus(str, Enum):
    """Coarse health status for a single shield layer."""

    OK = "OK"
    WARN = "WARN"
    ALERT = "ALERT"


@dataclass
class LayerHealth:
    """
    Normalised health view for a single shield layer.

    Attributes
    ----------
    layer:
        Human-readable layer name (e.g. "sentinel", "dqsn", "adn").
    score:
        Float in [0.0, 1.0]; higher means *more* risk / stress.
        0.0  -> perfectly calm
        0.25 -> slightly elevated
        0.5  -> concerning
        0.75 -> high risk
        1.0  -> critical
    status:
        Coarse qualitative state derived from the score.
    details:
        Optional extra metadata (raw metrics, flags, etc.).
    """

    layer: str
    score: float
    status: LayerHealthStatus
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ShieldSnapshot:
    """
    Aggregated view of all shield layers at a point in time.

    This is what the wallet / UI will eventually consume.

    Attributes
    ----------
    sentinel:
        Sentinel telemetry / anomaly view.
    dqsn:
        Distributed confirmation network view.
    adn:
        Node-level lockdown / defence view.
    adaptive:
        Adaptive Core / immune-system style score.
    overall_score:
        Simple aggregate in [0.0, 1.0] (max of layer scores by default).
    meta:
        Optional extra metadata.
    """

    sentinel: Optional[LayerHealth] = None
    dqsn: Optional[LayerHealth] = None
    adn: Optional[LayerHealth] = None
    adaptive: Optional[LayerHealth] = None

    overall_score: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)

    def max_status(self) -> LayerHealthStatus:
        """
        Return the 'worst' status among all layers.

        Ordering: ALERT > WARN > OK
        """
        order = {LayerHealthStatus.OK: 0,
                 LayerHealthStatus.WARN: 1,
                 LayerHealthStatus.ALERT: 2}

        statuses = [
            lh.status
            for lh in (self.sentinel, self.dqsn, self.adn, self.adaptive)
            if lh is not None
        ]
        if not statuses:
            return LayerHealthStatus.OK
        return max(statuses, key=lambda s: order[s])


# ---------------------------------------------------------------------------
# Shield Bridge client
# ---------------------------------------------------------------------------


class ShieldBridgeClient:
    """
    High-level adapter that converts raw shield metrics into LayerHealth
    and ShieldSnapshot objects.

    In future this may pull directly from:
      - Sentinel AI v2 metrics streams,
      - DQSN v2 gossip / confirmations,
      - ADN v2 node health + lockdown state,
      - Adaptive Core immune system events.

    For now we expose simple `from_*` helpers that accept already
    normalised scores or raw data and map them into LayerHealth.
    """

    # ------------------------- utility helpers ------------------------- #

    @staticmethod
    def _normalise_score(raw: float) -> float:
        """
        Clamp a raw float into the [0.0, 1.0] range.

        The caller is expected to pass something that roughly represents
        a risk score; we simply make sure it doesn't leave the 0–1 range.
        """
        if raw < 0.0:
            return 0.0
        if raw > 1.0:
            return 1.0
        return raw

    @staticmethod
    def _status_from_score(score: float) -> LayerHealthStatus:
        """
        Derive a coarse status from a normalised score.
        """
        if score >= 0.75:
            return LayerHealthStatus.ALERT
        if score >= 0.35:
            return LayerHealthStatus.WARN
        return LayerHealthStatus.OK

    @classmethod
    def _make_layer(
        cls,
        layer: str,
        raw_score: float,
        details: Dict[str, Any] | None = None,
    ) -> LayerHealth:
        score = cls._normalise_score(raw_score)
        status = cls._status_from_score(score)
        return LayerHealth(layer=layer, score=score, status=status,
                           details=details or {})

    # ------------------------ per-layer builders ----------------------- #

    def from_sentinel(
        self, *, score: float, details: Dict[str, Any] | None = None
    ) -> LayerHealth:
        """
        Build a LayerHealth view for Sentinel AI v2.

        `score` should be in [0, 1] where higher = more risk.
        """
        return self._make_layer("sentinel", score, details)

    def from_dqsn(
        self, *, score: float, details: Dict[str, Any] | None = None
    ) -> LayerHealth:
        """Build a LayerHealth view for DQSN v2."""
        return self._make_layer("dqsn", score, details)

    def from_adn(
        self, *, score: float, details: Dict[str, Any] | None = None
    ) -> LayerHealth:
        """Build a LayerHealth view for ADN v2."""
        return self._make_layer("adn", score, details)

    def from_adaptive_core(
        self, *, score: float, details: Dict[str, Any] | None = None
    ) -> LayerHealth:
        """Build a LayerHealth view for Adaptive Core."""
        return self._make_layer("adaptive_core", score, details)

    # ----------------------- snapshot composition ---------------------- #

    def build_snapshot(
        self,
        *,
        sentinel: LayerHealth | None = None,
        dqsn: LayerHealth | None = None,
        adn: LayerHealth | None = None,
        adaptive: LayerHealth | None = None,
        meta: Dict[str, Any] | None = None,
    ) -> ShieldSnapshot:
        """
        Combine individual layer health objects into a single snapshot.

        If any layer is None, it is simply omitted from the aggregate.
        The default overall_score is the max of available layer scores.
        """
        layers = [lh for lh in (sentinel, dqsn, adn, adaptive) if lh is not None]
        overall = max((lh.score for lh in layers), default=0.0)

        return ShieldSnapshot(
            sentinel=sentinel,
            dqsn=dqsn,
            adn=adn,
            adaptive=adaptive,
            overall_score=overall,
            meta=meta or {},
        )
