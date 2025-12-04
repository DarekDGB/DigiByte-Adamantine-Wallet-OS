"""
Risk Engine – Adapter for Guardian Wallet Policy

This module translates a Guardian `PolicyDecision` into a simpler
risk/UX shape the rest of the wallet can consume.

It does **not** talk to the network or storage – it is pure logic.

Typical flow:

    decision = guardian_policy.evaluate(operation_ctx)
    adapter   = GuardianRiskAdapter()
    summary   = adapter.from_policy_decision(decision)

The UI / orchestrator can then look at `GuardianRiskSummary` and decide:
  - show PIN screen
  - ask for guardian approval
  - block the operation, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from core.guardian_wallet.guardian_policy import PolicyDecision, Decision


@dataclass
class GuardianRiskSummary:
    """
    Normalised view of Guardian requirements from a risk perspective.
    """

    decision: Decision
    """Final Guardian decision: allow / require_auth / require_guardian / block."""

    reasons: List[str] = field(default_factory=list)
    """Machine-readable reasons (for logs / telemetry)."""

    ui_message_key: str = "guardian.ok"
    """
    Key for the client-side i18n/UX layer, for example:
      - guardian.ok
      - guardian.require_auth
      - guardian.require_guardian
      - guardian.blocked
    """

    require_device_auth: bool = False
    """Whether the client must ask for device-level auth (PIN / biometric)."""

    require_guardian_approval: bool = False
    """Whether the client must collect explicit guardian approval."""

    hard_block: bool = False
    """If True, the operation must not proceed under any circumstance."""


class GuardianRiskAdapter:
    """
    Adapter that converts Guardian `PolicyDecision` objects into
    `GuardianRiskSummary` instances consumed by the risk engine / UI.

    Keeping this logic isolated means:
      - we can evolve Guardian rules without touching UI code
      - we can plug additional context (future risk signals) here later
    """

    def from_policy_decision(self, decision: PolicyDecision) -> GuardianRiskSummary:
        """
        Map a PolicyDecision into a GuardianRiskSummary.

        Right now this is a straightforward mapping, but we keep it as
        a separate layer so we can enrich it with more risk context over time.
        """
        summary = GuardianRiskSummary(
            decision=decision.decision,
            reasons=list(decision.reasons),
        )

        # Map decision → UX key + blocking flag
        if decision.decision == "allow":
            summary.ui_message_key = "guardian.ok"
            summary.hard_block = False
        elif decision.decision == "require_auth":
            summary.ui_message_key = "guardian.require_auth"
            summary.require_device_auth = True
        elif decision.decision == "require_guardian":
            summary.ui_message_key = "guardian.require_guardian"
            summary.require_device_auth = True
            summary.require_guardian_approval = True
        elif decision.decision == "block":
            summary.ui_message_key = "guardian.blocked"
            summary.hard_block = True
            summary.require_device_auth = False
            summary.require_guardian_approval = False

        # If the underlying requirements list contained guardian-related
        # requirements, make sure the flags reflect that too.
        if decision.requires_any_guardian():
            summary.require_guardian_approval = True
            if summary.decision == "allow":
                # Safety: if rules say guardian approval is needed but the
                # top-level decision is "allow", gently escalate to require_auth.
                summary.decision = "require_guardian"
                summary.ui_message_key = "guardian.require_guardian"

        return summary
