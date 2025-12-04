"""
Guardian UI Payloads

Small helper functions and dataclasses that turn low-level Guardian
objects (GuardianVerdict, ApprovalRequest, GuardianRule, etc.) into
simple, serialisable payloads that UI layers (Android / iOS / Web) can
render.

The goal: wallet front-ends should NOT need to know internal Guardian
engine structures. They receive plain dicts or dataclasses describing:

- what happened (ALLOW / REQUIRE_APPROVAL / BLOCK),
- why it happened (short + long message),
- who needs to approve (guardians, counts),
- what the user can do next.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

from .engine import GuardianVerdict
from .models import (
    Guardian,
    GuardianRule,
    ApprovalRequest,
    ApprovalStatus,
)


# ---------------------------------------------------------------------------
# View models
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

    This is what the clients (Android / iOS / Web) should consume.
    """

    verdict: str  # "ALLOW" | "REQUIRE_APPROVAL" | "BLOCK"
    short_message: str
    long_message: Optional[str]

    # For REQUIRE_APPROVAL:
    needs_approval: bool
    approval_request_id: Optional[str]
    rule_id: Optional[str]
    rule_description: Optional[str]

    guardians: List[GuardianView]
    status: Optional[ApprovalStatusView]

    # Optional extra info the client may show or log
    meta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict for JSON / API responses."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _build_guardian_view_map(guardians: Dict[str, Guardian]) -> Dict[str, GuardianView]:
    """Convert Guardian objects into GuardianView map keyed by id."""
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
    """Summarise current approval status for UI."""
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
) -> GuardianUIPayload:
    """
    Build a GuardianUIPayload from the engine result + config maps.

    Arguments
    ---------
    verdict:
        Result of GuardianEngine.evaluate(...)
    approval_request:
        Optional ApprovalRequest returned by GuardianEngine (for REQUIRE_APPROVAL).
    rules:
        Dictionary of GuardianRule objects keyed by rule id.
    guardians:
        Dictionary of Guardian objects keyed by guardian id.
    meta:
        Optional extra context (e.g. asset symbol, flow type, amount).

    Returns
    -------
    GuardianUIPayload
        A digestible, UI-friendly representation.
    """
    meta = meta or {}
    guardian_views = _build_guardian_view_map(guardians)

    # Default fields
    approval_request_id: Optional[str] = None
    rule_id: Optional[str] = None
    rule_description: Optional[str] = None
    status_view: Optional[ApprovalStatusView] = None
    needs_approval = False

    # Short / long messages depend on verdict
    if verdict == GuardianVerdict.ALLOW:
        short = "Action allowed"
        long = meta.get("long_message") or "Guardian policy allowed this action without extra approvals."

    elif verdict == GuardianVerdict.REQUIRE_APPROVAL:
        needs_approval = True
        short = "Approval required"
        long = meta.get("long_message") or "This action needs guardian approvals before it can continue."

        if approval_request is not None:
            approval_request_id = approval_request.id
            rule_id = approval_request.rule_id
            status_view = _build_status_view(approval_request)

            rule_obj = rules.get(rule_id) if rule_id else None
            if rule_obj is not None:
                rule_description = rule_obj.description

    elif verdict == GuardianVerdict.BLOCK:
        short = "Action blocked"
        long = meta.get("long_message") or "Guardian policy blocked this action."

    else:
        # Unknown verdict type (future-proofing)
        short = f"Unknown guardian verdict: {verdict}"
        long = meta.get("long_message") or "The guardian engine returned an unrecognised verdict."

    # Filter guardians to only those relevant to the request if applicable
    guardian_list: List[GuardianView]
    if approval_request is not None and getattr(approval_request, "required_guardians", None):
        guardian_list = [
            guardian_views[gid]
            for gid in approval_request.required_guardians
            if gid in guardian_views
        ]
    else:
        # For ALLOW / BLOCK or missing request, we can show all or none.
        guardian_list = list(guardian_views.values())

    return GuardianUIPayload(
        verdict=verdict.name if hasattr(verdict, "name") else str(verdict),
        short_message=short,
        long_message=long,
        needs_approval=needs_approval,
        approval_request_id=approval_request_id,
        rule_id=rule_id,
        rule_description=rule_description,
        guardians=guardian_list,
        status=status_view,
        meta=meta,
    )
