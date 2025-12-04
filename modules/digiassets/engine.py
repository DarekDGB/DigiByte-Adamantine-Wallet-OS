# modules/digiassets/engine.py

"""
DigiAssets engine
-----------------

High-level orchestration for DigiAsset minting and transfers.

This module does NOT build raw DigiByte transactions itself.
Instead, it:
  - validates intent (amounts, metadata, basic rules)
  - calls the risk engine for a risk score
  - calls Guardian Wallet to turn that score into a decision
  - returns a plan object that Wallet Core / clients can execute.

Actual TX construction lives in the lower-level wallet / tx builder layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------

class AssetActionType(Enum):
    MINT = auto()
    TRANSFER = auto()
    BURN = auto()


@dataclass(frozen=True)
class AssetId:
    """
    Minimal identifier for a DigiAsset.

    This can be expanded later (e.g. issuer TXID + index) to match the
    DigiAssets v3 spec, but for now we keep it abstract.
    """
    symbol: str  # e.g. "DUSD", "NFT_DRAGON_001"


@dataclass(frozen=True)
class AssetMintRequest:
    asset_id: AssetId
    amount: int  # smallest unit of the asset
    metadata: Dict[str, Any]
    from_account: str  # wallet account / label
    # Optional hooks for DD / compliance / KYC in the future
    purpose: Optional[str] = None


@dataclass(frozen=True)
class AssetTransferRequest:
    asset_id: AssetId
    amount: int
    from_account: str
    to_address: str
    memo: Optional[str] = None


@dataclass(frozen=True)
class AssetActionContext:
    """
    The context we pass to the risk engine and Guardian Wallet.
    """
    action: AssetActionType
    request: Any  # AssetMintRequest | AssetTransferRequest
    # In the future we can add:
    # - current balances
    # - recent activity summary
    # - device / geo hints (if user opts in)
    # - shield / node info (best node, latency, etc.)


class GuardianDecision(Enum):
    ALLOW = auto()
    REQUIRE_CONFIRMATION = auto()
    BLOCK = auto()


@dataclass(frozen=True)
class GuardianOutcome:
    """
    Result of asking Guardian Wallet what to do with this action.
    """
    decision: GuardianDecision
    message: Optional[str] = None
    # e.g. "High value mint, extra confirmation required"


@dataclass(frozen=True)
class TxPlan:
    """
    A high-level transaction plan that other layers can materialize
    into a concrete DigiByte transaction.
    """
    description: str
    # These are intentionally abstract – Wallet Core will expand them.
    inputs_hint: Dict[str, Any]
    outputs_hint: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class AssetEngineResult:
    """
    What the DigiAssets engine returns to the caller (Wallet Core / clients).
    """
    guardian: GuardianOutcome
    risk_score: float
    tx_plan: Optional[TxPlan] = None


# ---------------------------------------------------------------------------
# DigiAssetsEngine
# ---------------------------------------------------------------------------

class DigiAssetsEngine:
    """
    Thin orchestration layer that glues together:
      - risk engine
      - Guardian Wallet
      - wallet / tx builder hints

    It does *not* know how to serialize DigiAssets on-chain formats.
    """

    def __init__(self, risk_engine, guardian_engine, wallet_state):
        """
        Parameters
        ----------
        risk_engine:
            An object with a method `score_asset_action(context: AssetActionContext) -> float`.
        guardian_engine:
            An object with a method
            `evaluate_asset_action(context: AssetActionContext, risk_score: float) -> GuardianOutcome`.
        wallet_state:
            WalletState-like object that can answer balance questions, etc.
            We keep it generic so it matches core/data-models/wallet_state.py.
        """
        self._risk_engine = risk_engine
        self._guardian = guardian_engine
        self._wallet_state = wallet_state

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def plan_mint(self, request: AssetMintRequest) -> AssetEngineResult:
        """
        Entry point for minting new DigiAssets.

        Validates the request, scores the risk, asks Guardian, and if allowed
        builds a high-level TxPlan.
        """
        self._validate_mint_request(request)

        context = AssetActionContext(
            action=AssetActionType.MINT,
            request=request,
        )

        risk_score = self._risk_engine.score_asset_action(context)
        guardian_outcome = self._guardian.evaluate_asset_action(context, risk_score)

        if guardian_outcome.decision == GuardianDecision.BLOCK:
            return AssetEngineResult(
                guardian=guardian_outcome,
                risk_score=risk_score,
                tx_plan=None,
            )

        tx_plan = self._build_mint_plan(request)

        return AssetEngineResult(
            guardian=guardian_outcome,
            risk_score=risk_score,
            tx_plan=tx_plan,
        )

    def plan_transfer(self, request: AssetTransferRequest) -> AssetEngineResult:
        """
        Entry point for transferring existing DigiAssets.
        """
        self._validate_transfer_request(request)

        context = AssetActionContext(
            action=AssetActionType.TRANSFER,
            request=request,
        )

        risk_score = self._risk_engine.score_asset_action(context)
        guardian_outcome = self._guardian.evaluate_asset_action(context, risk_score)

        if guardian_outcome.decision == GuardianDecision.BLOCK:
            return AssetEngineResult(
                guardian=guardian_outcome,
                risk_score=risk_score,
                tx_plan=None,
            )

        tx_plan = self._build_transfer_plan(request)

        return AssetEngineResult(
            guardian=guardian_outcome,
            risk_score=risk_score,
            tx_plan=tx_plan,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _validate_mint_request(self, request: AssetMintRequest) -> None:
        if request.amount <= 0:
            raise ValueError("Mint amount must be positive.")

        if not request.asset_id.symbol:
            raise ValueError("Asset symbol must not be empty.")

        # Example future hooks:
        # - check metadata size
        # - enforce per-asset caps, DD-specific rules, etc.

    def _validate_transfer_request(self, request: AssetTransferRequest) -> None:
        if request.amount <= 0:
            raise ValueError("Transfer amount must be positive.")

        if not request.to_address:
            raise ValueError("Destination address must not be empty.")

        # Basic sanity check using wallet_state (best-effort).
        balance = self._wallet_state.get_asset_balance(
            account_id=request.from_account,
            asset_symbol=request.asset_id.symbol,
        )
        if balance is not None and request.amount > balance:
            raise ValueError("Insufficient asset balance for transfer.")

    def _build_mint_plan(self, request: AssetMintRequest) -> TxPlan:
        """
        Construct a high-level plan for the mint.
        Wallet Core / TX builder will map this into concrete UTXOs and op-returns.
        """
        inputs_hint = {
            "from_account": request.from_account,
            "asset_symbol": request.asset_id.symbol,
            "amount": request.amount,
        }

        outputs_hint = {
            "mint_to_account": request.from_account,
        }

        metadata = dict(request.metadata)
        metadata.setdefault("purpose", request.purpose or "mint")
        metadata.setdefault("engine", "digiassets")

        return TxPlan(
            description=f"Mint {request.amount} of {request.asset_id.symbol}",
            inputs_hint=inputs_hint,
            outputs_hint=outputs_hint,
            metadata=metadata,
        )

    def _build_transfer_plan(self, request: AssetTransferRequest) -> TxPlan:
        inputs_hint = {
            "from_account": request.from_account,
            "asset_symbol": request.asset_id.symbol,
            "amount": request.amount,
        }

        outputs_hint = {
            "to_address": request.to_address,
            "asset_symbol": request.asset_id.symbol,
            "amount": request.amount,
        }

        metadata = {
            "memo": request.memo,
            "engine": "digiassets",
            "purpose": "transfer",
        }

        return TxPlan(
            description=(
                f"Transfer {request.amount} of {request.asset_id.symbol} "
                f"from {request.from_account} to {request.to_address}"
            ),
            inputs_hint=inputs_hint,
            outputs_hint=outputs_hint,
            metadata=metadata,
        )
