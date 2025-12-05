"""
Guardian Wallet – Policy Evaluation

This module takes:
  * a GuardianConfig (rules loaded from YAML)
  * a description of the pending wallet operation

and returns a simple decision the wallet can act on, plus the list of
requirements that must be satisfied (PIN, biometric, guardian approval, etc.).

The goal is to keep this logic **pure and testable** so that:
  - mobile / web clients can call it the same way
  - the risk engine can plug into it later if needed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional

from .guardian_config import GuardianConfig, GuardianRule, Requirement, SpendingLimit


Decision = Literal["allow", "require_auth", "require_guardian", "block"]


@dataclass
class OperationContext:
    """
    Description of a pending wallet operation.

    Fields are intentionally generic so the same structure can be used for:
      - DGB sends
      - DigiDollar mint / redeem
      - DigiAssets transfers
    """

    asset: str                # "DGB", "DD", "DGA" (for DigiAssets), etc.
    operation: str            # "send", "mint", "redeem", "transfer", ...
    amount: float             # nominal amount in the asset units

    # How much was already spent in the relevant time window, if known.
    # This lets us check rolling limits like "10k DGB per 24h".
    recent_window_spent: float = 0.0


@dataclass
class PolicyDecision:
    """
    Result of evaluating Guardian rules for a given operation.
    """

    decision: Decision
    """High-level decision the wallet should enforce."""

    reasons: List[str] = field(default_factory=list)
    """Human-readable reasons that can be surfaced in the UI or logs."""

    requirements: List[Requirement] = field(default_factory=list)
    """
    Concrete requirements that must be satisfied before proceeding,
    e.g. device PIN, biometric, guardian_approval.
    """

    rules_triggered: List[str] = field(default_factory=list)
    """IDs of the Guardian rules that contributed to this decision."""

    def requires_any_guardian(self) -> bool:
        """Convenience helper used by UI / higher-level logic."""
        return any(r.code == "guardian_approval" for r in self.requirements)


class GuardianPolicy:
    """
    Policy engine that interprets GuardianConfig rules for a single operation.

    This class does **not** talk to the network, wallet storage, or UI.
    It simply turns (config + operation context) into a PolicyDecision.
    """

    def __init__(self, config: GuardianConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, ctx: OperationContext) -> PolicyDecision:
        """
        Evaluate all Guardian rules that apply to the given operation.

        The algorithm is intentionally simple and explainable:
          1. Find matching rules for (asset, operation).
          2. For each rule, check spending limits and collect requirements.
          3. Combine everything into a single decision.

        More advanced risk scoring can be layered on top later.
        """
        asset = ctx.asset.upper()
        operation = ctx.operation.lower()

        matching_rules = self._config.rules_for_operation(asset=asset, operation=operation)

        if not matching_rules:
            # No Guardian rules apply – normal wallet behaviour.
            return PolicyDecision(
                decision="allow",
                reasons=["no_matching_rules"],
                requirements=[],
                rules_triggered=[],
            )

        reasons: List[str] = []
        requirements: List[Requirement] = []
        triggered: List[str] = []

        # Track escalation level
        highest: Decision = "allow"

        for rule in matching_rules:
            triggered.append(rule.id)

            # 1) Check spending limit, if present
            over_limit = self._check_spending_limit(rule, ctx)
            if over_limit:
                reasons.append(f"spending_limit:{rule.id}")
                # spending limit breach usually requires guardian approval
                highest = self._escalate(highest, "require_guardian")

            # 2) Collect requirements
            for req in rule.requirements:
                requirements.append(req)
                if req.code in {"guardian_approval", "out_of_band_confirmation"}:
                    highest = self._escalate(highest, "require_guardian")
                elif req.code in {"device_pin", "biometric"}:
                    highest = self._escalate(highest, "require_auth")

            # 3) Critical severity rules can force a block
            if rule.severity == "critical" and over_limit:
                highest = self._escalate(highest, "block")
                reasons.append(f"critical_block:{rule.id}")

        if not requirements and highest == "allow":
            reasons.append("rules_match_but_no_extra_requirements")

        return PolicyDecision(
            decision=highest,
            reasons=reasons,
            requirements=requirements,
            rules_triggered=triggered,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _escalate(current: Decision, new: Decision) -> Decision:
        """
        Escalate a decision to the more restrictive one.

        Order from weakest to strongest:
            allow < require_auth < require_guardian < block
        """
        order = ["allow", "require_auth", "require_guardian", "block"]
        if order.index(new) > order.index(current):
            return new
        return current

    @staticmethod
    def _check_spending_limit(rule: GuardianRule, ctx: OperationContext) -> bool:
        """
        True if the operation would exceed the rule's spending limit.
        If the rule has no spending limit, returns False.
        """
        sl: Optional[SpendingLimit] = rule.spending_limit
        if sl is None:
            return False

        projected = ctx.recent_window_spent + ctx.amount
        return projected > sl.max_amount
