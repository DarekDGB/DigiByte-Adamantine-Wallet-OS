"""
Guardian Adapter

Thin adapter between wallet flows (send, DigiAssets, DigiDollar, etc.)
and the GuardianEngine.

Wallet / DD / DigiAssets code should NOT construct rules or interpret
Guardian internals directly. Instead, they call these helpers with
high-level parameters and receive:

    GuardianDecision

This keeps the rest of the codebase simple and makes it easy to evolve
Guardian over time without touching every flow.

Typical usage from a send flow:

    adapter = GuardianAdapter(engine)
    decision = adapter.evaluate_send_dgb(
        wallet_id="w1",
        account_id="a1",
        value_dgb=50_000,  # minor units or absolute units, per convention
        description="user send",
    )

    if decision.is_allowed():
        ... proceed ...
    elif decision.needs_approval():
        ... show guardian approval UI ...
    elif decision.is_blocked():
        ... show blocked message ...
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict, Any

from .engine import GuardianEngine, ActionContext, GuardianVerdict
from .models import (
    RuleAction,
    ApprovalRequest,
)


@dataclass
class GuardianDecision:
    """
    A small view object for wallet / UI layers.

    It wraps the low-level (verdict, ApprovalRequest) pair into a more
    convenient shape that is easy to serialise / send to UI clients.
    """
    verdict: GuardianVerdict
    approval_request: Optional[ApprovalRequest]

    def needs_approval(self) -> bool:
        return self.verdict == GuardianVerdict.REQUIRE_APPROVAL

    def is_allowed(self) -> bool:
        return self.verdict == GuardianVerdict.ALLOW

    def is_blocked(self) -> bool:
        return self.verdict == GuardianVerdict.BLOCK


class GuardianAdapter:
    """
    High-level adapter that knows how to:

      - map wallet actions into Guardian ActionContext
      - pick appropriate RuleAction
      - attach human-readable descriptions and tags

    It does not know about concrete UI; it just returns GuardianDecision.
    """

    def __init__(self, engine: GuardianEngine):
        self._engine = engine

    # ------------------------------------------------------------------
    # Public helpers for common flows
    # ------------------------------------------------------------------

    def evaluate_send_dgb(
        self,
        wallet_id: str,
        account_id: str,
        value_dgb: Decimal | int | float,
        description: str = "DGB send",
        meta: Optional[Dict[str, Any]] = None,
    ) -> GuardianDecision:
        """
        Evaluate a standard DGB send flow against Guardian rules.

        `value_dgb` should follow the same convention used in rules
        (e.g. if rules are defined in "DGB units", pass DGB; if in
        "minor units", pass the same minor units).
        """
        value_int = int(value_dgb) if not isinstance(value_dgb, int) else value_dgb

        ctx = ActionContext(
            action=RuleAction.SEND,
            wallet_id=wallet_id,
            account_id=account_id,
            value=value_int,
            description=description,
            meta=meta or {},
        )

        verdict, approval = self._engine.evaluate(ctx)
        return GuardianDecision(verdict=verdict, approval_request=approval)

    def evaluate_mint_dd(
        self,
        wallet_id: str,
        account_id: str,
        dgb_value_in: Decimal | int | float,
        description: str = "Mint DigiDollar (DD)",
        meta: Optional[Dict[str, Any]] = None,
    ) -> GuardianDecision:
        """
        Evaluate a DigiDollar mint (DGB -> DD) before executing.

        This assumes Guardian rules include a RuleAction for minting DD,
        or they fall back to SEND.
        """
        value_int = int(dgb_value_in) if not isinstance(dgb_value_in, int) else dgb_value_in
        action = getattr(RuleAction, "MINT_DD", RuleAction.SEND)

        ctx = ActionContext(
            action=action,
            wallet_id=wallet_id,
            account_id=account_id,
            value=value_int,
            description=description,
            meta=meta or {},
        )

        verdict, approval = self._engine.evaluate(ctx)
        return GuardianDecision(verdict=verdict, approval_request=approval)

    def evaluate_redeem_dd(
        self,
        wallet_id: str,
        account_id: str,
        dd_amount: Decimal | int | float,
        description: str = "Redeem DigiDollar (DD)",
        meta: Optional[Dict[str, Any]] = None,
    ) -> GuardianDecision:
        """
        Evaluate a DigiDollar redeem (DD -> DGB) before executing.

        The numeric convention for `dd_amount` should match how rules
        are expressed (e.g. DD units).
        """
        value_int = int(dd_amount) if not isinstance(dd_amount, int) else dd_amount
        action = getattr(RuleAction, "REDEEM_DD", RuleAction.SEND)

        ctx = ActionContext(
            action=action,
            wallet_id=wallet_id,
            account_id=account_id,
            value=value_int,
            description=description,
            meta=meta or {},
        )

        verdict, approval = self._engine.evaluate(ctx)
        return GuardianDecision(verdict=verdict, approval_request=approval)

    def evaluate_digiasset_op(
        self,
        wallet_id: str,
        account_id: str,
        value_units: int,
        op_kind: str,
        description: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> GuardianDecision:
        """
        Evaluate a generic DigiAsset operation (mint / transfer / burn).

        `op_kind` can be one of: "mint", "transfer", "burn".
        It is mapped into appropriate RuleAction if present, otherwise falls
        back to SEND.
        """
        action = self._map_digiasset_action(op_kind)

        ctx = ActionContext(
            action=action,
            wallet_id=wallet_id,
            account_id=account_id,
            value=value_units,
            description=description,
            meta=meta or {},
        )

        verdict, approval = self._engine.evaluate(ctx)
        return GuardianDecision(verdict=verdict, approval_request=approval)

    def evaluate_enigmatic_message(
        self,
        wallet_id: str,
        account_id: str,
        value_dgb: int,
        description: str = "Enigmatic Layer-0 message",
        meta: Optional[Dict[str, Any]] = None,
    ) -> GuardianDecision:
        """
        Evaluate an Enigmatic Layer-0 message flow.

        Some deployments may choose to guard certain Enigmatic operations
        (e.g. high-value messages, governance actions) with Guardian rules.
        """
        action = getattr(RuleAction, "ENIGMATIC", RuleAction.SEND)

        ctx = ActionContext(
            action=action,
            wallet_id=wallet_id,
            account_id=account_id,
            value=value_dgb,
            description=description,
            meta=meta or {},
        )

        verdict, approval = self._engine.evaluate(ctx)
        return GuardianDecision(verdict=verdict, approval_request=approval)

    # ------------------------------------------------------------------
    # DigiAsset-specific convenience wrappers
    # ------------------------------------------------------------------

    def evaluate_asset_creation(
        self,
        wallet_id: str,
        account_id: str,
        description: str = "Create DigiAsset",
        meta: Optional[Dict[str, Any]] = None,
    ) -> GuardianDecision:
        """
        Evaluate a DigiAsset *creation* (no concrete amount yet).

        We treat creation as a special-case operation and pass value 0,
        so rules that care only about 'creating new assets' can be keyed
        on the RuleAction type rather than the numeric value.
        """
        return self.evaluate_digiasset_op(
            wallet_id=wallet_id,
            account_id=account_id,
            value_units=0,
            op_kind="mint",
            description=description,
            meta=meta or {},
        )

    def evaluate_asset_issuance(
        self,
        wallet_id: str,
        account_id: str,
        asset_id: str,
        amount: int,
        description: str = "Issue DigiAsset units",
        meta: Optional[Dict[str, Any]] = None,
    ) -> GuardianDecision:
        """
        Evaluate an *issuance* (or extra mint) of an existing DigiAsset.
        """
        meta_merged = {"asset_id": asset_id, **(meta or {})}
        return self.evaluate_digiasset_op(
            wallet_id=wallet_id,
            account_id=account_id,
            value_units=amount,
            op_kind="mint",
            description=description,
            meta=meta_merged,
        )

    def evaluate_asset_transfer(
        self,
        wallet_id: str,
        account_id: str,
        asset_id: str,
        amount: int,
        description: str = "Transfer DigiAsset units",
        meta: Optional[Dict[str, Any]] = None,
    ) -> GuardianDecision:
        """
        Evaluate a DigiAsset transfer between addresses.
        """
        meta_merged = {"asset_id": asset_id, **(meta or {})}
        return self.evaluate_digiasset_op(
            wallet_id=wallet_id,
            account_id=account_id,
            value_units=amount,
            op_kind="transfer",
            description=description,
            meta=meta_merged,
        )

    def evaluate_asset_burn(
        self,
        wallet_id: str,
        account_id: str,
        asset_id: str,
        amount: int,
        description: str = "Burn DigiAsset units",
        meta: Optional[Dict[str, Any]] = None,
    ) -> GuardianDecision:
        """
        Evaluate a DigiAsset burn (destroying units).
        """
        meta_merged = {"asset_id": asset_id, **(meta or {})}
        return self.evaluate_digiasset_op(
            wallet_id=wallet_id,
            account_id=account_id,
            value_units=amount,
            op_kind="burn",
            description=description,
            meta=meta_merged,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_digiasset_action(op_kind: str) -> RuleAction:
        """
        Map a generic DigiAsset operation string into a RuleAction.

        Falls back to SEND if a more specific action is not available
        in the current RuleAction enum.
        """
        op = op_kind.lower().strip()

        if op == "mint" and hasattr(RuleAction, "MINT_ASSET"):
            return getattr(RuleAction, "MINT_ASSET")
        if op == "transfer" and hasattr(RuleAction, "TRANSFER_ASSET"):
            return getattr(RuleAction, "TRANSFER_ASSET")
        if op == "burn" and hasattr(RuleAction, "BURN_ASSET"):
            return getattr(RuleAction, "BURN_ASSET")

        # Fallback: treat as generic SEND-like action
        return RuleAction.SEND
