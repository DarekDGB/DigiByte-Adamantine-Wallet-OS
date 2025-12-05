# tests/test_dd_minting_engine.py

"""
Tests for DigiDollar (DD) mint/redeem engine.

We use simple stubs for:
  - oracle service
  - guardian service

to verify:
  - quotes are computed correctly
  - guardian assessments are wired in
  - BLOCKED decisions produce no TxPlan
  - happy-path confirm flows produce a TxPlan
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from modules.dd_minting.engine import (
    DDMintingEngine,
    DDOracleService,
    DDGuardianService,
)

from modules.dd_minting.models import (
    DGBAmount,
    DDAmount,
    FiatCurrency,
    FlowKind,
    OracleQuote,
    MintQuoteRequest,
    RedeemQuoteRequest,
    MintConfirmRequest,
    RedeemConfirmRequest,
    DDActionRiskLevel,
    DDGuardianAssessment,
)


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


class OracleStub(DDOracleService):
    def __init__(self, dgb_per_dd: Decimal = Decimal("10.0")):
        # Example: 1 DD costs 10 DGB
        self.quote = OracleQuote(
            dgb_per_dd=dgb_per_dd,
            timestamp=datetime.now(timezone.utc),
            source="stub-oracle",
        )

    def latest_quote(self) -> OracleQuote:
        return self.quote


class GuardianStub(DDGuardianService):
    def __init__(self, level: DDActionRiskLevel = DDActionRiskLevel.LOW, message: str = ""):
        self.level = level
        self.message = message or f"stub-level={level.value}"
        self.calls = []

    def assess_dd_action(
        self,
        flow: FlowKind,
        dgb_amount: DGBAmount,
        dd_amount: DDAmount,
        context=None,
    ) -> DDGuardianAssessment:
        self.calls.append(
            {
                "flow": flow,
                "dgb": dgb_amount.dgb,
                "dd": dd_amount.dd,
                "context": context or {},
            }
        )
        return DDGuardianAssessment(
            level=self.level,
            message=self.message,
        )


def make_engine(
    dgb_per_dd: str = "10.0",
    guardian_level: DDActionRiskLevel = DDActionRiskLevel.LOW,
):
    oracle = OracleStub(dgb_per_dd=Decimal(dgb_per_dd))
    guardian = GuardianStub(level=guardian_level)
    return DDMintingEngine(oracle=oracle, guardian=guardian), oracle, guardian


# ---------------------------------------------------------------------------
# Tests – Quotes
# ---------------------------------------------------------------------------


def test_mint_quote_basic_math_and_guardian():
    engine, oracle, guardian = make_engine(dgb_per_dd="10.0")

    req = MintQuoteRequest(
        from_account_id="acct-1",
        dgb_amount=DGBAmount(dgb=Decimal("100")),
        preferred_fiat=FiatCurrency.USD,
    )

    quote = engine.get_mint_quote(req)

    # At 10 DGB per DD, 100 DGB => 10 DD
    assert quote.flow == FlowKind.MINT
    assert quote.dgb_side.dgb == Decimal("100")
    assert quote.dd_side.dd == Decimal("10")
    assert quote.oracle_quote == oracle.quote

    # Guardian was called
    assert quote.guardian is not None
    assert quote.guardian.level == DDActionRiskLevel.LOW
    assert guardian.calls, "GuardianStub should have been called at least once"

    # Approx fiat should be around 10 units (1 DD ~= 1 USD)
    assert quote.approx_fiat is not None
    assert quote.approx_fiat.currency == FiatCurrency.USD
    assert quote.approx_fiat.amount == Decimal("10")


def test_redeem_quote_basic_math_and_guardian():
    engine, oracle, guardian = make_engine(dgb_per_dd="5.0")

    req = RedeemQuoteRequest(
        from_account_id="acct-1",
        dd_amount=DDAmount(dd=Decimal("3")),
        preferred_fiat=FiatCurrency.EUR,
    )

    quote = engine.get_redeem_quote(req)

    # At 5 DGB per DD, 3 DD => 15 DGB
    assert quote.flow == FlowKind.REDEEM
    assert quote.dd_side.dd == Decimal("3")
    assert quote.dgb_side.dgb == Decimal("15")
    assert quote.oracle_quote == oracle.quote

    assert quote.guardian is not None
    assert quote.guardian.level == DDActionRiskLevel.LOW
    assert guardian.calls, "GuardianStub should have been called"

    # Approx fiat (for 15 DGB at 5 DGB per DD => 3 DD)
    assert quote.approx_fiat is not None
    assert quote.approx_fiat.currency == FiatCurrency.EUR
    assert quote.approx_fiat.amount == Decimal("3")


# ---------------------------------------------------------------------------
# Tests – Confirm flows
# ---------------------------------------------------------------------------


def test_confirm_mint_blocked_by_guardian_yields_no_tx_plan():
    engine, oracle, _ = make_engine(
        dgb_per_dd="10.0",
        guardian_level=DDActionRiskLevel.BLOCKED,
    )

    req = MintConfirmRequest(
        from_account_id="acct-1",
        dgb_amount=DGBAmount(dgb=Decimal("50")),
        expected_dd=DDAmount(dd=Decimal("5")),
        oracle_quote=oracle.latest_quote(),
        client_reference="mint-123",
    )

    result = engine.confirm_mint(req)

    assert result.flow == FlowKind.MINT
    assert result.tx_plan is None
    assert result.guardian.level == DDActionRiskLevel.BLOCKED
    assert result.rejected_reason is not None


def test_confirm_mint_happy_path_produces_tx_plan():
    engine, oracle, _ = make_engine(
        dgb_per_dd="10.0",
        guardian_level=DDActionRiskLevel.LOW,
    )

    req = MintConfirmRequest(
        from_account_id="acct-1",
        dgb_amount=DGBAmount(dgb=Decimal("50")),
        expected_dd=DDAmount(dd=Decimal("5")),
        oracle_quote=oracle.latest_quote(),
        client_reference="mint-456",
    )

    result = engine.confirm_mint(req)

    assert result.flow == FlowKind.MINT
    assert result.tx_plan is not None
    tx = result.tx_plan

    # 50 DGB in, 0.05 DGB fee (0.1% of 50), so 49.95 out
    assert tx.dgb_in.dgb == Decimal("50")
    assert tx.dd_out.dd == Decimal("5")
    assert tx.fee_dgb.dgb > Decimal("0")
    assert tx.metadata["client_reference"] == "mint-456"


def test_confirm_redeem_blocked_by_guardian_yields_no_tx_plan():
    engine, oracle, _ = make_engine(
        dgb_per_dd="2.0",
        guardian_level=DDActionRiskLevel.BLOCKED,
    )

    req = RedeemConfirmRequest(
        from_account_id="acct-1",
        dd_amount=DDAmount(dd=Decimal("10")),
        expected_dgb=DGBAmount(dgb=Decimal("20")),
        oracle_quote=oracle.latest_quote(),
        client_reference="redeem-001",
    )

    result = engine.confirm_redeem(req)

    assert result.flow == FlowKind.REDEEM
    assert result.tx_plan is None
    assert result.guardian.level == DDActionRiskLevel.BLOCKED
    assert result.rejected_reason is not None


def test_confirm_redeem_happy_path_produces_tx_plan():
    engine, oracle, _ = make_engine(
        dgb_per_dd="2.0",
        guardian_level=DDActionRiskLevel.LOW,
    )

    req = RedeemConfirmRequest(
        from_account_id="acct-1",
        dd_amount=DDAmount(dd=Decimal("10")),
        expected_dgb=DGBAmount(dgb=Decimal("20")),
        oracle_quote=oracle.latest_quote(),
        client_reference="redeem-xyz",
    )

    result = engine.confirm_redeem(req)

    assert result.flow == FlowKind.REDEEM
    assert result.tx_plan is not None
    tx = result.tx_plan

    # 10 DD in, 2 DGB per DD => 20 DGB minus fee
    assert tx.dd_in.dd == Decimal("10")
    assert tx.dgb_out.dgb > Decimal("0")
    assert tx.metadata["client_reference"] == "redeem-xyz"
