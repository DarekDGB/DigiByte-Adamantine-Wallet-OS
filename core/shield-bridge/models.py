"""
Shield Bridge Models (v0.2 runtime skeleton)

MIT Licensed.
Author: @Darek_DGB
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


RiskScore = float


@dataclass
class RiskPacket:
    """
    Normalized risk request travelling through Shield Bridge.

    This mirrors the JSON structure from docs/shield-bridge/overview.md
    but is kept minimal and implementation-agnostic.
    """

    packet_id: str
    wallet_id: str
    account_id: str
    flow_type: str  # e.g. "TRANSFER", "MINT", "BURN", "MESSAGE", "NODE_OP"
    amount_sats: int
    asset_id: Optional[str] = None
    metadata_size: int = 0
    client: str = "service"  # "web" | "ios" | "android" | "service"
    context: Dict[str, Any] = field(default_factory=dict)
    layer_payloads: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "wallet_id": self.wallet_id,
            "account_id": self.account_id,
            "flow_type": self.flow_type,
            "amount_sats": self.amount_sats,
            "asset_id": self.asset_id,
            "metadata_size": self.metadata_size,
            "client": self.client,
            "context": self.context,
            "layer_payloads": self.layer_payloads,
        }


@dataclass
class LayerResult:
    """
    Response from a single shield layer.

    risk_score is always in [0.0, 1.0].
    """

    layer: str  # "sentinel" | "dqsn" | "adn" | "qwg" | "adaptive" | custom
    risk_score: RiskScore
    status: str = "ok"  # "ok" | "unreachable" | "error"
    signals: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer": self.layer,
            "risk_score": self.risk_score,
            "status": self.status,
            "signals": self.signals,
        }


@dataclass
class RiskMap:
    """
    Aggregated results from all shield layers for a given RiskPacket.
    """

    packet_id: str
    results: List[LayerResult] = field(default_factory=list)

    def add_result(self, result: LayerResult) -> None:
        self.results.append(result)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "results": [r.to_dict() for r in self.results],
        }

    def get_score_by_layer(self, layer: str) -> Optional[RiskScore]:
        for r in self.results:
            if r.layer == layer:
                return r.risk_score
        return None
