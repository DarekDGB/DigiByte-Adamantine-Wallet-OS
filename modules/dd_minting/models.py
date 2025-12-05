# modules/dd_minting/models.py

"""
Data models for DigiDollar (DD) mint / redeem flows.

These are *wallet-side* models:
- how the UI expresses a mint/redeem request
- how oracles / shield / guardian decisions are represented
- what the engine returns to the rest of the wallet
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum, auto
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Basic value objects
# ---------------------------------------------------------------------------


class FiatCurrency(str, Enum):
    """Supported fiat currencies for pricing and UX."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


@dataclass(frozen=True)
class DGBAmount:
    """Amount of DGB, expressed in whole DGB for UX purposes.

    Internally the node will still operate in satoshis, but the wallet
    can keep this higher-level representation for clarity.
    """

    dgb: Decimal

    def to_satoshis(self) -> int:
        return int(self.dgb * Decimal("100000000"))


@dataclass(frozen=True)
class DDAmount:
    """Amount of DigiDollar (1 DD ≈ 1 unit of reference currency, e.g. 1 USD)."""

    dd: Decimal


@dataclass(frozen=True)
class FiatAmount:
    """A helper type when the UI wants to show 'approximate' fiat value."""

    currency: FiatCurrency
    amount: Decimal


# ---------------------------------------------------------------------------
# Oracle & pricing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OracleQuote:
    """Snapshot of oracle pricing used for a mint / redeem decision."""

    dgb_per_dd: Decimal       # how many DGB to get 1 DD
    timestamp: datetime
    source: str               # e.g. "dgb-dd-oracle-main"


# ---------------------------------------------------------------------------
# Mint / Redeem Requests
# ---------------------------------------------------------------------------


class FlowKind(str, Enum):
    MINT = "MINT"       # DGB -> DD
    REDEEM = "REDEEM"   # DD  -> DGB


@dataclass
class MintQuoteRequest:
    """User asks: 'If I send this much DGB, how much DD do I get?'"""

    from_account_id: str
    dgb_amount: DGBAmount
    preferred_fiat: Optional[FiatCurrency] = None


@dataclass
class RedeemQuoteRequest:
    """User asks: 'If I burn this much DD, how much DGB comes back?'"""

    from_account_id: str
    dd_amount: DDAmount
    preferred_fiat: Optional[FiatCurrency] = None


@dataclass
class MintConfirmRequest:
    """User confirms a previously shown mint quote."""

    from_account_id: str
    dgb_amount: DGBAmount
    expected_dd: DDAmount
    oracle_quote: OracleQuote
    client_reference: str  # UI-side id for tracking / receipts


@dataclass
class RedeemConfirmRequest:
    """User confirms a previously shown redeem quote."""

    from_account_id: str
    dd_amount: DDAmount
    expected_dgb: DGBAmount
    oracle_quote: OracleQuote
    client_reference: str


# ---------------------------------------------------------------------------
# Guardian / risk integration (high level)
# ---------------------------------------------------------------------------


class DDActionRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"


@dataclass
class DDGuardianAssessment:
    """Result of sending mint/redeem context through risk engine + guardian."""

    level: DDActionRiskLevel
    message: Optional[str] = None
    # How long this assessment can be cached before re-check
    ttl: timedelta = timedelta(minutes=5)


# ---------------------------------------------------------------------------
# Engine results
# ---------------------------------------------------------------------------


@dataclass
class DDTxPlan:
    """High-level Tx plan produced by the engine, similar to DigiAssets.

    The actual node-specific transaction building will happen in the
    wallet core / node client layer.
    """

    flow: FlowKind
    from_account_id: str
    dgb_in: DGBAmount
    dd_in: DDAmount
    dgb_out: DGBAmount
    dd_out: DDAmount
    fee_dgb: DGBAmount
    oracle_quote: OracleQuote
    guardian: DDGuardianAssessment
    metadata: Dict[str, str]


@dataclass
class DDQuoteResponse:
    """A user-facing quote (used for both mint and redeem)."""

    flow: FlowKind
    dgb_side: DGBAmount
    dd_side: DDAmount
    approx_fiat: Optional[FiatAmount]
    oracle_quote: OracleQuote
    guardian: Optional[DDGuardianAssessment] = None
    expires_at: Optional[datetime] = None


@dataclass
class DDConfirmResult:
    """Result of confirming a mint/redeem flow."""

    flow: FlowKind
    tx_plan: Optional[DDTxPlan]
    guardian: DDGuardianAssessment
    rejected_reason: Optional[str] = None
