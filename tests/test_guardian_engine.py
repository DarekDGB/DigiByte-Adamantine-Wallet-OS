"""
Tests for the Guardian Wallet Engine.

We verify:

- no rules -> ALLOW
- threshold rule below limit -> ALLOW
- threshold rule above/equal limit -> REQUIRE_APPROVAL
- block rule (no threshold, min_approvals = 0) -> BLOCK
- apply_decision updates ApprovalRequest status correctly
"""

from core.guardian_wallet.engine import (
    GuardianEngine,
    ActionContext,
    GuardianVerdict,
)
from core.guardian_wallet.models import (
    Guardian,
    GuardianRule,
    GuardianRole,
    GuardianStatus,
    RuleScope,
    RuleAction,
    ApprovalStatus,
)


def _make_guardian(gid: str = "g1") -> Guardian:
    return Guardian(
        id=gid,
        label="Guardian 1",
        role=GuardianRole.PERSON,
        contact="guardian@example.com",
        status=GuardianStatus.ACTIVE,
    )


def _make_simple_rule(
    rid: str = "r1",
    scope: RuleScope = RuleScope.WALLET,
    action: RuleAction = RuleAction.SEND,
    threshold_value: int | None = None,
    min_approvals: int = 1,
    guardian_ids: list[str] | None = None,
) -> GuardianRule:
    return GuardianRule(
        id=rid,
        scope=scope,
        action=action,
        threshold_value=threshold_value,
        min_approvals=min_approvals,
        guardian_ids=guardian_ids or ["g1"],
        description="Test rule",
    )


# -------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------


def test_no_rules_allows_action():
    engine = GuardianEngine(guardians={}, rules={})

    ctx = ActionContext(
        action=RuleAction.SEND,
        wallet_id="w1",
        account_id="a1",
        value=1_000,
        description="send small amount",
    )

    verdict, request = engine.evaluate(ctx)

    assert verdict == GuardianVerdict.ALLOW
    assert request is None


def test_threshold_rule_below_limit_allows():
    guardians = {"g1": _make_guardian("g1")}
    rules = {
        "r1": _make_simple_rule(
            rid="r1",
            threshold_value=10_000,  # require approval at >= 10k
            min_approvals=1,
        )
    }

    engine = GuardianEngine(guardians=guardians, rules=rules)

    ctx = ActionContext(
        action=RuleAction.SEND,
        wallet_id="w1",
        account_id="a1",
        value=5_000,  # below threshold
        description="small payment",
    )

    verdict, request = engine.evaluate(ctx)

    assert verdict == GuardianVerdict.ALLOW
    assert request is None


def test_threshold_rule_above_limit_requires_approval():
    guardians = {"g1": _make_guardian("g1")}
    rules = {
        "r1": _make_simple_rule(
            rid="r1",
            threshold_value=10_000,
            min_approvals=1,
        )
    }

    engine = GuardianEngine(guardians=guardians, rules=rules)

    ctx = ActionContext(
        action=RuleAction.SEND,
        wallet_id="w1",
        account_id="a1",
        value=20_000,  # above threshold
        description="large payment",
    )

    verdict, request = engine.evaluate(ctx)

    assert verdict == GuardianVerdict.REQUIRE_APPROVAL
    assert request is not None
    assert request.rule_id == "r1"
    assert request.value == 20_000
    assert request.status == ApprovalStatus.PENDING
    assert request.required_guardians == ["g1"]


def test_block_rule_without_threshold_blocks_immediately():
    guardians = {"g1": _make_guardian("g1")}
    # threshold_value=None and min_approvals=0 -> interpret as BLOCK rule
    rules = {
        "block_rule": _make_simple_rule(
            rid="block_rule",
            threshold_value=None,
            min_approvals=0,
        )
    }

    engine = GuardianEngine(guardians=guardians, rules=rules)

    ctx = ActionContext(
        action=RuleAction.SEND,
        wallet_id="w1",
        account_id="a1",
        value=1_000_000,
        description="blocked by policy",
    )

    verdict, request = engine.evaluate(ctx)

    assert verdict == GuardianVerdict.BLOCK
    assert request is None


def test_apply_decision_approves_after_minimum_reached():
    guardians = {
        "g1": _make_guardian("g1"),
        "g2": _make_guardian("g2"),
    }
    rules = {
        "r_multi": GuardianRule(
            id="r_multi",
            scope=RuleScope.WALLET,
            action=RuleAction.SEND,
            threshold_value=1_000,
            min_approvals=2,
            guardian_ids=["g1", "g2"],
            description="two-guardian approval",
        )
    }

    engine = GuardianEngine(guardians=guardians, rules=rules)

    ctx = ActionContext(
        action=RuleAction.SEND,
        wallet_id="w1",
        account_id="a1",
        value=5_000,
        description="multi-guardian send",
    )

    verdict, request = engine.evaluate(ctx)
    assert verdict == GuardianVerdict.REQUIRE_APPROVAL
    assert request is not None
    assert request.status == ApprovalStatus.PENDING

    # First approval
    engine.apply_decision(request, guardian_id="g1", status=ApprovalStatus.APPROVED)
    assert request.status == ApprovalStatus.PENDING  # still waiting for second

    # Second approval
    engine.apply_decision(request, guardian_id="g2", status=ApprovalStatus.APPROVED)
    assert request.status == ApprovalStatus.APPROVED


def test_apply_decision_rejected_overrides_approvals():
    guardians = {"g1": _make_guardian("g1")}
    rules = {
        "r1": _make_simple_rule(
            rid="r1",
            threshold_value=100,
            min_approvals=1,
        )
    }

    engine = GuardianEngine(guardians=guardians, rules=rules)

    ctx = ActionContext(
        action=RuleAction.SEND,
        wallet_id="w1",
        account_id="a1",
        value=1_000,
        description="test rejection",
    )

    verdict, request = engine.evaluate(ctx)
    assert verdict == GuardianVerdict.REQUIRE_APPROVAL
    assert request is not None

    engine.apply_decision(
        request,
        guardian_id="g1",
        status=ApprovalStatus.REJECTED,
        reason="I don't trust this send",
    )

    assert request.status == ApprovalStatus.REJECTED
    assert request.rejections_count() == 1
