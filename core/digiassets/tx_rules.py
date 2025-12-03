"""
DigiAssets transaction-level rules for Adamantine Wallet.

This module holds *generic* safety checks for DigiAssets operations at the
wallet layer:

- mint:    aligns with minting_rules.MintPolicy / MintContext
- transfer:basic balance + address sanity checks
- burn:    checks for valid burn targets and non-negative amounts

It does **not** parse raw DigiByte transactions – that lives in
`parsing.py`. Instead, this operates on higher-level intents that
the UI / parsing logic construct.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


# ---------------------------------------------------------------------------
# Common decision object
# ---------------------------------------------------------------------------


@dataclass
class TxDecision:
    """
    Generic decision object for DigiAssets operations.

    - `allowed` — whether the wallet should proceed.
    - `errors`  — hard reasons to block the tx.
    - `warnings` — soft notes the UI may show.
    """

    allowed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.allowed = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


# ---------------------------------------------------------------------------
# Transaction intent models
# ---------------------------------------------------------------------------


class DigiAssetTxType(Enum):
    """High-level operation type for DigiAssets."""

    MINT = auto()
    TRANSFER = auto()
    BURN = auto()


@dataclass
class TransferContext:
    """
    Context required to evaluate a transfer operation.

    The wallet can populate this from its own state.
    """

    asset_id: str
    spendable_balance: int  # confirmed + spendable
    # Optionally: unconfirmed, frozen, etc. (future extension)


@dataclass
class TransferRequest:
    """
    High-level description of an asset transfer.

    `from_address` and `to_address` are DigiByte addresses (or compatible
    encodings) in the current network.
    """

    asset_id: str
    amount: int
    from_address: str
    to_address: str


@dataclass
class BurnContext:
    """
    Context required to evaluate a burn.

    For now this mirrors TransferContext. We keep it separate to allow
    future burn-specific fields.
    """

    asset_id: str
    spendable_balance: int


@dataclass
class BurnRequest:
    """
    Description of a burn operation.

    `burn_target` is typically one of:
      - a recognised provably-unspendable "burn" address
      - a script template reserved for destroying supply
    The exact set of valid burn targets is configured by the wallet.
    """

    asset_id: str
    amount: int
    holder_address: str
    burn_target: str


# ---------------------------------------------------------------------------
# Transfer validation
# ---------------------------------------------------------------------------


def validate_transfer(
    ctx: TransferContext,
    req: TransferRequest,
    *,
    min_dust_amount: Optional[int] = None,
) -> TxDecision:
    """
    Validate a DigiAssets *transfer* at the wallet layer.

    This does not attempt protocol-level validation; it only enforces
    basic safety rules the wallet can know about up front.
    """

    decision = TxDecision(allowed=True)

    # 1. Asset id consistency
    if req.asset_id != ctx.asset_id:
        decision.add_error(
            f"Transfer asset_id={req.asset_id} does not match wallet asset_id={ctx.asset_id}."
        )
        return decision

    # 2. Positive amount
    if req.amount <= 0:
        decision.add_error("Transfer amount must be positive.")
        return decision

    # 3. Optional dust guard (UI can pass a chain-appropriate threshold)
    if min_dust_amount is not None and req.amount < min_dust_amount:
        decision.add_warning(
            f"Transfer amount {req.amount} is below suggested dust threshold {min_dust_amount}."
        )

    # 4. Balance check
    if req.amount > ctx.spendable_balance:
        decision.add_error(
            f"Insufficient asset balance. Have {ctx.spendable_balance}, "
            f"trying to send {req.amount}."
        )

    # 5. Basic address sanity
    if req.from_address == req.to_address:
        decision.add_warning("Sender and recipient addresses are identical.")

    return decision


# ---------------------------------------------------------------------------
# Burn validation
# ---------------------------------------------------------------------------


def validate_burn(
    ctx: BurnContext,
    req: BurnRequest,
    *,
    allowed_burn_targets: Optional[list[str]] = None,
) -> TxDecision:
    """
    Validate a DigiAssets *burn* operation.

    The wallet decides what constitutes a valid burn target by providing
    `allowed_burn_targets` – a list of addresses / scripts that are
    considered permanently unspendable.
    """

    decision = TxDecision(allowed=True)

    # 1. Asset id consistency
    if req.asset_id != ctx.asset_id:
        decision.add_error(
            f"Burn asset_id={req.asset_id} does not match wallet asset_id={ctx.asset_id}."
        )
        return decision

    # 2. Positive amount
    if req.amount <= 0:
        decision.add_error("Burn amount must be positive.")
        return decision

    # 3. Balance check
    if req.amount > ctx.spendable_balance:
        decision.add_error(
            f"Insufficient asset balance to burn. Have {ctx.spendable_balance}, "
            f"trying to burn {req.amount}."
        )

    # 4. Burn target allowlist (if provided)
    if allowed_burn_targets is not None and req.burn_target not in allowed_burn_targets:
        decision.add_error(
            f"Burn target {req.burn_target} is not in the configured set of allowed burn addresses."
        )

    # 5. Soft warning: burning to own address
    if req.holder_address == req.burn_target:
        decision.add_warning(
            "Burn target address is the same as the holder address; "
            "ensure this really is a burn script."
        )

    return decision
