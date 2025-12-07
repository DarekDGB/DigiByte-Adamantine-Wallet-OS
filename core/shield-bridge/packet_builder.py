"""
Helpers for constructing RiskPacket instances from Guardian / wallet context.

MIT Licensed.
Author: @Darek_DGB
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from .models import RiskPacket


def new_packet_id() -> str:
    """Generate a unique packet identifier."""
    return str(uuid.uuid4())


def build_risk_packet(
    wallet_id: str,
    account_id: str,
    flow_type: str,
    amount_sats: int,
    asset_id: Optional[str] = None,
    metadata_size: int = 0,
    client: str = "service",
    context: Optional[Dict[str, Any]] = None,
    layer_payloads: Optional[Dict[str, Dict[str, Any]]] = None,
) -> RiskPacket:
    """
    Convenience helper to create a RiskPacket from common inputs.

    Guardian / wallet-service can call this to standardize packet creation.
    """
    return RiskPacket(
        packet_id=new_packet_id(),
        wallet_id=wallet_id,
        account_id=account_id,
        flow_type=flow_type,
        amount_sats=amount_sats,
        asset_id=asset_id,
        metadata_size=metadata_size,
        client=client,
        context=context or {},
        layer_payloads=layer_payloads or {},
    )
