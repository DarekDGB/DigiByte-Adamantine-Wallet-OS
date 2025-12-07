"""
Risk aggregation logic for Shield Bridge.

Takes LayerResult objects and produces a RiskMap suitable for
Guardian + Risk Engine consumption.

MIT Licensed.
Author: @Darek_DGB
"""

from __future__ import annotations

from typing import Iterable

from .exceptions import AggregationError
from .models import LayerResult, RiskMap


class RiskAggregator:
    """
    Minimal, deterministic aggregator.

    For v0.2 this simply wraps LayerResult objects into a RiskMap.
    More advanced weighting or cross-layer logic belongs in the
    Risk Engine (core/risk-engine).
    """

    def build_risk_map(
        self, packet_id: str, results: Iterable[LayerResult]
    ) -> RiskMap:
        risk_map = RiskMap(packet_id=packet_id)
        try:
            for result in results:
                risk_map.add_result(result)
        except Exception as exc:  # pragma: no cover - defensive
            raise AggregationError(str(exc)) from exc
        return risk_map
