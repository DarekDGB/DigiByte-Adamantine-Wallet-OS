# modules/dd_minting/engine.py

"""
DigiDollar (DD) mint / redeem orchestration.

This module glues together:

- pricing oracles
- guardian / risk assessments
- high-level Tx planning for DGB <-> DD flows

It does NOT:
- talk directly to nodes
- build raw DigiByte transactions
- persist anything

Those concerns live in wallet core / node client layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Protocol, Optional, Dict

from .models import (
    DGBAmount,
    DDAmount,
    FiatAmount,
    FiatCurrency,
    FlowKind,
    OracleQuote,
    MintQuoteRequest,
    RedeemQuoteRequest,
    MintConfirmRequest,
    RedeemConfirmRequest,
    DDGuardianAssessment,
    DDActionRiskLevel,
    DDTxPlan,
    DDQuoteResponse,
)


# ---------------------------------------------------------------------------
# Service interfaces (to be wired by wallet core)
# ---------------------------------------------------------------------------


class DDOracleService(Protocol):
    """Abstract pricing oracle for DGB <-> DD.

    Implementations might aggregate multiple feeds, apply smoothing,
    or enforce staleness limits.
    """

    def latest_quote(self) -> OracleQuote:
        ...


class DDGuardianService(Protocol):
    """Abstract interface to guardian / risk engine.

    The engine only cares about a high-level assessment; the concrete
    implementation can talk to Sentinel, DQSN, risk-engine, etc.
    """

    def assess_dd_action(
        self,
        flow: FlowKind,
        dgb_amount: DGBAmount,
        dd_amount: DDAmount,
        context: Optional[Dict[str, str]] = None,
    ) -> DDGuardianAssessment:
        ...


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _approx_fiat(
    currency: Optional[FiatCurrency],
    dgb_amount: DGBAmount,
    quote: OracleQuote,
) -> Optional[FiatAmount]:
    """Very rough fiat approximation.

    For now we treat 1 DD ≈ 1 reference unit (e.g. 1 USD) and DD side
    is already encoded in the quote math. Wallet UIs can choose to
    enrich this later with proper FX feeds.
    """
    if currency is None:
        return None

    # dgb_amount -> equivalent DD
    dd_equiv = dgb_amount.dgb / quote.dgb_per_dd
    return FiatAmount(currency=currency, amount=dd_equiv)


def _quote_expiry(now: datetime, ttl: timedelta = timedelta(minutes=5)) -> datetime:
    return now + ttl


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


@dataclass
class DDMintingEngine:
    """Pure-orchestration engine for DD mint / redeem flows."""

    oracle: DDOracleService
    guardian: DDGuardianService

    quote_ttl: timedelta = timedelta(minutes=5)

    # --------------------- QUOTES -----------------------------------------

    def get_mint_quote(self, req: MintQuoteRequest) -> DDQuoteResponse:
        """Compute DGB -> DD quote."""
        now = datetime.now(timezone.utc)
        quote = self.oracle.latest_quote()

        dd_out = DDAmount(dd=req.dgb_amount.dgb / quote.dgb_per_dd)

        guardian_assessment = self.guardian.assess_dd_action(
            flow=FlowKind.MINT,
            dgb_amount=req.dgb_amount,
            dd_amount=dd_out,
            context={"from_account_id": req.from_account_id},
        )

        approx = _approx_fiat(req.preferred_fiat, req.dgb_amount, quote)

        return DDQuoteResponse(
            flow=FlowKind.MINT,
            dgb_side=req.dgb_amount,
            dd_side=dd_out,
            approx_fiat=approx,
            oracle_quote=quote,
            guardian=guardian_assessment,
            expires_at=_quote_expiry(now, self.quote_ttl),
        )

    def get_redeem_quote(self, req: RedeemQuoteRequest) -> DDQuoteResponse:
        """Compute DD -> DGB quote."""
        now = datetime.now(timezone.utc)
        quote = self.oracle.latest_quote()

        dgb_out = DGBAmount(dgb=req.dd_amount.dd * quote.dgb_per_dd)

        guardian_assessment = self.guardian.assess_dd_action(
            flow=FlowKind.REDEEM,
            dgb_amount=dgb_out,
            dd_amount=req.dd_amount,
            context={"from_account_id": req.from_account_id},
        )

        approx = _approx_fiat(req.preferred_fiat, dgb_out, quote)

        return DDQuoteResponse(
            flow=FlowKind.REDEEM,
            dgb_side=dgb_out,
            dd_side=req.dd_amount,
            approx_fiat=approx,
            oracle_quote=quote,
            guardian=guardian_assessment,
            expires_at=_quote_expiry(now, self.quote_ttl),
        )

    # --------------------- CONFIRMATION -----------------------------------

    def confirm_mint(self, req: MintConfirmRequest) -> "DDConfirmResult":
        """Re-check guardian + oracle and produce a Tx plan.

        The wallet core will take the Tx plan and construct the actual
        DigiByte transactions.
        """
        # Recompute DD based on provided oracle (defensive)
        dd_out = DDAmount(dd=req.dgb_amount.dgb / req.oracle_quote.dgb_per_dd)

        guardian_assessment = self.guardian.assess_dd_action(
            flow=FlowKind.MINT,
            dgb_amount=req.dgb_amount,
            dd_amount=dd_out,
            context={"client_reference": req.client_reference},
        )

        # If guardian blocks, do not produce a Tx plan
        if guardian_assessment.level == DDActionRiskLevel.BLOCKED:
            from .models import DDConfirmResult  # local import to avoid circulars

            return DDConfirmResult(
                flow=FlowKind.MINT,
                tx_plan=None,
                guardian=guardian_assessment,
                rejected_reason=guardian_assessment.message
                or "Mint blocked by guardian policy",
            )

        # Simple fee model for now: flat % of DGB in
        fee = DGBAmount(dgb=req.dgb_amount.dgb * Decimal("0.001"))

        tx_plan = DDTxPlan(
            flow=FlowKind.MINT,
            from_account_id=req.from_account_id,
            dgb_in=req.dgb_amount,
            dd_in=DDAmount(dd=Decimal("0")),
            dgb_out=DGBAmount(dgb=req.dgb_amount.dgb - fee.dgb),
            dd_out=dd_out,
            fee_dgb=fee,
            oracle_quote=req.oracle_quote,
            guardian=guardian_assessment,
            metadata={"client_reference": req.client_reference},
        )

        from .models import DDConfirmResult  # local import to avoid circulars

        return DDConfirmResult(
            flow=FlowKind.MINT,
            tx_plan=tx_plan,
            guardian=guardian_assessment,
            rejected_reason=None,
        )

    def confirm_redeem(self, req: RedeemConfirmRequest) -> "DDConfirmResult":
        """Re-check guardian + oracle and produce a Tx plan for redeem."""
        dgb_out = DGBAmount(dgb=req.dd_amount.dd * req.oracle_quote.dgb_per_dd)

        guardian_assessment = self.guardian.assess_dd_action(
            flow=FlowKind.REDEEM,
            dgb_amount=dgb_out,
            dd_amount=req.dd_amount,
            context={"client_reference": req.client_reference},
        )

        if guardian_assessment.level == DDActionRiskLevel.BLOCKED:
            from .models import DDConfirmResult

            return DDConfirmResult(
                flow=FlowKind.REDEEM,
                tx_plan=None,
                guardian=guardian_assessment,
                rejected_reason=guardian_assessment.message
                or "Redeem blocked by guardian policy",
            )

        fee = DGBAmount(dgb=dgb_out.dgb * Decimal("0.001"))

        tx_plan = DDTxPlan(
            flow=FlowKind.REDEEM,
            from_account_id=req.from_account_id,
            dgb_in=DGBAmount(dgb=Decimal("0")),
            dd_in=req.dd_amount,
            dgb_out=DGBAmount(dgb=dgb_out.dgb - fee.dgb),
            dd_out=DDAmount(dd=Decimal("0")),
            fee_dgb=fee,
            oracle_quote=req.oracle_quote,
            guardian=guardian_assessment,
            metadata={"client_reference": req.client_reference},
        )

        from .models import DDConfirmResult

        return DDConfirmResult(
            flow=FlowKind.REDEEM,
            tx_plan=tx_plan,
            guardian=guardian_assessment,
            rejected_reason=None,
        )
