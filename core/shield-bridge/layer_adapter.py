"""
Layer adapters for Shield Bridge.

Each adapter is responsible for translating between the generic
RiskPacket / LayerResult model and a concrete shield layer API
(Sentinel, DQSN, ADN, QWG, Adaptive, etc.).

This module only provides abstract interfaces and simple no-op
implementations suitable for v0.2 architecture.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# IMPORTANT:
# Relative imports do NOT work because shield-bridge is not a package.
# Tests add core/shield-bridge to sys.path, so we import top-level modules.
from models import LayerResult, RiskPacket


class BaseLayerAdapter(ABC):
    """Abstract base for all shield layer adapters."""

    layer_name: str

    def __init__(self, layer_name: str) -> None:
        self.layer_name = layer_name

    @abstractmethod
    def evaluate(self, packet: RiskPacket) -> LayerResult:
        """
        Evaluate the risk packet for this layer.

        Implementations should never raise internal exceptions to callers;
        instead, they should capture errors and encode them in the
        returned LayerResult (status="error").
        """


class NoopLayerAdapter(BaseLayerAdapter):
    """
    Minimal adapter that always returns risk_score=0.0 and status="unreachable".

    Useful as a placeholder when a layer is not yet implemented.
    """

    def evaluate(self, packet: RiskPacket) -> LayerResult:
        return LayerResult(
            layer=self.layer_name,
            risk_score=0.0,
            status="unreachable",
            signals={"note": "layer adapter not yet implemented"},
        )


def build_default_adapters() -> dict[str, BaseLayerAdapter]:
    """
    Build a default set of adapters for all known layers.

    For v0.2 these are all "Noop" placeholders so tests and imports stay safe.
    Real implementations can gradually replace them.
    """
    layers = ["sentinel", "dqsn", "adn", "qwg", "adaptive"]
    return {name: NoopLayerAdapter(layer_name=name) for name in layers}
