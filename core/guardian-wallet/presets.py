"""
Guardian Wallet – Policy Presets

This module defines a few opinionated *presets* that a wallet UI can
offer to users, such as:

- "conservative"  – high friction, strong guard rails
- "balanced"      – sensible defaults for most users
- "aggressive"    – minimal prompts, more freedom / responsibility

Each preset is expressed as a dictionary of GuardianRule objects.  The
actual Guardian objects (people / devices / services) are provided by
the caller; presets only describe *when* and *how many* approvals are
required.

Typical usage:

    from core.guardian_wallet import presets

    rules = presets.build_balanced_preset(default_guardian_ids=["g1"])
    engine = GuardianEngine(guardians=my_guardians, rules=rules)

You are free to tweak these or provide your own custom presets on top.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .models import (
    GuardianRule,
    RuleScope,
    RuleAction,
)


@dataclass(frozen=True)
class GuardianPreset:
    """
    Simple value object describing a named preset.
    """
    name: str
    description: str
    rules: Dict[str, GuardianRule]


# ---------------------------------------------------------------------------
# Internal rule helpers
# ---------------------------------------------------------------------------

def _threshold_rule(
    rule_id: str,
    *,
    scope: RuleScope,
    action: RuleAction,
    threshold_value: int,
    min_approvals: int,
    guardian_ids: List[str],
    description: str,
) -> GuardianRule:
    """
    Build a standard threshold-based rule:
        - below threshold  -> ALLOW
        - at/above         -> REQUIRE_APPROVAL
    """
    return GuardianRule(
        id=rule_id,
        scope=scope,
        action=action,
        threshold_value=threshold_value,
        min_approvals=min_approvals,
        guardian_ids=list(guardian_ids),
        description=description,
    )


def _block_rule(
    rule_id: str,
    *,
    scope: RuleScope,
    action: RuleAction,
    description: str,
) -> GuardianRule:
    """
    Build a hard block rule:
        - no threshold, min_approvals = 0
        - interpreted by GuardianEngine as "BLOCK immediately"
    """
    return GuardianRule(
        id=rule_id,
        scope=scope,
        action=action,
        threshold_value=None,
        min_approvals=0,
        guardian_ids=[],
        description=description,
    )


# ---------------------------------------------------------------------------
# Public preset builders
# ---------------------------------------------------------------------------

def build_conservative_preset(
    default_guardian_ids: List[str],
) -> Dict[str, GuardianRule]:
    """
    Very protective defaults.

    - Any send over 1,000 DGB-equivalent requires 2 approvals.
    - Any DigiDollar mint/redeem over 500 DGB-equivalent requires 2 approvals.
    - Optional: block "high-risk" custom actions by policy (can be extended).
    """
    if not default_guardian_ids:
        raise ValueError("conservative preset requires at least one guardian id")

    # If only one guardian is provided, we still ask for 1-of-1 approvals.
    approvals_for_large = max(1, min(2, len(default_guardian_ids)))

    rules: Dict[str, GuardianRule] = {}

    # High-value DGB sends
    rules["conservative_send_large"] = _threshold_rule(
        "conservative_send_large",
        scope=RuleScope.WALLET,
        action=RuleAction.SEND,
        threshold_value=1_000_000,  # interpret as "minor units" or DGB per convention
        min_approvals=approvals_for_large,
        guardian_ids=default_guardian_ids,
        description="Require guardian approval for large DGB sends.",
    )

    # High-value DigiDollar minting (DGB -> DD)
    if hasattr(RuleAction, "MINT_DD"):
        rules["conservative_mint_dd_large"] = _threshold_rule(
            "conservative_mint_dd_large",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "MINT_DD"),
            threshold_value=500_000,
            min_approvals=approvals_for_large,
            guardian_ids=default_guardian_ids,
            description="Require guardian approval for large DigiDollar mints.",
        )

    # High-value DigiDollar redeem (DD -> DGB)
    if hasattr(RuleAction, "REDEEM_DD"):
        rules["conservative_redeem_dd_large"] = _threshold_rule(
            "conservative_redeem_dd_large",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "REDEEM_DD"),
            threshold_value=500_000,
            min_approvals=approvals_for_large,
            guardian_ids=default_guardian_ids,
            description="Require guardian approval for large DigiDollar redeems.",
        )

    return rules


def build_balanced_preset(
    default_guardian_ids: List[str],
) -> Dict[str, GuardianRule]:
    """
    Balanced defaults for most users.

    - Frequent small payments flow without friction.
    - Medium and large operations ask guardians to confirm.
    """
    if not default_guardian_ids:
        raise ValueError("balanced preset requires at least one guardian id")

    approvals_for_large = max(1, min(2, len(default_guardian_ids)))

    rules: Dict[str, GuardianRule] = {}

    # Medium+ DGB sends (e.g. > 100k units) need 1 approval.
    rules["balanced_send_medium"] = _threshold_rule(
        "balanced_send_medium",
        scope=RuleScope.WALLET,
        action=RuleAction.SEND,
        threshold_value=100_000,
        min_approvals=1,
        guardian_ids=[default_guardian_ids[0]],
        description="Ask for guardian confirmation on medium / large DGB sends.",
    )

    # Larger DGB sends need more approvals if available.
    rules["balanced_send_large"] = _threshold_rule(
        "balanced_send_large",
        scope=RuleScope.WALLET,
        action=RuleAction.SEND,
        threshold_value=1_000_000,
        min_approvals=approvals_for_large,
        guardian_ids=default_guardian_ids,
        description="Require multiple guardian approvals for very large sends.",
    )

    # DigiDollar mint/redeem – mainly guard larger movements.
    if hasattr(RuleAction, "MINT_DD"):
        rules["balanced_mint_dd_large"] = _threshold_rule(
            "balanced_mint_dd_large",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "MINT_DD"),
            threshold_value=250_000,
            min_approvals=1,
            guardian_ids=[default_guardian_ids[0]],
            description="Guardian confirmation for large DigiDollar mints.",
        )

    if hasattr(RuleAction, "REDEEM_DD"):
        rules["balanced_redeem_dd_large"] = _threshold_rule(
            "balanced_redeem_dd_large",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "REDEEM_DD"),
            threshold_value=250_000,
            min_approvals=1,
            guardian_ids=[default_guardian_ids[0]],
            description="Guardian confirmation for large DigiDollar redeems.",
        )

    return rules


def build_aggressive_preset(
    default_guardian_ids: List[str],
) -> Dict[str, GuardianRule]:
    """
    Minimal friction preset.

    - Only extremely large operations (e.g. "life changing" value) are guarded.
    - Intended for power users who still want a last-resort safety net.
    """
    if not default_guardian_ids:
        raise ValueError("aggressive preset requires at least one guardian id")

    rules: Dict[str, GuardianRule] = {}

    rules["aggressive_send_extreme"] = _threshold_rule(
        "aggressive_send_extreme",
        scope=RuleScope.WALLET,
        action=RuleAction.SEND,
        threshold_value=10_000_000,  # extremely high
        min_approvals=1,
        guardian_ids=[default_guardian_ids[0]],
        description="Only guard extremely large sends.",
    )

    if hasattr(RuleAction, "MINT_DD"):
        rules["aggressive_mint_dd_extreme"] = _threshold_rule(
            "aggressive_mint_dd_extreme",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "MINT_DD"),
            threshold_value=5_000_000,
            min_approvals=1,
            guardian_ids=[default_guardian_ids[0]],
            description="Only guard extremely large DigiDollar mints.",
        )

    if hasattr(RuleAction, "REDEEM_DD"):
        rules["aggressive_redeem_dd_extreme"] = _threshold_rule(
            "aggressive_redeem_dd_extreme",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "REDEEM_DD"),
            threshold_value=5_000_000,
            min_approvals=1,
            guardian_ids=[default_guardian_ids[0]],
            description="Only guard extremely large DigiDollar redeems.",
        )

    return rules


# ---------------------------------------------------------------------------
# Registry helper
# ---------------------------------------------------------------------------

def get_preset(
    name: str,
    default_guardian_ids: List[str],
) -> GuardianPreset:
    """
    Resolve a preset by name and build its rules.

    Names (case-insensitive):

        - "conservative"
        - "balanced"
        - "aggressive"
    """
    key = name.strip().lower()

    if key == "conservative":
        rules = build_conservative_preset(default_guardian_ids)
        return GuardianPreset(
            name="conservative",
            description="High protection / high friction policy.",
            rules=rules,
        )
    if key == "balanced":
        rules = build_balanced_preset(default_guardian_ids)
        return GuardianPreset(
            name="balanced",
            description="Default preset for most users.",
            rules=rules,
        )
    if key == "aggressive":
        rules = build_aggressive_preset(default_guardian_ids)
        return GuardianPreset(
            name="aggressive",
            description="Low friction, guards only extreme operations.",
            rules=rules,
        )

    raise ValueError(f"Unknown Guardian preset name: {name!r}")
