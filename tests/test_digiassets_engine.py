# tests/test_digiassets_engine.py

"""
Basic tests for DigiAssetsEngine.

These tests make sure that:
  - mint / transfer flows call the risk engine and guardian
  - guardian decisions are respected (BLOCK => no TxPlan)
  - simple validation (amounts, balances) behaves as expected
"""

import pytest

from modules.digiassets.engine import (
    AssetId,
    AssetMintRequest,
    AssetTransferRequest,
    DigiAssetsEngine,
    GuardianDecision,
    GuardianOutcome,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class RiskEngineStub:
    def __init__(self, score: float = 0.1):
        self.score = score
        self.calls = []

    def score_asset_action(self, context):
        self.calls.append(context)
        return self.score


class GuardianEngineStub:
    def __init__(self, decision: GuardianDecision = GuardianDecision.ALLOW):
        self.decision = decision
        self.calls = []

    def evaluate_asset_action(self, context, risk_score: float) -> GuardianOutcome:
        self.calls.append((context, risk_score))
        # Simple rule: use configured decision, attach a tiny message
        return GuardianOutcome(
            decision=self.decision,
            message=f"stub decision={self.decision.name}",
        )


class WalletStateStub:
    def __init__(self, balances=None):
        # balances: {(account_id, asset_symbol): amount}
        self.balances = balances or {}

    def get_asset_balance(self, account_id: str, asset_symbol: str):
        return self.balances.get((account_id, asset_symbol))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def make_engine(
    risk_score: float = 0.1,
    guardian_decision: GuardianDecision = GuardianDecision.ALLOW,
    balances=None,
) -> DigiAssetsEngine:
    risk = RiskEngineStub(score=risk_score)
    guardian = GuardianEngineStub(decision=guardian_decision)
    wallet_state = WalletStateStub(balances=balances)
    engine = DigiAssetsEngine(risk_engine=risk, guardian_engine=guardian, wallet_state=wallet_state)
    return engine


def test_mint_happy_path_creates_tx_plan():
    engine = make_engine(risk_score=0.2, guardian_decision=GuardianDecision.ALLOW)

    request = AssetMintRequest(
        asset_id=AssetId(symbol="TESTASSET"),
        amount=1000,
        metadata={"name": "Test Asset"},
        from_account="account_1",
    )

    result = engine.plan_mint(request)

    # Risk + guardian were called
    assert result.risk_score == 0.2
    assert result.guardian.decision == GuardianDecision.ALLOW
    assert result.tx_plan is not None

    # TxPlan has some basic hints wired correctly
    plan = result.tx_plan
    assert "Mint" in plan.description
    assert plan.inputs_hint["from_account"] == "account_1"
    assert plan.inputs_hint["asset_symbol"] == "TESTASSET"
    assert plan.metadata["engine"] == "digiassets"
    assert plan.metadata["purpose"] == "mint"


def test_mint_blocked_by_guardian_has_no_tx_plan():
    engine = make_engine(
        risk_score=0.9,
        guardian_decision=GuardianDecision.BLOCK,
    )

    request = AssetMintRequest(
        asset_id=AssetId(symbol="RISKY"),
        amount=1,
        metadata={},
        from_account="account_1",
    )

    result = engine.plan_mint(request)

    assert result.guardian.decision == GuardianDecision.BLOCK
    assert result.tx_plan is None


def test_transfer_fails_on_insufficient_balance():
    # Wallet has only 10 units of TESTASSET
    balances = {("source_account", "TESTASSET"): 10}
    engine = make_engine(balances=balances)

    request = AssetTransferRequest(
        asset_id=AssetId(symbol="TESTASSET"),
        amount=20,  # more than balance
        from_account="source_account",
        to_address="dgb1qexample",
    )

    with pytest.raises(ValueError):
        engine.plan_transfer(request)


def test_transfer_happy_path_builds_tx_plan():
    balances = {("source_account", "TESTASSET"): 100}
    engine = make_engine(balances=balances)

    request = AssetTransferRequest(
        asset_id=AssetId(symbol="TESTASSET"),
        amount=25,
        from_account="source_account",
        to_address="dgb1qdestination",
        memo="hello",
    )

    result = engine.plan_transfer(request)

    assert result.guardian.decision == GuardianDecision.ALLOW
    assert result.tx_plan is not None

    plan = result.tx_plan
    assert plan.outputs_hint["to_address"] == "dgb1qdestination"
    assert plan.outputs_hint["amount"] == 25
    assert plan.metadata["purpose"] == "transfer"
    assert plan.metadata["engine"] == "digiassets"
