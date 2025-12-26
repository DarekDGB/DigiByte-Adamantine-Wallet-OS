"""
EQC Policy Engine — Equilibrium Confirmation

This module transforms an EQCContext into a deterministic Verdict
using explicit, ordered policy rules.

EQC policies:
- are deterministic
- are side-effect free
- never sign or execute actions
- only decide whether an action is allowed, denied, or requires step-up

EQC (Equilibrium Confirmation) remains the single decision authority.
WSQK may only be invoked after VerdictType.ALLOW.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .context import EQCContext
from .verdicts import Verdict, VerdictType, Reason, ReasonCode, StepUp


@dataclass(frozen=True)
class PolicyRule:
    """
    A single policy rule.

    If `when(context)` returns True:
      - returns `verdict(context)` OR
      - returns None to allow evaluation to continue
    """
    name: str
    when: Callable[[EQCContext], bool]
    verdict: Callable[[EQCContext], Optional[Verdict]]


@dataclass
class EQCPolicy:
    """
    Policy runner. Applies rules in order and returns the first terminal verdict.

    Rule priority matters:
    - hard blocks first
    - then step-up rules
    - then allow rules
    """
    rules: List[PolicyRule] = field(default_factory=list)

    def evaluate(self, ctx: EQCContext) -> Verdict:
        # Minimal context sanity
        if not ctx or not ctx.action or not ctx.device or not ctx.network or not ctx.user:
            return Verdict.deny(
                Reason(
                    code=ReasonCode.MISSING_CONTEXT,
                    message="Missing required context fields.",
                )
            )

        for rule in self.rules:
            if rule.when(ctx):
                out = rule.verdict(ctx)
                if out is not None:
                    # Attach rule match reason if not already present
                    if not any(r.code == ReasonCode.POLICY_RULE_MATCH for r in out.reasons):
                        return Verdict(
                            type=out.type,
                            reasons=[
                                Reason(
                                    code=ReasonCode.POLICY_RULE_MATCH,
                                    message=f"Matched policy rule: {rule.name}",
                                    details={"rule": rule.name},
                                ),
                                *out.reasons,
                            ],
                            step_up=out.step_up,
                        )
                    return out

        # Default allow (explicitly deterministic)
        return Verdict.allow(
            Reason(
                code=ReasonCode.POLICY_RULE_MATCH,
                message="No policy rules blocked the action.",
                details={"rule": "DEFAULT_ALLOW"},
            )
        )


def default_policy() -> EQCPolicy:
    """
    Returns the baseline EQC policy set (v1).

    This can be extended later without breaking the interface.
    """
    rules: List[PolicyRule] = []

    # --- Hard blocks (architecture invariants) ---

    def is_browser(ctx: EQCContext) -> bool:
        return ctx.device.device_type.lower() == "browser"

    rules.append(
        PolicyRule(
            name="HARD_BLOCK_BROWSER_CONTEXT",
            when=is_browser,
            verdict=lambda ctx: Verdict.deny(
                Reason(
                    code=ReasonCode.BROWSER_CONTEXT_BLOCKED,
                    message="Browser context is not permitted for sensitive operations.",
                    details={"device_type": ctx.device.device_type},
                )
            ),
        )
    )

    def is_extension(ctx: EQCContext) -> bool:
        return ctx.device.device_type.lower() in {"extension", "browser_extension"}

    rules.append(
        PolicyRule(
            name="HARD_BLOCK_EXTENSION_CONTEXT",
            when=is_extension,
            verdict=lambda ctx: Verdict.deny(
                Reason(
                    code=ReasonCode.EXTENSION_CONTEXT_BLOCKED,
                    message="Extension context is not permitted for signing or seed handling.",
                    details={"device_type": ctx.device.device_type},
                )
            ),
        )
    )

    # --- Step-up rules (sensitive actions) ---

    def is_mint_or_redeem(ctx: EQCContext) -> bool:
        a = ctx.action.action.lower()
        return a in {"mint", "redeem"} or (ctx.action.asset.lower() == "digidollar" and a in {"issue", "burn"})

    rules.append(
        PolicyRule(
            name="STEP_UP_FOR_MINT_REDEEM",
            when=is_mint_or_redeem,
            verdict=lambda ctx: Verdict.step_up(
                StepUp(
                    requirements=_best_step_up_requirements(ctx),
                    message="Mint/Redeem requires step-up verification.",
                ),
                Reason(
                    code=ReasonCode.MINT_REDEEM_REQUIRES_STEP_UP,
                    message="Sensitive monetary action requires additional verification.",
                    details={"action": ctx.action.action, "asset": ctx.action.asset},
                ),
            ),
        )
    )

    # Large amount step-up (generic baseline)
    def is_large_amount(ctx: EQCContext) -> bool:
        # amount units are wallet-defined (e.g., satoshis). Threshold is a policy knob.
        # v1: step-up for >= 10_000_000 units (tunable).
        return (ctx.action.amount or 0) >= 10_000_000

    rules.append(
        PolicyRule(
            name="STEP_UP_FOR_LARGE_AMOUNT",
            when=is_large_amount,
            verdict=lambda ctx: Verdict.step_up(
                StepUp(
                    requirements=_best_step_up_requirements(ctx),
                    message="Large amount requires step-up verification.",
                ),
                Reason(
                    code=ReasonCode.LARGE_AMOUNT,
                    message="Amount exceeds baseline step-up threshold.",
                    details={"amount": ctx.action.amount},
                ),
            ),
        )
    )

    # New / untrusted device step-up
    def untrusted_device(ctx: EQCContext) -> bool:
        return not bool(ctx.device.trusted)

    rules.append(
        PolicyRule(
            name="STEP_UP_FOR_UNTRUSTED_DEVICE",
            when=untrusted_device,
            verdict=lambda ctx: Verdict.step_up(
                StepUp(
                    requirements=_best_step_up_requirements(ctx),
                    message="Untrusted device requires step-up verification.",
                ),
                Reason(
                    code=ReasonCode.NEW_DEVICE,
                    message="Device is not yet trusted.",
                    details={"device_id": ctx.device.device_id},
                ),
            ),
        )
    )

    return EQCPolicy(rules=rules)


def _best_step_up_requirements(ctx: EQCContext) -> List[str]:
    """
    Choose the strongest available local step-up checks, deterministically.
    """
    req: List[str] = []
    if ctx.user.biometric_available:
        req.append("biometric")
    if ctx.user.pin_set:
        req.append("pin")
    if not req:
        req.append("local_confirmation")
    return req
