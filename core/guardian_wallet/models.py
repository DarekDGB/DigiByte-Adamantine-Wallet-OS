"""
DigiByte Adamantine Wallet — Guardian Wallet Core Models
--------------------------------------------------------

These models describe the *intent layer* for Guardian behaviour:

- who is a guardian,
- what rules exist,
- how approvals are requested,
- how decisions are recorded.

They do NOT talk to the blockchain or sign anything directly.
That logic will live in higher-level Guardian engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class GuardianRole(str, Enum):
    """Role of a guardian relative to the protected wallet/account."""

    PERSON = "PERSON"          # e.g. trusted friend, family member
    DEVICE = "DEVICE"          # second device you own
    SERVICE = "SERVICE"        # e.g. custody or institutional service


class GuardianStatus(str, Enum):
    """Lifecycle status of a guardian."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


@dataclass
class Guardian:
    """
    A single guardian entity.

    `id` can be a UUID string or any locally unique identifier.
    """

    id: str
    label: str
    role: GuardianRole
    contact: Optional[str] = None  # email / username / address hint
    status: GuardianStatus = GuardianStatus.ACTIVE


class RuleScope(str, Enum):
    """What the rule applies to."""

    WALLET = "WALLET"
    ACCOUNT = "ACCOUNT"
    ASSET = "ASSET"


class RuleAction(str, Enum):
    """What kind of operation the rule protects."""

    SEND = "SEND"              # regular DGB / asset sends
    DD_MINT = "DD_MINT"        # DigiDollar mint
    DD_REDEEM = "DD_REDEEM"    # DigiDollar redeem
    ASSET_ISSUE = "ASSET_ISSUE"
    ASSET_BURN = "ASSET_BURN"
    DEVICE_BIND = "DEVICE_BIND"
    SETTINGS_CHANGE = "SETTINGS_CHANGE"


@dataclass
class GuardianRule:
    """
    A single Guardian rule.

    Example:
        - scope: WALLET
        - action: SEND
        - threshold_dgb: 10_000
        - required_guardians: ["g1", "g2"]
    """

    id: str
    scope: RuleScope
    action: RuleAction

    # Optional scoping fields:
    account_id: Optional[str] = None
    asset_id: Optional[str] = None

    # Thresholds (smallest units: satoshis, asset units, etc.)
    threshold_value: Optional[int] = None

    # Guardian requirements:
    min_approvals: int = 1
    guardian_ids: List[str] = field(default_factory=list)

    description: Optional[str] = None


class ApprovalStatus(str, Enum):
    """State of a given approval request."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class GuardianVerdict(str, Enum):
    """
    High-level verdict for Guardian decisions.

    Tests and GuardianDecision use this enum.
    """

    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    BLOCK = "BLOCK"


@dataclass
class ApprovalDecision:
    """A single guardian's response to an approval request."""

    guardian_id: str
    status: ApprovalStatus
    reason: Optional[str] = None


@dataclass
class ApprovalRequest:
    """
    A structured request for guardian approval.

    This object is created before a protected action is executed.
    """

    id: str
    rule_id: str
    action: RuleAction
    scope: RuleScope

    # Who/what is being protected:
    wallet_id: Optional[str] = None
    account_id: Optional[str] = None
    asset_id: Optional[str] = None

    # What is being attempted:
    value: Optional[int] = None          # e.g. DGB satoshis or asset units
    description: Optional[str] = None    # short human-readable summary

    # Guardians:
    required_guardians: List[str] = field(default_factory=list)
    decisions: List[ApprovalDecision] = field(default_factory=list)

    # Overall status:
    status: ApprovalStatus = ApprovalStatus.PENDING

    def approvals_count(self) -> int:
        return sum(1 for d in self.decisions if d.status == ApprovalStatus.APPROVED)

    def rejections_count(self) -> int:
        return sum(1 for d in self.decisions if d.status == ApprovalStatus.REJECTED)

    def is_satisfied(self, min_required: int) -> bool:
        """
        Check if the minimum number of approvals has been reached.
        """
        return self.approvals_count() >= min_required


# ---------------------------------------------------------------------------
# Runtime context + decisions for GuardianAdapter / WalletService
# ---------------------------------------------------------------------------


@dataclass
class ActionContext:
    """
    Information about the operation the guardian is evaluating.

    Tests expect at least:
      - wallet_id
      - account_id
      - value
      - description
      - meta (dict, default {})
    """

    action: RuleAction
    wallet_id: str
    account_id: str
    value: int

    # Optional human-readable description shown in the UI
    description: str = ""

    # Arbitrary extra metadata (asset_id, tags, flags, etc.)
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GuardianDecision:
    """
    Result of a guardian evaluation.

    Tests typically check:
      - decision.blocked         (bool)
      - decision.needs_approval  (bool)
      - decision.context         (ActionContext with correct fields)

    `verdict` uses GuardianVerdict for higher-level UI logic.
    """

    blocked: bool
    needs_approval: bool = False
    reason: Optional[str] = None
    risk_score: float = 0.0
    verdict: GuardianVerdict = GuardianVerdict.ALLOW
    context: Optional[ActionContext] = None

    # -------- Convenience constructors --------

    @classmethod
    def allow(
        cls,
        *,
        context: Optional[ActionContext] = None,
        reason: str = "",
        risk_score: float = 0.0,
    ) -> "GuardianDecision":
        return cls(
            blocked=False,
            needs_approval=False,
            reason=reason,
            risk_score=risk_score,
            verdict=GuardianVerdict.ALLOW,
            context=context,
        )

    @classmethod
    def require_approval(
        cls,
        *,
        context: Optional[ActionContext] = None,
        reason: str = "",
        risk_score: float = 0.0,
    ) -> "GuardianDecision":
        return cls(
            blocked=False,
            needs_approval=True,
            reason=reason,
            risk_score=risk_score,
            verdict=GuardianVerdict.REQUIRE_APPROVAL,
            context=context,
        )

    @classmethod
    def block(
        cls,
        *,
        context: Optional[ActionContext] = None,
        reason: str = "",
        risk_score: float = 1.0,
    ) -> "GuardianDecision":
        return cls(
            blocked=True,
            needs_approval=False,
            reason=reason,
            risk_score=risk_score,
            verdict=GuardianVerdict.BLOCK,
            context=context,
        )
