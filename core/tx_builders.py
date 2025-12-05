"""
core/tx_builders.py

High-level helpers for constructing WalletTransaction objects.

These builders do NOT talk to the DigiByte node directly and they do NOT
perform full UTXO selection. That work will be delegated to a lower
"chain integration" layer (e.g. core/node or a separate UTXO service).

The goal here is to:

- define *what* the wallet wants to do (kind, amounts, recipients)
- create a WalletTransaction skeleton that:
    - Guardian / Risk Engine can inspect
    - UI can present to the user for confirmation
    - node-specific code can later fill with concrete inputs and fees
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .transactions import (
    WalletTransaction,
    TxKind,
    TxStatus,
    PaymentOutput,
    FeeEstimate,
)


@dataclass
class TxBuildRequest:
    """
    Generic request to build a wallet transaction.

    This captures user intent before UTXO selection and fee estimation.
    """

    wallet_id: str
    account_id: str
    to_address: str
    amount_sats: int
    description: str = ""
    meta: Dict[str, Any] = None
    asset_id: Optional[str] = None  # for DigiAssets / DigiDollar-like flows

    def as_meta(self) -> Dict[str, Any]:
        base = self.meta.copy() if self.meta else {}
        base.setdefault("to_address", self.to_address)
        return base


# ----------------------------------------------------------------------
# DGB send
# ----------------------------------------------------------------------


def build_dgb_send_skeleton(
    tx_id: str,
    req: TxBuildRequest,
    fee_rate_hint: Optional[float] = None,
) -> WalletTransaction:
    """
    Build a skeleton WalletTransaction for a plain DGB send.

    - inputs are intentionally left empty (to be filled by UTXO selection)
    - fee.total_sats is left None; optional fee_rate_hint is recorded

    The node / chain integration layer will later:
      - choose UTXOs
      - compute vsize
      - finalise fee.total_sats
    """
    fee = FeeEstimate()
    if fee_rate_hint is not None:
        from decimal import Decimal

        fee.rate_sats_per_vbyte = Decimal(str(fee_rate_hint))

    output = PaymentOutput(
        address=req.to_address,
        value_sats=req.amount_sats,
    )

    tx = WalletTransaction(
        id=tx_id,
        kind=TxKind.DGB_SEND,
        wallet_id=req.wallet_id,
        account_id=req.account_id,
        outputs=[output],
        fee=fee,
        status=TxStatus.DRAFT,
        description=req.description or "DGB send",
        meta=req.as_meta(),
    )

    return tx


# ----------------------------------------------------------------------
# DigiDollar (DD) mint / redeem
# ----------------------------------------------------------------------


def build_dd_mint_skeleton(
    tx_id: str,
    req: TxBuildRequest,
    oracle_price_hint: Optional[float] = None,
) -> WalletTransaction:
    """
    Skeleton for a DigiDollar mint (DGB -> DD).

    `amount_sats` here is the DGB being committed to the mint.
    The actual DD amount will be derived by the DigiDollar engine
    using oracle data; we record hints in `meta`.
    """
    meta = req.as_meta()
    if oracle_price_hint is not None:
        meta.setdefault("oracle_price_hint", oracle_price_hint)

    tx = WalletTransaction(
        id=tx_id,
        kind=TxKind.DIGIDOLLAR_MINT,
        wallet_id=req.wallet_id,
        account_id=req.account_id,
        outputs=[],  # on-chain representation handled by DD engine
        fee=FeeEstimate(),
        status=TxStatus.DRAFT,
        description=req.description or "Mint DigiDollar (DD)",
        meta=meta,
    )

    # DD engine / node integration layer will:
    #   - choose DGB inputs
    #   - encode DD-mint-specific outputs / metadata
    return tx


def build_dd_redeem_skeleton(
    tx_id: str,
    req: TxBuildRequest,
) -> WalletTransaction:
    """
    Skeleton for a DigiDollar redeem (DD -> DGB).

    `amount_sats` can represent DD minor units, depending on convention.
    Chain-specific code will turn this into concrete redeem transactions.
    """
    meta = req.as_meta()
    meta.setdefault("dd_amount_units", req.amount_sats)

    tx = WalletTransaction(
        id=tx_id,
        kind=TxKind.DIGIDOLLAR_REDEEM,
        wallet_id=req.wallet_id,
        account_id=req.account_id,
        outputs=[],
        fee=FeeEstimate(),
        status=TxStatus.DRAFT,
        description=req.description or "Redeem DigiDollar (DD)",
        meta=meta,
    )
    return tx


# ----------------------------------------------------------------------
# DigiAssets & Enigmatic placeholders (to be expanded later)
# ----------------------------------------------------------------------


def build_digiasset_skeleton(
    tx_id: str,
    req: TxBuildRequest,
    op_kind: str,
) -> WalletTransaction:
    """
    Skeleton for DigiAsset operations (mint / transfer / burn).

    This function only tags the transaction; concrete asset encodings
    will live in the DigiAssets engine.
    """
    meta = req.as_meta()
    meta.setdefault("digiasset_op_kind", op_kind)

    tx = WalletTransaction(
        id=tx_id,
        kind=TxKind.DIGIASSET,
        wallet_id=req.wallet_id,
        account_id=req.account_id,
        outputs=[],
        fee=FeeEstimate(),
        status=TxStatus.DRAFT,
        description=req.description or f"DigiAsset {op_kind}",
        meta=meta,
    )
    return tx


def build_enigmatic_message_skeleton(
    tx_id: str,
    req: TxBuildRequest,
) -> WalletTransaction:
    """
    Skeleton for an Enigmatic Layer-0 message transaction.

    Enigmatic dialect planning + UTXO layout will be handled in the
    Enigmatic module; here we only mark intent for Guardian / Risk.
    """
    meta = req.as_meta()
    meta.setdefault("enigmatic", True)

    tx = WalletTransaction(
        id=tx_id,
        kind=TxKind.ENIGMATIC_MESSAGE,
        wallet_id=req.wallet_id,
        account_id=req.account_id,
        outputs=[],
        fee=FeeEstimate(),
        status=TxStatus.DRAFT,
        description=req.description or "Enigmatic message",
        meta=meta,
    )
    return tx
