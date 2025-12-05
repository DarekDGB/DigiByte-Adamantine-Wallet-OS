"""
DigiAssetsEngine – high-level orchestration for DigiByte assets & NFTs.

This module does NOT talk directly to Android/iOS/Web UI.
Instead, it is used by wallet_service.py (and other orchestrators) to:

  - describe an asset operation (mint / transfer / burn)
  - run basic validation and policy checks
  - delegate to:
        * GuardianAdapter       (policy / approvals)
        * NodeClient / RPC      (UTXO + transaction building, later)
        * index / metadata      (future: on-disk index, galleries, etc.)

The goal here is to define clear, testable interfaces so that
mobile and web implementations can be generated or ported later.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

from core.guardian_wallet.guardian_adapter import (
    GuardianAdapter,
    GuardianDecision,
)
from core.node.node_client import NodeClient


# ---------------------------------------------------------------------------
# Core types
# ---------------------------------------------------------------------------


class AssetOpKind(str, Enum):
    """High-level operation kind for DigiAssets."""

    MINT = "mint"
    TRANSFER = "transfer"
    BURN = "burn"


@dataclass
class AssetId:
    """
    Logical asset identifier.

    In real DigiAssets this is usually derived from an issuing txid
    + index, but for the architecture we model it as a simple string.
    """

    id: str


@dataclass
class AssetAmount:
    """
    Amount wrapper to make intent explicit and future-proof
    (e.g. decimals, fixed-point, etc.).
    """

    units: int  # smallest indivisible units of the asset


@dataclass
class AssetOperation:
    """
    A single asset operation request coming from wallet flows.

    This is what wallet_service.py will build and pass into DigiAssetsEngine.
    """

    op: AssetOpKind
    wallet_id: str
    account_id: str

    asset_id: Optional[AssetId]  # None for first-time mint
    amount: AssetAmount

    # Optional fields for richer flows
    to_address: Optional[str] = None
    metadata: Dict[str, Any] = None
    memo: Optional[str] = None


@dataclass
class AssetEngineResult:
    """
    Result of attempting an asset operation at the engine level.

    The engine does *not* broadcast transactions itself. Instead, it
    returns enough information for higher layers to decide what to do.
    """

    ok: bool
    guardian: GuardianDecision
    # In a full implementation this would include tx hex, fee estimate, etc.
    details: Dict[str, Any]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class DigiAssetsEngine:
    """
    High-level orchestrator for DigiAssets mint / transfer / burn.

    Responsibilities (architecture level):

      - Accept well-formed AssetOperation objects.
      - Apply cheap, synchronous validation (required fields, ranges).
      - Ask GuardianAdapter whether this operation is allowed / needs approval.
      - Prepare a response that wallet_service.py can act on.

    It deliberately does NOT:

      - maintain its own UTXO or database (that can be added later)
      - build final DigiByte tx bytes (delegated to lower-level builders)
      - manage UI / prompts
    """

    def __init__(self, node_client: NodeClient, guardian: GuardianAdapter) -> None:
        self._node = node_client
        self._guardian = guardian

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_operation(self, op: AssetOperation) -> AssetEngineResult:
        """
        Entry point for all asset flows.

        - validates the operation
        - runs Guardian policy checks
        - returns a structured result

        The actual transaction construction / submission is left
        to higher layers (wallet_service.py, platform-specific code).
        """
        errors: List[str] = []

        self._basic_validate(op, errors)
        if errors:
            # Guardian was never consulted; this is a local validation failure.
            dummy_guardian = self._make_validation_failure_decision(errors)
            return AssetEngineResult(
                ok=False,
                guardian=dummy_guardian,
                details={"errors": errors, "stage": "validation"},
            )

        guardian_decision = self._evaluate_guardian(op)

        if guardian_decision.is_blocked():
            return AssetEngineResult(
                ok=False,
                guardian=guardian_decision,
                details={"stage": "guardian_block"},
            )

        if guardian_decision.needs_approval():
            # Higher layers are responsible for presenting approval UI
            # and only proceeding once approvals are granted.
            return AssetEngineResult(
                ok=False,
                guardian=guardian_decision,
                details={"stage": "guardian_pending"},
            )

        # At this point, from Guardian's perspective, we are allowed.
        # Future: we would build a DigiByte transaction template here.
        tx_preview = self._build_tx_preview(op)

        return AssetEngineResult(
            ok=True,
            guardian=guardian_decision,
            details={
                "stage": "ready",
                "tx_preview": tx_preview,
            },
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _basic_validate(op: AssetOperation, errors: List[str]) -> None:
        """Cheap synchronous validation, no network access."""
        if op.amount.units <= 0:
            errors.append("amount_must_be_positive")

        if op.op in {AssetOpKind.TRANSFER, AssetOpKind.BURN} and op.asset_id is None:
            errors.append("asset_id_required_for_transfer_or_burn")

        if op.op == AssetOpKind.TRANSFER and not op.to_address:
            errors.append("to_address_required_for_transfer")

        # Additional rules can be added as the spec matures.

    def _evaluate_guardian(self, op: AssetOperation) -> GuardianDecision:
        """
        Ask GuardianAdapter for a policy decision.

        We map AssetOpKind into the existing RuleAction space using
        the adapter's DigiAsset helper.
        """
        op_kind_str = op.op.value  # "mint" / "transfer" / "burn"

        meta: Dict[str, Any] = {
            "asset_id": op.asset_id.id if op.asset_id else None,
            "op_kind": op_kind_str,
            "to_address": op.to_address,
            "memo": op.memo,
        }

        return self._guardian.evaluate_digiasset_op(
            wallet_id=op.wallet_id,
            account_id=op.account_id,
            value_units=op.amount.units,
            op_kind=op_kind_str,
            description=f"DigiAsset {op_kind_str}",
            meta=meta,
        )

    @staticmethod
    def _make_validation_failure_decision(errors: List[str]) -> GuardianDecision:
        """
        Construct a synthetic GuardianDecision used when validation fails
        before Guardian is even consulted.
        """
        from core.guardian_wallet.models import GuardianVerdict

        return GuardianDecision(
            verdict=GuardianVerdict.BLOCK,
            approval_request=None,  # no approval possible – invalid op
        )

    @staticmethod
    def _build_tx_preview(op: AssetOperation) -> Dict[str, Any]:
        """
        Placeholder for future tx construction.

        For now we just surface a preview structure that higher layers
        can log or display in tests.
        """
        return {
            "op": op.op.value,
            "wallet_id": op.wallet_id,
            "account_id": op.account_id,
            "asset_id": op.asset_id.id if op.asset_id else None,
            "amount_units": op.amount.units,
            "to_address": op.to_address,
            "memo": op.memo,
        }
