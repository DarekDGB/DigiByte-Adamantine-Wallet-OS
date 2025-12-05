"""
Tests for DigiAsset helper methods on GuardianAdapter.

We don't test GuardianEngine rule logic here.
Instead we:

  - use a stub engine that records the last ActionContext it received
  - call the DigiAsset-specific helper methods on GuardianAdapter
  - assert that the ActionContext fields (wallet_id, account_id, value, description)
    are propagated correctly.
"""

from core.guardian_wallet.guardian_adapter import GuardianAdapter
from core.guardian_wallet.engine import ActionContext, GuardianVerdict


class DummyEngine:
    """
    Minimal stub for GuardianEngine.

    It only stores the last ActionContext passed into evaluate()
    and always returns (GuardianVerdict.ALLOW, None).
    """

    def __init__(self):
        self.last_ctx: ActionContext | None = None
        self.evaluate_calls: int = 0

    def evaluate(self, ctx: ActionContext):
        self.last_ctx = ctx
        self.evaluate_calls += 1
        return GuardianVerdict.ALLOW, None


def make_adapter() -> tuple[GuardianAdapter, DummyEngine]:
    engine = DummyEngine()
    adapter = GuardianAdapter(engine=engine)
    return adapter, engine


def test_evaluate_asset_creation_uses_zero_value_and_mint_op():
    adapter, engine = make_adapter()

    decision = adapter.evaluate_asset_creation(
        wallet_id="w1",
        account_id="a1",
        description="Create asset test",
        meta={"test_flag": True},
    )

    # Engine should have been called once
    assert engine.evaluate_calls == 1
    ctx = engine.last_ctx
    assert ctx is not None

    # wallet / account ids preserved
    assert ctx.wallet_id == "w1"
    assert ctx.account_id == "a1"

    # value is zero for creation
    assert ctx.value == 0

    # description propagated
    assert "Create asset test" in ctx.description

    # meta propagated
    assert ctx.meta.get("test_flag") is True

    # Decision is simple ALLOW from DummyEngine
    assert decision.is_allowed()
    assert not decision.needs_approval()
    assert not decision.is_blocked()


def test_evaluate_asset_issuance_sets_amount_and_mint_op_kind():
    adapter, engine = make_adapter()

    decision = adapter.evaluate_asset_issuance(
        wallet_id="w1",
        account_id="a1",
        asset_id="asset-123",
        amount=42,
        description="Issue asset units",
    )

    assert engine.evaluate_calls == 1
    ctx = engine.last_ctx
    assert ctx is not None

    assert ctx.wallet_id == "w1"
    assert ctx.account_id == "a1"
    assert ctx.value == 42
    assert "Issue asset units" in ctx.description

    # Asset id included in meta
    assert ctx.meta.get("asset_id") == "asset-123"

    assert decision.is_allowed()


def test_evaluate_asset_transfer_sets_amount_and_meta():
    adapter, engine = make_adapter()

    decision = adapter.evaluate_asset_transfer(
        wallet_id="wX",
        account_id="aY",
        asset_id="asset-xyz",
        amount=999,
        description="Transfer asset units",
        meta={"custom": "ok"},
    )

    assert engine.evaluate_calls == 1
    ctx = engine.last_ctx
    assert ctx is not None

    assert ctx.wallet_id == "wX"
    assert ctx.account_id == "aY"
    assert ctx.value == 999
    assert "Transfer asset units" in ctx.description
    assert ctx.meta.get("asset_id") == "asset-xyz"
    assert ctx.meta.get("custom") == "ok"

    assert decision.is_allowed()


def test_evaluate_asset_burn_sets_amount_and_meta():
    adapter, engine = make_adapter()

    decision = adapter.evaluate_asset_burn(
        wallet_id="wBurn",
        account_id="aBurn",
        asset_id="asset-burn",
        amount=7,
        description="Burn asset units",
    )

    assert engine.evaluate_calls == 1
    ctx = engine.last_ctx
    assert ctx is not None

    assert ctx.wallet_id == "wBurn"
    assert ctx.account_id == "aBurn"
    assert ctx.value == 7
    assert "Burn asset units" in ctx.description
    assert ctx.meta.get("asset_id") == "asset-burn"

    assert decision.is_allowed()
