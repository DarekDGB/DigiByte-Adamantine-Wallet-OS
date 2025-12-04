# modules/digiassets/guardian_bridge.py

"""
Guardian bridge for DigiAssets.

This module connects DigiAssets lifecycle events (create, issue, transfer,
burn) with the Guardian Wallet policy engine using the GuardianAdapter.

Purpose:
    - Every DigiAsset operation is evaluated BEFORE execution.
    - Guardian rules can block, allow, or require approvals.
    - Wallet Core does NOT need to understand Guardian internals.

This acts exactly like the DDGuardianBridge but specialized for DigiAssets.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
from decimal import Decimal

from modules.digiassets.models import (
    AssetActionKind,
    AssetAmount,
    AssetGuardianAssessment,
    AssetRiskLevel,
)
from core.guardian_wallet.guardian_adapter import GuardianAdapter
from core.guardian_wallet.engine import GuardianVerdict


@dataclass
class DigiAssetsGuardianBridge:
    """
    Bridge between DigiAssets module and GuardianAdapter.

    wallet_id / account_id:
        Identify which wallet and account the action belongs to.
    """

    guardian_adapter: GuardianAdapter
    wallet_id: str
    account_id: str

    def assess_asset_action(
        self,
        action: AssetActionKind,
        asset_id: Optional[str],
        amount: Optional[AssetAmount],
        context: Optional[Dict[str, str]] = None,
    ) -> AssetGuardianAssessment:
        """
        Run Guardian evaluation depending on asset action type.

        Supported:
            - CREATE
            - ISSUE
            - TRANSFER
            - BURN

        We translate Guardian verdicts into AssetRiskLevel:
            ALLOW            -> LOW
            REQUIRE_APPROVAL -> MEDIUM
            BLOCK            -> BLOCKED
        """
        context = context or {}

        # -------------------------------
        #  Map asset action to GuardianAdapter call
        # -------------------------------
        if action == AssetActionKind.CREATE:
            decision = self.guardian_adapter.evaluate_asset_creation(
                wallet_id=self.wallet_id,
                account_id=self.account_id,
                description=f"Create DigiAsset {asset_id}",
                meta={"flow": "asset_create", **context},
            )

        elif action == AssetActionKind.ISSUE:
            decision = self.guardian_adapter.evaluate_asset_issuance(
                wallet_id=self.wallet_id,
                account_id=self.account_id,
                asset_id=asset_id,
                amount=amount.units if amount else 0,
                description=f"Issue DigiAsset {asset_id}",
                meta={"flow": "asset_issue", **context},
            )

        elif action == AssetActionKind.TRANSFER:
            decision = self.guardian_adapter.evaluate_asset_transfer(
                wallet_id=self.wallet_id,
                account_id=self.account_id,
                asset_id=asset_id,
                amount=amount.units if amount else 0,
                description=f"Transfer DigiAsset {asset_id}",
                meta={"flow": "asset_transfer", **context},
            )

        elif action == AssetActionKind.BURN:
            decision = self.guardian_adapter.evaluate_asset_burn(
                wallet_id=self.wallet_id,
                account_id=self.account_id,
                asset_id=asset_id,
                amount=amount.units if amount else 0,
                description=f"Burn DigiAsset {asset_id}",
                meta={"flow": "asset_burn", **context},
            )

        else:
            # fallback — treat unknown asset actions as transfer
            decision = self.guardian_adapter.evaluate_asset_transfer(
                wallet_id=self.wallet_id,
                account_id=self.account_id,
                asset_id=asset_id,
                amount=amount.units if amount else 0,
                description=f"Asset action ({action.value})",
                meta={"flow": f"asset_{action.value.lower()}", **context},
            )

        # -------------------------------
        # Map Guardian verdict to internal risk level
        # -------------------------------
        level = self._map_verdict(decision.verdict)

        if level == AssetRiskLevel.LOW:
            msg = "Guardian allowed DigiAsset operation."
        elif level == AssetRiskLevel.MEDIUM:
            msg = "Guardian requires additional approvals for DigiAsset operation."
        else:
            msg = "Guardian blocked this DigiAsset operation."

        return AssetGuardianAssessment(
            level=level,
            message=msg,
        )

    # -------------------------------
    # Internals
    # -------------------------------

    @staticmethod
    def _map_verdict(verdict: GuardianVerdict) -> AssetRiskLevel:
        if verdict == GuardianVerdict.ALLOW:
            return AssetRiskLevel.LOW
        if verdict == GuardianVerdict.REQUIRE_APPROVAL:
            return AssetRiskLevel.MEDIUM
        if verdict == GuardianVerdict.BLOCK:
            return AssetRiskLevel.BLOCKED
        return AssetRiskLevel.MEDIUM
