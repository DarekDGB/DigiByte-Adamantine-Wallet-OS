"""
Guardian UI Payloads (Public Client Contract) — schema v1

Purpose
-------
Convert low-level Guardian engine outputs into a stable, JSON-friendly payload
that wallet clients (Android / iOS / Web) can render without knowing internal
engine structures.

Contract Stability
------------------
This file defines a client-facing schema. Fields MUST remain backward compatible.
- You may add new optional fields.
- Do not change meanings of existing fields.
- If a breaking change is needed, bump schema_version (e.g. "2").

Atomic Units
------------
Amounts should be represented in atomic units (integer smallest units).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Literal
import time

from .engine import GuardianVerdict
from .models import Guardian, GuardianRule, ApprovalRequest


SchemaVersion = Literal["1"]


# ---------------------------------------------------------------------------
# View models (safe for UI)
# ---------------------------------------------------------------------------

@dataclass
class GuardianView:
    """Minimal guardian info safe to show in UI."""
    id: str
    label: str
    role: str
    contact: Optional[str]
    status: str


@dataclass
class ApprovalStatusView:
    """Aggregated view of approvals vs rejections vs pending."""
    total_required: int
    approved: int
    rejected: int
    pending: int


@dataclass
class GuardianUIPayload:
    """
    High-level payload representing the outcome of a Guardian evaluation.

    This is the stable contract wallet clients consume.
    """

    # Contract
    schema_version: SchemaVersion

    # Outcome
    verdict: str  # "ALLOW" | "REQUIRE_APPROVAL" | "BLOCK"
    needs_approval: bool

    # Human-facing
    short_message: str
    long_message: Optional[str]

    # Machine-facing (clients should prefer these over parsing messages)
    codes: List[str]
    next_actions: List[str]

    # For REQUIRE_APPROVAL:
    approval_request_id: Optional[str]
    rule_id: Optional[str]
    rule_description: Optional[str]

    guardians: List[GuardianView]
    status: Optional[ApprovalStatusView]

    # Optional extra info the client may show or log
    meta: Dict[str, Any]

    # Optional timestamp for UI ordering/logging
    timestamp_ms: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict for JSON / API responses."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _build_guardian_view_map(guardians: Dict[str, Guardian]) -> Dict[str, GuardianView]:
    view_map: Dict[str, GuardianView] = {}
    for gid, g in guardians.items():
        view_map[gid] = GuardianView(
            id=g.id,
            label=g.label,
            role=g.role.name if hasattr(g.role, "name") else str(g.role),
            contact=getattr(g, "contact", None),
            status=g.status.name if hasattr(g.status, "name") else str(g.status),
        )
    return view_map


def _build_status_view(req: ApprovalRequest) -> ApprovalStatusView:
    approved = req.approvals_count()
    rejected = req.rejections_count()
    total_required = req.min_approvals
    pending = max(total_required - approved - rejected, 0)

    return ApprovalStatusView(
        total_required=total_required,
        approved=approved,
        rejected=rejected,
        pending=pending,
    )


def build_ui_payload(
    verdict: GuardianVerdict,
    approval_request: Optional[ApprovalRequest],
    rules: Dict[str, GuardianRule],
    guardians: Dict[str, Guardian],
    meta: Optional[Dict[str, Any]] = None,
    *,
    schema_version: SchemaVersion = "1",
) -> GuardianUIPayload:
    """
    Build a GuardianUIPayload from the engine result + config maps.

    meta can include:
      - "long_message": override long_message for more specific reasoning
      - any client-safe fields for display/logging (amount_atoms, asset, address, ...)
    """
    meta = meta or {}
    guardian_views = _build_guardian_view_map(guardians)

    # Defaults
    approval_request_id: Optional[str] = None
    rule_id: Optional[str] = None
    rule_description: Optional[str] = None
    status_view: Optional[ApprovalStatusView] = None
    needs_approval = False

    codes: List[str] = []
    next_actions: List[str] = []

    # Messages and actions depend on verdict
    if verdict == GuardianVerdict.ALLOW:
        short = "Action allowed"
        long = meta.get("long_message") or "Guardian policy allowed this action without extra approvals."
        codes = ["ALLOW"]
        next_actions = ["CONTINUE", "VIEW_DETAILS"]

    elif verdict == GuardianVerdict.REQUIRE_APPROVAL:
        needs_approval = True
        short = "Approval required"
        long = meta.get("long_message") or "This action needs guardian approvals before it can continue."
        codes = ["REQUIRE_APPROVAL"]
        next_actions = ["REQUEST_APPROVAL", "CANCEL", "VIEW_DETAILS"]

        if approval_request is not None:
            approval_request_id = approval_request.id
            rule_id = approval_request.rule_id
            status_view = _build_status_view(approval_request)

            rule_obj = rules.get(rule_id) if rule_id else None
            if rule_obj is not None:
                rule_description = rule_obj.description
                codes.append("POLICY_RULE")

    elif verdict == GuardianVerdict.BLOCK:
        short = "Action blocked"
        long = meta.get("long_message") or "Guardian policy blocked this action."
        codes = ["BLOCK"]
        next_actions = ["CANCEL", "VIEW_DETAILS"]

    else:
        # Future-proofing
        short = f"Unknown guardian verdict: {verdict}"
        long = meta.get("long_message") or "The guardian engine returned an unrecognised verdict."
        codes = ["UNKNOWN_VERDICT"]
        next_actions = ["CANCEL", "VIEW_DETAILS"]

    # Filter guardians to only those relevant to the request if applicable
    if approval_request is not None and getattr(approval_request, "required_guardians", None):
        guardian_list = [
            guardian_views[gid]
            for gid in approval_request.required_guardians
            if gid in guardian_views
        ]
    else:
        guardian_list = list(guardian_views.values())

    return GuardianUIPayload(
        schema_version=schema_version,
        verdict=verdict.name if hasattr(verdict, "name") else str(verdict),
        needs_approval=needs_approval,
        short_message=short,
        long_message=long,
        codes=codes,
        next_actions=next_actions,
        approval_request_id=approval_request_id,
        rule_id=rule_id,
        rule_description=rule_description,
        guardians=guardian_list,
        status=status_view,
        meta=meta,
        timestamp_ms=int(time.time() * 1000),
    )
