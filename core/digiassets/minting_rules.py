"""
DigiAssets minting rules for Adamantine Wallet.

This module defines *policy-level* rules for creating new DigiAssets supply.
It is protocol-agnostic: we are not encoding raw DigiAssets transactions here,
only the logical guardrails around who may mint, how much, and under which
conditions.

This keeps all "hard" constraints in one place so that:

- the Guardian Wallet can inspect / enforce them
- UIs can explain *why* a mint is allowed or rejected
- different assets can have different policies without changing core code
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set


# ---------------------------------------------------------------------------
# Core policy model
# ---------------------------------------------------------------------------


@dataclass
class MintPolicy:
    """
    High-level, human-readable minting policy for a single DigiAsset.

    This is intentionally simple and can be extended over time.
    """

    asset_id: str

    # Optional hard cap on total supply (across all mints)
    max_supply: Optional[int] = None

    # Optional limit per single mint operation
    per_mint_limit: Optional[int] = None

    # If set, only these addresses may initiate a mint.
    # These are DigiByte addresses *or* higher-level identifiers
    # (e.g. Guardian identities) depending on integration.
    allowed_minters: Set[str] = field(default_factory=set)

    # Whether the Guardian Wallet must sign off before broadcast.
    require_guardian_approval: bool = False

    # Optional "soft" flags the UI can use to present warnings.
    # Example: {"regulatory": "restricted-jurisdictions", "kyc": "required"}
    flags: Dict[str, str] = field(default_factory=dict)

    # Optional schema hints for metadata keys expected at mint time.
    # Example: {"name": "string", "ticker": "string", "url": "uri"}
    metadata_schema: Dict[str, str] = field(default_factory=dict)


@dataclass
class MintContext:
    """
    Dynamic context used when evaluating a mint request.
    """

    # Current confirmed supply before this mint (units of the asset).
    current_supply: int

    # Whether guardian approval has been granted (if required).
    guardian_approved: bool = False


@dataclass
class MintRequest:
    """
    Logical description of a mint the wallet would like to perform.
    """

    asset_id: str
    amount: int
    minter_address: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class MintDecision:
    """
    Result of applying a MintPolicy + MintContext to a MintRequest.

    - `allowed` tells the caller whether it is safe to proceed.
    - `errors` contains hard reasons why minting should be blocked.
    - `warnings` are soft concerns that the UI may show but do not
       prevent minting.
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
# Validation logic
# ---------------------------------------------------------------------------


def validate_mint(
    policy: MintPolicy,
    context: MintContext,
    request: MintRequest,
) -> MintDecision:
    """
    Evaluate whether a mint request is allowed under a given policy and context.

    This function performs *pure* validation; it does not touch the network
    or build raw transactions.
    """

    decision = MintDecision(allowed=True)

    # 1. Asset id consistency
    if request.asset_id != policy.asset_id:
        decision.add_error(
            f"Mint request asset_id={request.asset_id} does not match policy asset_id={policy.asset_id}."
        )
        return decision

    # 2. Non-negative, non-zero amount
    if request.amount <= 0:
        decision.add_error("Mint amount must be positive.")
        return decision

    # 3. Per-mint limit
    if policy.per_mint_limit is not None and request.amount > policy.per_mint_limit:
        decision.add_error(
            f"Mint amount {request.amount} exceeds per-mint limit {policy.per_mint_limit}."
        )

    # 4. Supply cap
    if policy.max_supply is not None:
        projected_supply = context.current_supply + request.amount
        if projected_supply > policy.max_supply:
            decision.add_error(
                f"Mint would exceed max supply {policy.max_supply} "
                f"(current={context.current_supply}, requested={request.amount})."
            )

    # 5. Allowed minters
    if policy.allowed_minters:
        if request.minter_address not in policy.allowed_minters:
            decision.add_error(
                f"Minter {request.minter_address} is not in the allowed_minters set."
            )

    # 6. Guardian approval (if required)
    if policy.require_guardian_approval and not context.guardian_approved:
        decision.add_error(
            "Guardian approval required by mint policy but not yet granted."
        )

    # 7. Metadata schema hints (soft check)
    if policy.metadata_schema:
        for key in policy.metadata_schema.keys():
            if key not in request.metadata:
                decision.add_warning(
                    f"Metadata key '{key}' is missing (expected by policy schema)."
                )

    return decision


# ---------------------------------------------------------------------------
# Helper for computing new supply after a successful mint
# ---------------------------------------------------------------------------


def project_new_supply(context: MintContext, request: MintRequest) -> int:
    """
    Return the hypothetical new confirmed supply *if* the mint were to succeed.
    """

    return context.current_supply + request.amount
