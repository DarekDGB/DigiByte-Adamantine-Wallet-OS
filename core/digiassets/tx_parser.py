"""
DigiByte Adamantine Wallet — DigiAssets Transaction Parser
----------------------------------------------------------

This module provides a *skeleton* parser that converts raw DigiByte
transactions (mempool or confirmed) into a structured DigiAssets view.

It does **NOT** perform:
- on-chain validation,
- detailed envelope decoding,
- supply enforcement,
- reorg handling.

Those behaviours will be added on top.

The goal here is to define the clean API and the parsing flow structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .models import (
    DigiAssetTxView,
    DigiAssetAmount,
    DigiAssetOperation,
)


# ---------------------------------------------------------------------------
# Utility placeholders — to be implemented in future steps
# ---------------------------------------------------------------------------

def detect_digiasset_envelope(tx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Detect if the transaction contains a DigiAssets envelope.

    This is a placeholder. In full implementation, this function would:

    - scan outputs for OP_RETURN prefix
    - detect DigiAssets version byte
    - extract operation type
    - extract asset_id
    - extract per-output asset quantities (if encoded)

    Returns:
        dict with fields:
            {
                "operation": "ISSUE" | "TRANSFER" | "BURN" | "REISSUE",
                "asset_id": "...",
                "payload": { ... }  # protocol-dependent
            }

        Or None if no DigiAssets structure is detected.
    """
    return None  # placeholder until spec-level logic is implemented


def extract_wallet_addresses(tx: Dict[str, Any]) -> (List[str], List[str]):
    """
    Extract source and target addresses from the raw TX.

    This helps populate DigiAssetTxView.from_addresses / to_addresses.

    NOTE: This is deliberately simple because full address/script
    analysis will be implemented later.
    """
    inputs = []
    outputs = []

    for vin in tx.get("vin", []):
        addr = vin.get("address")
        if addr:
            inputs.append(addr)

    for vout in tx.get("vout", []):
        addr = vout.get("address")
        if addr:
            outputs.append(addr)

    return inputs, outputs


# ---------------------------------------------------------------------------
# Main parser class
# ---------------------------------------------------------------------------

class DigiAssetTxParser:
    """
    Stateless parser that takes a DigiByte transaction (raw JSON-like dict)
    and returns a DigiAssetTxView if the transaction participates in the
    DigiAssets protocol.
    """

    def parse(self, tx: Dict[str, Any], block_height: Optional[int] = None) -> Optional[DigiAssetTxView]:
        """
        Parse a raw DigiByte transaction into a DigiAssets-aware structure.

        Args:
            tx: raw tx dict from DigiByte RPC or indexer
            block_height: None if mempool

        Returns:
            DigiAssetTxView OR None if no DigiAssets activity is present.
        """

        envelope = detect_digiasset_envelope(tx)
        if envelope is None:
            return None  # Not a DigiAssets TX

        op_type = DigiAssetOperation(envelope["operation"])
        asset_id = envelope["asset_id"]

        # --- Extract address info for UX ------------------------------------
        from_addrs, to_addrs = extract_wallet_addresses(tx)

        # --- Amount extraction (placeholder for real protocol logic) --------
        # For now we create empty input/output lists.
        # Later we will fill these with true DigiAssetAmount derived
        # from protocol rules, payload, and tx graph.
        amounts_in: List[DigiAssetAmount] = []
        amounts_out: List[DigiAssetAmount] = []

        # Placeholder logic: future steps will decode quantity fields,
        # match outputs, and detect change.
        # ---------------------------------------------------------------------

        txid = tx.get("txid", "UNKNOWN")

        return DigiAssetTxView(
            txid=txid,
            block_height=block_height,
            op_type=op_type,
            asset_id=asset_id,
            amounts_in=amounts_in,
            amounts_out=amounts_out,
            from_addresses=from_addrs,
            to_addresses=to_addrs,
        )
