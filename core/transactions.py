"""
core/transactions.py

Shared transaction models for the Adamantine Wallet.

This module defines neutral, chain-agnostic data structures that all
wallet flows can use:

- plain DGB sends
- DigiAssets transfers
- DigiDollar mint / redeem

It is intentionally *not* a full DigiByte transaction encoder/decoder.
That work will live in chain-specific modules or bindings. Here we just
model what the wallet needs to:

- track what the user is trying to do
- estimate fees
- prepare data for signing / broadcasting
- surface clear information to the UI
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class TxKind(str, Enum):
    """High-level classification of a wallet transaction."""

    DGB_SEND = "dgb_send"
    DIGIASSET = "digiasset"
    DIGIDOLLAR_MINT = "digidollar_mint"
    DIGIDOLLAR_REDEEM = "digidollar_redeem"
    ENIGMATIC_MESSAGE = "enigmatic_message"


class TxStatus(str, Enum):
    """Lifecycle state of a wallet transaction."""

    DRAFT = "draft"          # constructed, not signed
    SIGNED = "signed"        # fully signed locally
    BROADCAST = "broadcast"  # sent to the network
    CONFIRMED = "confirmed"  # included in sufficient blocks
    FAILED = "failed"        # rejected / not accepted
    CANCELLED = "cancelled"  # abandoned by the wallet/user


@dataclass
class UtxoInput:
    """
    A single UTXO being spent by this wallet transaction.

    This is a logical view; chain-specific serializers will map it into
    raw DigiByte transaction inputs.
    """

    txid: str
    vout: int
    value_sats: int
    address: Optional[str] = None

    def __post_init__(self) -> None:
        if self.value_sats < 0:
            raise ValueError("value_sats must be non-negative")


@dataclass
class PaymentOutput:
    """
    An output of the wallet transaction.

    For standard DGB transfers this is just a value + address.
    For DigiAssets / DigiDollar, `asset_id` and metadata may be used.
    """

    address: str
    value_sats: int = 0
    asset_id: Optional[str] = None  # DigiAsset / DD identifier, if relevant
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.value_sats < 0:
            raise ValueError("value_sats must be non-negative")


@dataclass
class FeeEstimate:
    """
    Simple fee information attached to a wallet transaction.

    `rate` is usually in sats/vbyte; `total_sats` is the absolute fee.
    """

    rate_sats_per_vbyte: Optional[Decimal] = None
    total_sats: Optional[int] = None

    def ensure_total(self, vsize: Optional[int] = None) -> Optional[int]:
        """
        Optionally compute `total_sats` from `rate_sats_per_vbyte` and
        an estimated virtual size, if not already set.

        Returns the resolved total_sats.
        """
        if self.total_sats is not None:
            return self.total_sats
        if self.rate_sats_per_vbyte is None or vsize is None:
            return None

        total = int(self.rate_sats_per_vbyte * Decimal(vsize))
        self.total_sats = total
        return total


@dataclass
class WalletTransaction:
    """
    High-level wallet transaction model.

    This is what the wallet core and UI talk about. It can later be
    turned into a raw DigiByte transaction by chain-specific code.
    """

    id: str
    kind: TxKind
    wallet_id: str
    account_id: str

    inputs: List[UtxoInput] = field(default_factory=list)
    outputs: List[PaymentOutput] = field(default_factory=list)

    change_address: Optional[str] = None
    fee: FeeEstimate = field(default_factory=FeeEstimate)

    status: TxStatus = TxStatus.DRAFT
    description: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    # Optional references into other modules
    guardian_request_id: Optional[str] = None
    risk_summary_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def total_input_sats(self) -> int:
        """Sum of all input values."""
        return sum(i.value_sats for i in self.inputs)

    def total_output_sats(self) -> int:
        """Sum of all *non-change* outputs."""
        return sum(o.value_sats for o in self.outputs)

    def implied_fee_sats(self) -> Optional[int]:
        """
        Compute fee from inputs - outputs if both are known.

        If inputs or outputs are empty, returns None.
        """
        if not self.inputs or not self.outputs:
            return None
        return self.total_input_sats() - self.total_output_sats()

    def effective_fee_sats(self) -> Optional[int]:
        """
        Prefer an explicit fee.total_sats; otherwise fall back to an
        implied fee from inputs/outputs.
        """
        if self.fee.total_sats is not None:
            return self.fee.total_sats
        return self.implied_fee_sats()

    def mark_signed(self) -> None:
        self.status = TxStatus.SIGNED

    def mark_broadcast(self) -> None:
        self.status = TxStatus.BROADCAST

    def mark_confirmed(self) -> None:
        self.status = TxStatus.CONFIRMED

    def mark_failed(self, reason: str) -> None:
        self.status = TxStatus.FAILED
        self.meta.setdefault("failure_reasons", []).append(reason)

    def mark_cancelled(self, reason: str) -> None:
        self.status = TxStatus.CANCELLED
        self.meta.setdefault("cancel_reasons", []).append(reason)
