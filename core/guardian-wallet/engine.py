"""
DigiByte Adamantine Wallet — Guardian Wallet Engine
---------------------------------------------------

This module contains the decision-making logic of the Guardian Wallet.

Responsibilities:

1. Evaluate rules against a requested action.
2. Determine whether approval is required.
3. Generate ApprovalRequest objects.
4. Apply guardian decisions to update approval status.
5. Return a final verdict: ALLOW or BLOCK (pending approval).

This is a skeleton with clean APIs that the wallet can call.
Transaction signing / networking is NOT done here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from .models import (
    Guardian,
    GuardianRule,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
    RuleScope,
    RuleAction,
)


class GuardianVerdict(str, Enum):
    """Outcome of guardian evaluation."""

    ALLOW = "ALLOW"          # No approval required
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    BLOCK = "BLOCK"          # Explicitly forbidden by a rule


@dataclass
class ActionContext:
    """
    Represents what the wallet is attempting to do.

    This is passed into the guardian engine to determine rule matches.
    """

    action: RuleAction
    wallet_id: Optional[str] = None
    account_id: Optional[str] = None
    asset_id: Optional[str] = None
    value: Optional[int] = None        # DGB satoshis or asset units
    description: Optional[str] = None  # human readable


class GuardianEngine:
    """
    Main rule evaluation engine.

    The wallet UI calls:

        verdict, request = engine.evaluate(context)

    If verdict == REQUIRE_APPROVAL:
        The wallet pauses the action and sends the ApprovalRequest to the UI
        so guardians can decide.

    If verdict == ALLOW:
        Signing can continue immediately.

    If verdict == BLOCK:
        UI shows an immediate error / denial.
    """

    def __init__(self, guardians: Dict[str, Guardian], rules: Dict[str, GuardianRule]):
        self.guardians = guardians
        self.rules = rules

    # ----------------------------------------------------------------------
    # Core evaluation flow
    # ----------------------------------------------------------------------

    def evaluate(self, ctx: ActionContext) -> (GuardianVerdict, Optional[ApprovalRequest]):
        """
        Evaluate all rules and determine the outcome for a given action.

        Returns:
            (GuardianVerdict, ApprovalRequest or None)
        """

        matching_rules = self._find_matching_rules(ctx)

        if not matching_rules:
            return GuardianVerdict.ALLOW, None

        # If any rule explicitly blocks the action, stop immediately.
        for rule in matching_rules:
            if rule.threshold_value is None and rule.min_approvals == 0:
                # Interpret this rule as a BLOCK rule.
                return GuardianVerdict.BLOCK, None

        # Determine if approval is needed based on thresholds.
        needs_approval, rule = self._requires_approval(ctx, matching_rules)

        if not needs_approval:
            return GuardianVerdict.ALLOW, None

        # Create an approval request for the UI.
        request = self._build_approval_request(ctx, rule)
        return GuardianVerdict.REQUIRE_APPROVAL, request

    # ----------------------------------------------------------------------
    # Rule matching
    # ----------------------------------------------------------------------

    def _find_matching_rules(self, ctx: ActionContext) -> List[GuardianRule]:
        matching: List[GuardianRule] = []

        for rule in self.rules.values():
            if rule.action != ctx.action:
                continue

            # Scope filtering
            if rule.scope == RuleScope.ACCOUNT and rule.account_id != ctx.account_id:
                continue
            if rule.scope == RuleScope.ASSET and rule.asset_id != ctx.asset_id:
                continue

            matching.append(rule)

        return matching

    # ----------------------------------------------------------------------
    # Approval need evaluation
    # ----------------------------------------------------------------------

    def _requires_approval(self, ctx: ActionContext, rules: List[GuardianRule]):
        """
        Among matching rules, determine if approval is required.

        Policy:
        - If rule has threshold_value:
            approval is required if ctx.value >= threshold
        - If rule has no threshold:
            always requires approval (min_approvals > 0)
        """

        for rule in rules:
            if rule.threshold_value is None:
                # Always require approval
                return True, rule

            if ctx.value is not None and ctx.value >= rule.threshold_value:
                return True, rule

        return False, None

    # ----------------------------------------------------------------------
    # Approval request construction
    # ----------------------------------------------------------------------

    def _build_approval_request(self, ctx: ActionContext, rule: GuardianRule) -> ApprovalRequest:
        """
        Convert a rule + action context into a full ApprovalRequest.
        """

        req = ApprovalRequest(
            id=f"req_{ctx.action}_{rule.id}",
            rule_id=rule.id,
            action=ctx.action,
            scope=rule.scope,
            wallet_id=ctx.wallet_id,
            account_id=ctx.account_id,
            asset_id=ctx.asset_id,
            value=ctx.value,
            description=ctx.description,
            required_guardians=list(rule.guardian_ids),
            decisions=[],
            status=ApprovalStatus.PENDING,
        )
        return req

    # ----------------------------------------------------------------------
    # Applying decisions
    # ----------------------------------------------------------------------

    def apply_decision(
        self,
        request: ApprovalRequest,
        guardian_id: str,
        status: ApprovalStatus,
        reason: Optional[str] = None,
    ) -> None:
        """
        Record a guardian's decision on an ApprovalRequest.
        """

        # Remove previous decision if it exists
        request.decisions = [
            d for d in request.decisions if d.guardian_id != guardian_id
        ]

        # Add new decision
        request.decisions.append(ApprovalDecision(
            guardian_id=guardian_id,
            status=status,
            reason=reason,
        ))

        # Check final outcome
        if status == ApprovalStatus.REJECTED:
            request.status = ApprovalStatus.REJECTED
        else:
            approvals = request.approvals_count()
            rule = self.rules.get(request.rule_id)

            if rule and approvals >= rule.min_approvals:
                request.status = ApprovalStatus.APPROVED
