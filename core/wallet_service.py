"""
WalletService — high-level orchestration for wallet flows.

This module ties together:

  - GuardianAdapter (safety / approval logic)
  - Node backend (local Digi-Mobile node, remote nodes, etc.)
  - Optional DigiDollar (DD) flows

It does NOT do low-level DigiByte transaction building itself. Instead,
it provides high-level methods that:

  - check Guardian policies
  - talk to a node client for broadcasting
  - return clear results for the UI layer

The actual transaction construction will be implemented later, once the
DigiByte Core / DigiAssets plumbing is in place.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Any, Dict, Optional

from core.guardian_wallet.guardian_adapter import (
    GuardianAdapter,
    GuardianDecision,
)
from modules.dd_minting.engine import DDMintingEngine


class SendStatus(Enum):
    """High-level status for a wallet action."""
    ALLOWED = auto()
    PENDING_GUARDIAN = auto()
    BLOCKED = auto()
    FAILED = auto()


@dataclass
class SendResult:
    """
    Result object returned by WalletService high-level methods.

    This is intentionally wallet- / UI-friendly and does not expose
    low-level Guardian or node internals.
    """
    status: SendStatus
    tx_id: Optional[str] = None
    guardian_decision: Optional[GuardianDecision] = None
    error_message: Optional[str] = None


class WalletService:
    """
    Thin orchestration layer for wallet actions.

    Dependencies are injected so this can be tested easily and wired up
    differently on Android / iOS / Web:

      - guardian / guardian_adapter: GuardianAdapter-like object
      - node_manager: an object that can return the "best" node client
        via `get_best_node()` or `get_preferred_node()` or
        `get_active_client()`.

    Tests construct this in two forms:

        WalletService(guardian_adapter=guardian, node_manager=nodes)
        WalletService(guardian=guardian, node_manager=nodes)
    """

    def __init__(
        self,
        *,
        guardian: Optional[GuardianAdapter] = None,
        node_manager: Any,
        guardian_adapter: Optional[GuardianAdapter] = None,
    ) -> None:
        # Support both keyword styles: guardian= and guardian_adapter=
        if guardian is None and guardian_adapter is not None:
            guardian = guardian_adapter

        self.guardian: Optional[GuardianAdapter] = guardian
        self.node_manager: Any = node_manager

    # ------------------------------------------------------------------
    # Public API — DGB sends
    # ------------------------------------------------------------------

    def send_dgb(
        self,
        *,
        wallet_id: str,
        account_id: str,
        # unit-test style arguments:
        value_dgb: Optional[int] = None,
        tx_hex: Optional[str] = None,
        description: str = "DGB send",
        # integration-test style arguments:
        to_address: Optional[str] = None,
        amount_minor: Optional[int] = None,
        amount_units: Optional[int] = None,
    ) -> SendResult:
        """
        Orchestrate a DGB send with Guardian checks.

        It supports both call styles used in tests:

          * unit tests:
                send_dgb(wallet_id=..., account_id=...,
                         value_dgb=..., tx_hex="00"*10)

          * integration tests:
                send_dgb(wallet_id=..., account_id=...,
                         to_address="dgb1...", amount_minor=1000)
        """
        # Normalised numeric value for guardian + tx payload
        effective_amount = (
            value_dgb
            if value_dgb is not None
            else amount_minor
            if amount_minor is not None
            else amount_units
            if amount_units is not None
            else 0
        )

        # --------------------------------------------------------------
        # 1) Guardian pre-check (if configured)
        # --------------------------------------------------------------
        decision: Optional[GuardianDecision] = None

        if self.guardian is not None and hasattr(self.guardian, "evaluate_send_dgb"):
            # Tests expect the canonical GuardianAdapter signature:
            #   (wallet_id, account_id, value_dgb, description="...", meta=None)
            meta: Optional[Dict[str, Any]] = None
            if to_address is not None or tx_hex is not None:
                meta = {
                    "to_address": to_address,
                    "tx_hex": tx_hex,
                }

            decision = self.guardian.evaluate_send_dgb(  # type: ignore[arg-type]
                wallet_id=wallet_id,
                account_id=account_id,
                value_dgb=effective_amount,
                description=description,
                meta=meta,
            )

            if decision.is_blocked():
                return SendResult(
                    status=SendStatus.BLOCKED,
                    guardian_decision=decision,
                    error_message="Action blocked by Guardian policy.",
                )

            if decision.needs_approval():
                # The UI layer is expected to drive the approval UX.
                return SendResult(
                    status=SendStatus.PENDING_GUARDIAN,
                    guardian_decision=decision,
                )

        # --------------------------------------------------------------
        # 2) Guardian allowed (or not configured) -> talk to node backend
        # --------------------------------------------------------------
        try:
            node_client = self._get_node_client()

            # Payload semantics:
            #   * If tx_hex is provided (unit tests), send raw hex to the node.
            #   * Otherwise, integration tests expect a dict with "amount".
            if tx_hex is not None:
                tx_payload: Any = tx_hex
            else:
                tx_payload = {
                    "wallet_id": wallet_id,
                    "account_id": account_id,
                    "to_address": to_address,
                    "amount": effective_amount,
                    "description": description,
                }

            tx_id = self._broadcast_via_node(node_client, tx_payload)

            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return SendResult(
                status=SendStatus.FAILED,
                guardian_decision=decision,
                error_message=str(exc),
            )

    # ------------------------------------------------------------------
    # Public API — DigiDollar (DD) previews
    # ------------------------------------------------------------------

    def preview_dd_mint(
        self,
        wallet_id: str,
        account_id: str,
        dgb_amount: int,
        dd_engine: DDMintingEngine,
        description: str = "Mint DigiDollar (DD)",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        High-level helper for DigiDollar mint (DGB -> DD).

        Orchestration steps:
          1. Ask the DDMintingEngine for a preview (rates, fees, DD out).
          2. Ask GuardianAdapter if this mint is allowed / needs approval.
          3. Return a single dict that UI / clients can consume.
        """
        meta = meta or {}

        # 1) Core DD economics + constraints
        preview = dd_engine.preview_mint(
            wallet_id=wallet_id,
            account_id=account_id,
            dgb_in=dgb_amount,
            meta=meta,
        )

        # 2) Guardian policy check (if Guardian is configured)
        guardian_decision: Optional[GuardianDecision] = None
        if self.guardian is not None and hasattr(self.guardian, "evaluate_mint_dd"):
            guardian_decision = self.guardian.evaluate_mint_dd(  # type: ignore[arg-type]
                wallet_id=wallet_id,
                account_id=account_id,
                dgb_value_in=dgb_amount,
                description=description,
                meta={"flow": "dd_mint", **meta},
            )

        # 3) Normalised response
        return {
            "wallet_id": wallet_id,
            "account_id": account_id,
            "flow": "dd_mint",
            "dd_preview": asdict(preview),
            "guardian_verdict": getattr(
                guardian_decision.verdict, "name", str(guardian_decision.verdict)
            )
            if guardian_decision is not None
            else None,
            "guardian_needs_approval": guardian_decision.needs_approval()
            if guardian_decision is not None
            else False,
            "guardian_is_blocked": guardian_decision.is_blocked()
            if guardian_decision is not None
            else False,
            "guardian_request": (
                asdict(guardian_decision.approval_request)
                if guardian_decision is not None
                and guardian_decision.approval_request is not None
                else None
            ),
        }

    def preview_dd_redeem(
        self,
        wallet_id: str,
        account_id: str,
        dd_amount: int,
        dd_engine: DDMintingEngine,
        description: str = "Redeem DigiDollar (DD)",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        High-level helper for DigiDollar redeem (DD -> DGB).

        Orchestration steps:
          1. Ask DDMintingEngine for a redeem preview.
          2. Ask GuardianAdapter whether this redeem is allowed.
          3. Return a single dict for UI / clients.
        """
        meta = meta or {}

        # 1) Core DD economics + constraints
        preview = dd_engine.preview_redeem(
            wallet_id=wallet_id,
            account_id=account_id,
            dd_amount=dd_amount,
            meta=meta,
        )

        # 2) Guardian policy check (if configured)
        guardian_decision: Optional[GuardianDecision] = None
        if self.guardian is not None and hasattr(self.guardian, "evaluate_redeem_dd"):
            guardian_decision = self.guardian.evaluate_redeem_dd(  # type: ignore[arg-type]
                wallet_id=wallet_id,
                account_id=account_id,
                dd_amount=dd_amount,
                description=description,
                meta={"flow": "dd_redeem", **meta},
            )

        # 3) Normalised response
        return {
            "wallet_id": wallet_id,
            "account_id": account_id,
            "flow": "dd_redeem",
            "dd_preview": asdict(preview),
            "guardian_verdict": getattr(
                guardian_decision.verdict, "name", str(guardian_decision.verdict)
            )
            if guardian_decision is not None
            else None,
            "guardian_needs_approval": guardian_decision.needs_approval()
            if guardian_decision is not None
            else False,
            "guardian_is_blocked": guardian_decision.is_blocked()
            if guardian_decision is not None
            else False,
            "guardian_request": (
                asdict(guardian_decision.approval_request)
                if guardian_decision is not None
                and guardian_decision.approval_request is not None
                else None
            ),
        }

    # ------------------------------------------------------------------
    # Public API — DigiDollar (DD) execution flows
    # ------------------------------------------------------------------

    def mint_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
        description: str = "Mint DigiDollar (DD)",
    ) -> SendResult:
        """
        Execute a DigiDollar mint (DD units out).

        Tests expect:
          - Guardian called (if present)
          - Node client invoked when ALLOW
          - SendResult with proper status + tx_id
        """
        decision: Optional[GuardianDecision] = None

        if self.guardian is not None and hasattr(self.guardian, "evaluate_mint_dd"):
            decision = self.guardian.evaluate_mint_dd(  # type: ignore[arg-type]
                wallet_id=wallet_id,
                account_id=account_id,
                amount_units=amount_units,
                description=description,
                meta={"flow": "dd_mint"},
            )

            if decision.is_blocked():
                return SendResult(
                    status=SendStatus.BLOCKED,
                    guardian_decision=decision,
                    error_message="DigiDollar mint blocked by Guardian policy.",
                )

            if decision.needs_approval():
                return SendResult(
                    status=SendStatus.PENDING_GUARDIAN,
                    guardian_decision=decision,
                )

        try:
            node_client = self._get_node_client()
            tx_payload = {
                "flow": "dd_mint",
                "wallet_id": wallet_id,
                "account_id": account_id,
                "amount_units": amount_units,
                "description": description,
            }
            tx_id = self._broadcast_via_node(node_client, tx_payload)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return SendResult(
                status=SendStatus.FAILED,
                guardian_decision=decision,
                error_message=str(exc),
            )

    def redeem_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
        description: str = "Redeem DigiDollar (DD)",
    ) -> SendResult:
        """
        Execute a DigiDollar redeem (DD units -> DGB).

        Tests expect BLOCKED redemptions to never hit the node.
        """
        decision: Optional[GuardianDecision] = None

        if self.guardian is not None and hasattr(self.guardian, "evaluate_redeem_dd"):
            decision = self.guardian.evaluate_redeem_dd(  # type: ignore[arg-type]
                wallet_id=wallet_id,
                account_id=account_id,
                amount_units=amount_units,
                description=description,
                meta={"flow": "dd_redeem"},
            )

            if decision.is_blocked():
                return SendResult(
                    status=SendStatus.BLOCKED,
                    guardian_decision=decision,
                    error_message="DigiDollar redeem blocked by Guardian policy.",
                )

            if decision.needs_approval():
                return SendResult(
                    status=SendStatus.PENDING_GUARDIAN,
                    guardian_decision=decision,
                )

        try:
            node_client = self._get_node_client()
            tx_payload = {
                "flow": "dd_redeem",
                "wallet_id": wallet_id,
                "account_id": account_id,
                "amount_units": amount_units,
                "description": description,
            }
            tx_id = self._broadcast_via_node(node_client, tx_payload)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return SendResult(
                status=SendStatus.FAILED,
                guardian_decision=decision,
                error_message=str(exc),
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_node_client(self) -> Any:
        """
        Helper to obtain a node client from the node manager.

        We support `get_best_node()`, `get_preferred_node()`,
        `get_active_client()` and `get_node()` naming to keep this
        adapter flexible across different layers.
        """
        if hasattr(self.node_manager, "get_best_node"):
            return self.node_manager.get_best_node()

        if hasattr(self.node_manager, "get_preferred_node"):
            return self.node_manager.get_preferred_node()

        if hasattr(self.node_manager, "get_active_client"):
            return self.node_manager.get_active_client()

        if hasattr(self.node_manager, "get_node"):
            return self.node_manager.get_node()

        raise RuntimeError("Node manager does not expose a node getter")

    def _broadcast_via_node(self, node_client: Any, tx_payload: Any) -> str:
        """
        Try several common method names for broadcasting a transaction.

        Tests use Dummy / Fake node clients that expose `broadcast_tx`,
        while real nodes might use JSON-RPC raw tx methods.
        """
        for method_name in ("broadcast_tx", "broadcast_raw_tx", "sendrawtransaction"):
            if hasattr(node_client, method_name):
                method = getattr(node_client, method_name)
                return method(tx_payload)

        raise RuntimeError("Node client does not expose a broadcast method")
