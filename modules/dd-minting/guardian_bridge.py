# modules/dd_minting/guardian_bridge.py

"""
Bridge between DigiDollar (DD) mint/redeem flows and Guardian Wallet.

This module adapts the GuardianAdapter interface into the DDGuardianService
protocol used by DDMintingEngine.

Flow:

    DDMintingEngine
        -> DDGuardianService.assess_dd_action(...)
            -> GuardianAdapter.evaluate_mint_dd / evaluate_redeem_dd(...)
                -> GuardianEngine / rules
                -> GuardianDecision
            -> DDGuardianAssessment (LOW / MEDIUM / BLOCKED)

This keeps the DD engine independent from Guardian internals and lets
Guardian evolve without changing DD business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from decimal import Decimal

from modules.dd_minting.models import (
    DGBAmount,
    DDAmount,
    FlowKind,
    DDGuardianAssessment,
    DDActionRiskLevel,
)
from modules.dd_minting.engine import DDGuardianService

from core.guardian_wallet.guardian_adapter import GuardianAdapter
from core.guardian_wallet.engine import GuardianVerdict


@dataclass
class DDGuardianBridge(DDGuardianService):
    """
    Implementation of DDGuardianService that delegates to GuardianAdapter.

    This assumes that:

      - Guardian rules include appropriate RuleAction entries for DD
        mint/redeem (MINT_DD, REDEEM_DD) OR they fall back to SEND.

      - A specific (wallet_id, account_id) pair is used for DD flows,
        typically the user's main spending account in the wallet.
    """

    guardian_adapter: GuardianAdapter
    wallet_id: str
    account_id: str

    def assess_dd_action(
        self,
        flow: FlowKind,
        dgb_amount: DGBAmount,
        dd_amount: DDAmount,
        context: Optional[Dict[str, str]] = None,
    ) -> DDGuardianAssessment:
        """
        Evaluate a DD mint/redeem operation using Guardian.

        We map:

          - FlowKind.MINT   -> adapter.evaluate_mint_dd(...)
          - FlowKind.REDEEM -> adapter.evaluate_redeem_dd(...)

        Then translate GuardianVerdict into a DDActionRiskLevel:

          - ALLOW            -> LOW
          - REQUIRE_APPROVAL -> MEDIUM
          - BLOCK            -> BLOCKED
        """
        context = context or {}

        if flow == FlowKind.MINT:
            decision = self.guardian_adapter.evaluate_mint_dd(
                wallet_id=self.wallet_id,
                account_id=self.account_id,
                dgb_value_in=dgb_amount.dgb,
                description="Mint DigiDollar (DD)",
                meta={"flow": "dd_mint", **context},
            )
        elif flow == FlowKind.REDEEM:
            decision = self.guardian_adapter.evaluate_redeem_dd(
                wallet_id=self.wallet_id,
                account_id=self.account_id,
                dd_amount=dd_amount.dd,
                description="Redeem DigiDollar (DD)",
                meta={"flow": "dd_redeem", **context},
            )
        else:
            # For future flows, treat as generic and fall back to mint semantics.
            decision = self.guardian_adapter.evaluate_mint_dd(
                wallet_id=self.wallet_id,
                account_id=self.account_id,
                dgb_value_in=dgb_amount.dgb,
                description=f"DD action ({flow.value})",
                meta={"flow": f"dd_{flow.value.lower()}", **context},
            )

        level = self._map_verdict_to_level(decision.verdict)

        # Short, human-readable summary for logs / UI
        if level == DDActionRiskLevel.LOW:
            msg = "Guardian allowed DigiDollar operation."
        elif level == DDActionRiskLevel.MEDIUM:
            msg = "Guardian requires additional approvals for DigiDollar operation."
        elif level == DDActionRiskLevel.BLOCKED:
            msg = "Guardian blocked DigiDollar operation by policy."
        else:
            msg = "Guardian returned an unknown decision for DigiDollar operation."

        return DDGuardianAssessment(
            level=level,
            message=msg,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _map_verdict_to_level(verdict: GuardianVerdict) -> DDActionRiskLevel:
        """
        Translate Guardian verdict into DDActionRiskLevel.

        This is intentionally simple in v1. Future versions may add more
        granularity (e.g. use risk scores or specific rule types).
        """
        if verdict == GuardianVerdict.ALLOW:
            return DDActionRiskLevel.LOW
        if verdict == GuardianVerdict.REQUIRE_APPROVAL:
            return DDActionRiskLevel.MEDIUM
        if verdict == GuardianVerdict.BLOCK:
            return DDActionRiskLevel.BLOCKED

        # Fallback for unknown verdict types
        return DDActionRiskLevel.MEDIUM
