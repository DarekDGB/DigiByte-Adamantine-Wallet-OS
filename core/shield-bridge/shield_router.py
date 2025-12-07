"""
Shield Router — high-level interface used by Guardian / Risk Engine.

It:
- accepts a RiskPacket
- dispatches it to configured layer adapters
- aggregates responses into a RiskMap

MIT Licensed.
Author: @Darek_DGB
"""

from __future__ import annotations

from typing import Dict, Iterable

# IMPORTANT:
# shield-bridge is not a Python package, so tests add this directory
# directly to sys.path and we import top-level modules instead of
# using relative imports.
from exceptions import LayerUnavailableError
from layer_adapter import BaseLayerAdapter, build_default_adapters
from models import LayerResult, RiskMap, RiskPacket
from risk_aggregator import RiskAggregator


class ShieldRouter:
    """
    Orchestrates evaluation across all configured shield layers.

    In v0.2 this is intentionally lightweight and synchronous.
    """

    def __init__(
        self,
        adapters: Dict[str, BaseLayerAdapter] | None = None,
        aggregator: RiskAggregator | None = None,
    ) -> None:
        self.adapters: Dict[str, BaseLayerAdapter] = adapters or build_default_adapters()
        self.aggregator: RiskAggregator = aggregator or RiskAggregator()

    def _iter_layer_results(self, packet: RiskPacket) -> Iterable[LayerResult]:
        for layer_name, adapter in self.adapters.items():
            try:
                yield adapter.evaluate(packet)
            except Exception as exc:  # pragma: no cover - defensive
                # Any unexpected adapter exception is downgraded
                # into a LayerResult with status="error".
                yield LayerResult(
                    layer=layer_name,
                    risk_score=0.0,
                    status="error",
                    signals={"exception": str(exc)},
                )

    def evaluate(self, packet: RiskPacket) -> RiskMap:
        """
        Evaluate the given RiskPacket across all configured layers
        and return a RiskMap.

        Implementations may later support:
        - async fan-out
        - per-layer timeouts
        - partial failure strategies
        """
        if not self.adapters:
            raise LayerUnavailableError("no shield layers are configured")

        results = list(self._iter_layer_results(packet))
        return self.aggregator.build_risk_map(
            packet_id=packet.packet_id,
            results=results,
        )
