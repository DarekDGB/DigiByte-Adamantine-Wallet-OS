"""
Transaction Classifier — EQC Equilibrium Confirmation

Extracts transaction-related signals from EQCContext.
No decisions. No thresholds enforcement. Just signals.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from __future__ import annotations

from typing import Dict, Any

from .base import Classifier, ClassificationResult
from ..context import EQCContext


class TransactionClassifier(Classifier):
    """
    Classifies transaction-level risk signals.
    """

    name = "transaction"

    def classify(self, ctx: EQCContext) -> ClassificationResult:
        signals: Dict[str, Any] = {}

        action = ctx.action.action.lower()
        amount = ctx.action.amount or 0

        # Basic action flags
        signals["is_send"] = action == "send"
        signals["is_mint"] = action == "mint"
        signals["is_redeem"] = action == "redeem"

        # Amount-related facts (policy decides thresholds)
        signals["amount"] = amount
        signals["has_amount"] = ctx.action.amount is not None

        # Recipient presence (policy decides what "new" means)
        signals["has_recipient"] = ctx.action.recipient is not None
        signals["recipient"] = ctx.action.recipient

        # Network fee observation
        signals["fee_rate"] = ctx.network.fee_rate
        signals["has_fee_rate"] = ctx.network.fee_rate is not None

        # Asset facts
        signals["asset"] = ctx.action.asset

        return ClassificationResult(
            name=self.name,
            signals=signals,
        )
