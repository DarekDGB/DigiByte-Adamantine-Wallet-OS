"""
Tests for DigiAssetsEngine mint / transfer / burn orchestration.

We verify:

- basic validation failures (amount <= 0, missing asset_id, missing to_address)
- Guardian BLOCK verdict short-circuits the flow
- Guardian REQUIRE_APPROVAL verdict returns guardian_pending stage
- Guardian ALLOW verdict returns ok=True with a tx_preview structure
"""

from core.digiassets.engine import (
    DigiAssetsEngine,
    AssetOperation,
    AssetOpKind,
    AssetAmount,
    AssetId,
)
from core.guardian_wallet.adapter import GuardianDecision
from core.guardian_wallet.models import GuardianVerdict


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeNodeClient:
    """Minimal stand-in; DigiAssetsEngine does not yet call NodeClient."""

    def __init__(self) -> None:
        self.called = False


class FakeGuardianAdapter:
    """Configurable fake that returns a pre-set GuardianDecision."""

    def __init__(self, decision: GuardianDecision) -> None:
        self.decision = decision
        self.calls: list[dict] = []

    def evaluate_digiasset_op(
        self,
        wallet_id: str,
        account_id: str,
        value_units: int,
        op_kind: str,
        description: str,
        meta: dict | None = None,
    ) -> GuardianDecision:
        # record the call so tests can assert on it
        self.calls.append(
            {
                "wallet_id": wallet_id,
                "account_id": account_id,
                "value_units": value_units,
                "op_kind": op_kind,
                "description": description,
                "meta": meta or {},
            }
        )
        return self.decision


def _guardian_decision(verdict: GuardianVerdict) -> GuardianDecision:
    """Helper to make a simple GuardianDecision with no approval request."""
    return GuardianDecision(verdict=verdict, approval_request=None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_validation_failure_blocks_before_guardian():
    """
    amount <= 0 should fail validation and never call GuardianAdapter.
    """

    node = FakeNodeClient()
    guardian = FakeGuardianAdapter(_guardian_decision(GuardianVerdict.ALLOW))
    engine = DigiAssetsEngine(node_client=node, guardian=guardian)

    op = AssetOperation(
        op=AssetOpKind.MINT,
        wallet_id="w1",
        account_id="a1",
        asset_id=None,  # first-time mint is OK
        amount=AssetAmount(units=0),  # invalid: must be positive
    )

    result = engine.handle_operation(op)

    assert result.ok is False
    assert result.details["stage"] == "validation"
    assert "amount_must_be_positive" in result.details["errors"]
    # Guardian should not be consulted on pure validation failure
    assert guardian.calls == []


def test_guardian_block_stops_flow():
    """
    If Guardian returns BLOCK for a valid operation, engine should
    surface guardian_block stage and ok=False.
    """

    node = FakeNodeClient()
    guardian = FakeGuardianAdapter(_guardian_decision(GuardianVerdict.BLOCK))
    engine = DigiAssetsEngine(node_client=node, guardian=guardian)

    op = AssetOperation(
        op=AssetOpKind.MINT,
        wallet_id="w1",
        account_id="a1",
        asset_id=None,
        amount=AssetAmount(units=10),
    )

    result = engine.handle_operation(op)

    assert result.ok is False
    assert result.details["stage"] == "guardian_block"
    assert guardian.calls  # guardian was consulted


def test_guardian_requires_approval_returns_pending_stage():
    """
    REQUIRE_APPROVAL should return ok=False with guardian_pending stage,
    leaving higher layers to handle approval UX.
    """

    node = FakeNodeClient()
    guardian = FakeGuardianAdapter(
        _guardian_decision(GuardianVerdict.REQUIRE_APPROVAL)
    )
    engine = DigiAssetsEngine(node_client=node, guardian=guardian)

    op = AssetOperation(
        op=AssetOpKind.TRANSFER,
        wallet_id="w1",
        account_id="a1",
        asset_id=AssetId(id="asset-1"),
        amount=AssetAmount(units=50),
        to_address="dgb1qexample...",
    )

    result = engine.handle_operation(op)

    assert result.ok is False
    assert result.details["stage"] == "guardian_pending"
    assert guardian.calls  # guardian was consulted


def test_guardian_allow_returns_tx_preview_ready():
    """
    ALLOW should return ok=True and a tx_preview structure containing
    the key fields from AssetOperation.
    """

    node = FakeNodeClient()
    guardian = FakeGuardianAdapter(_guardian_decision(GuardianVerdict.ALLOW))
    engine = DigiAssetsEngine(node_client=node, guardian=guardian)

    op = AssetOperation(
        op=AssetOpKind.BURN,
        wallet_id="w1",
        account_id="a1",
        asset_id=AssetId(id="asset-xyz"),
        amount=AssetAmount(units=5),
        to_address=None,
        memo="burn some supply",
    )

    result = engine.handle_operation(op)

    assert result.ok is True
    assert result.details["stage"] == "ready"

    preview = result.details["tx_preview"]
    assert preview["op"] == "burn"
    assert preview["wallet_id"] == "w1"
    assert preview["account_id"] == "a1"
    assert preview["asset_id"] == "asset-xyz"
    assert preview["amount_units"] == 5
    assert preview["memo"] == "burn some supply"
