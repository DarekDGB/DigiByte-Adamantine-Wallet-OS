"""
Guardian Wallet — Policy Presets (Atomic Units)

These presets are intended to be offered by wallet clients (Android/iOS/Web).
They generate GuardianRule dictionaries that the GuardianEngine can consume.

Atomic Units
------------
threshold_value is expressed in atomic units (integer smallest unit), not floats.

Example:
- If 1 DGB = 100,000,000 atoms, then:
  1,000 DGB = 1_000 * DGB_ATOMS
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .models import GuardianRule, RuleScope, RuleAction

# DigiByte atomic unit constant (choose and keep stable)
DGB_ATOMS = 100_000_000


@dataclass(frozen=True)
class GuardianPreset:
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
    threshold_atoms: int,
    min_approvals: int,
    guardian_ids: List[str],
    description: str,
) -> GuardianRule:
    """
    Standard threshold-based rule:
      - below threshold -> ALLOW
      - at/above       -> REQUIRE_APPROVAL
    """
    return GuardianRule(
        id=rule_id,
        scope=scope,
        action=action,
        threshold_value=threshold_atoms,
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
    Hard block rule:
      - threshold_value=None, min_approvals=0
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

def build_conservative_preset(default_guardian_ids: List[str]) -> Dict[str, GuardianRule]:
    """
    High protection / high friction.

    - Any send >= 1,000 DGB requires up to 2 approvals (depending on guardians available).
    - DigiDollar mint/redeem >= 500 DGB requires up to 2 approvals.
    """
    if not default_guardian_ids:
        raise ValueError("conservative preset requires at least one guardian id")

    approvals_for_large = max(1, min(2, len(default_guardian_ids)))

    rules: Dict[str, GuardianRule] = {}

    rules["conservative_send_large"] = _threshold_rule(
        "conservative_send_large",
        scope=RuleScope.WALLET,
        action=RuleAction.SEND,
        threshold_atoms=1_000 * DGB_ATOMS,
        min_approvals=approvals_for_large,
        guardian_ids=default_guardian_ids,
        description="Require guardian approval for large DGB sends.",
    )

    if hasattr(RuleAction, "MINT_DD"):
        rules["conservative_mint_dd_large"] = _threshold_rule(
            "conservative_mint_dd_large",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "MINT_DD"),
            threshold_atoms=500 * DGB_ATOMS,
            min_approvals=approvals_for_large,
            guardian_ids=default_guardian_ids,
            description="Require guardian approval for large DigiDollar mints.",
        )

    if hasattr(RuleAction, "REDEEM_DD"):
        rules["conservative_redeem_dd_large"] = _threshold_rule(
            "conservative_redeem_dd_large",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "REDEEM_DD"),
            threshold_atoms=500 * DGB_ATOMS,
            min_approvals=approvals_for_large,
            guardian_ids=default_guardian_ids,
            description="Require guardian approval for large DigiDollar redeems.",
        )

    return rules


def build_balanced_preset(default_guardian_ids: List[str]) -> Dict[str, GuardianRule]:
    """
    Sensible defaults for most users.

    - Medium sends (>= 100 DGB) require 1 approval.
    - Large sends (>= 1,000 DGB) require up to 2 approvals.
    """
    if not default_guardian_ids:
        raise ValueError("balanced preset requires at least one guardian id")

    approvals_for_large = max(1, min(2, len(default_guardian_ids)))

    rules: Dict[str, GuardianRule] = {}

    rules["balanced_send_medium"] = _threshold_rule(
        "balanced_send_medium",
        scope=RuleScope.WALLET,
        action=RuleAction.SEND,
        threshold_atoms=100 * DGB_ATOMS,
        min_approvals=1,
        guardian_ids=[default_guardian_ids[0]],
        description="Ask for guardian confirmation on medium / large DGB sends.",
    )

    rules["balanced_send_large"] = _threshold_rule(
        "balanced_send_large",
        scope=RuleScope.WALLET,
        action=RuleAction.SEND,
        threshold_atoms=1_000 * DGB_ATOMS,
        min_approvals=approvals_for_large,
        guardian_ids=default_guardian_ids,
        description="Require multiple guardian approvals for very large sends.",
    )

    if hasattr(RuleAction, "MINT_DD"):
        rules["balanced_mint_dd_large"] = _threshold_rule(
            "balanced_mint_dd_large",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "MINT_DD"),
            threshold_atoms=250 * DGB_ATOMS,
            min_approvals=1,
            guardian_ids=[default_guardian_ids[0]],
            description="Guardian confirmation for large DigiDollar mints.",
        )

    if hasattr(RuleAction, "REDEEM_DD"):
        rules["balanced_redeem_dd_large"] = _threshold_rule(
            "balanced_redeem_dd_large",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "REDEEM_DD"),
            threshold_atoms=250 * DGB_ATOMS,
            min_approvals=1,
            guardian_ids=[default_guardian_ids[0]],
            description="Guardian confirmation for large DigiDollar redeems.",
        )

    return rules


def build_aggressive_preset(default_guardian_ids: List[str]) -> Dict[str, GuardianRule]:
    """
    Low friction preset.

    - Only extreme sends (>= 10,000 DGB) require 1 approval.
    - Intended for power users who still want a last-resort safety net.
    """
    if not default_guardian_ids:
        raise ValueError("aggressive preset requires at least one guardian id")

    rules: Dict[str, GuardianRule] = {}

    rules["aggressive_send_extreme"] = _threshold_rule(
        "aggressive_send_extreme",
        scope=RuleScope.WALLET,
        action=RuleAction.SEND,
        threshold_atoms=10_000 * DGB_ATOMS,
        min_approvals=1,
        guardian_ids=[default_guardian_ids[0]],
        description="Only guard extremely large sends.",
    )

    if hasattr(RuleAction, "MINT_DD"):
        rules["aggressive_mint_dd_extreme"] = _threshold_rule(
            "aggressive_mint_dd_extreme",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "MINT_DD"),
            threshold_atoms=5_000 * DGB_ATOMS,
            min_approvals=1,
            guardian_ids=[default_guardian_ids[0]],
            description="Only guard extremely large DigiDollar mints.",
        )

    if hasattr(RuleAction, "REDEEM_DD"):
        rules["aggressive_redeem_dd_extreme"] = _threshold_rule(
            "aggressive_redeem_dd_extreme",
            scope=RuleScope.WALLET,
            action=getattr(RuleAction, "REDEEM_DD"),
            threshold_atoms=5_000 * DGB_ATOMS,
            min_approvals=1,
            guardian_ids=[default_guardian_ids[0]],
            description="Only guard extremely large DigiDollar redeems.",
        )

    return rules


def get_preset(name: str, default_guardian_ids: List[str]) -> GuardianPreset:
    """
    Resolve a preset by name and build its rules.

    Names (case-insensitive):
      - conservative
      - balanced
      - aggressive
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
