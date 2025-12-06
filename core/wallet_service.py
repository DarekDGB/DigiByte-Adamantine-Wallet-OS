"""
WalletService — high-level orchestration for wallet flows.

This module ties together:

  - WalletState (accounts, balances, etc.)
  - GuardianAdapter (safety / approval logic)
  - Node backend (local Digi-Mobile node, remote nodes, etc.)

It does NOT do low-level DigiByte transaction building itself. Instead,
it provides high-level methods that:

  - check Guardian policies
  - talk to a node client for broadcasting
  - return clear results for the UI layer

Unit tests expect three main methods:

  - send_dgb(...)
  - mint_dd(...)
  - redeem_dd(...)

Each returns one of the status strings:

  "blocked" | "needs_approval" | "broadcasted" | "failed"
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
    """High-level status for a DGB send attempt (for future richer APIs)."""
    ALLOWED = auto()
    PENDING_GUARDIAN = auto()
    BLOCKED = auto()
    FAILED = auto()


@dataclass
class SendResult:
    """
    Rich result object for potential future UI usage.

    NOTE: current unit tests only use the simple string statuses returned
    by WalletService methods. This type is kept for future extension.
    """
    status: SendStatus
    tx_id: Optional[str] = None
    guardian_decision: Optional[GuardianDecision] = None
    error_message: Optional[str] = None


class WalletService:
    """
    Thin orchestration layer for wallet actions.

    Tests construct this as:

        WalletService(guardian_adapter=..., node_manager=...)

    or

        WalletService(guardian=..., node_manager=...)

    The `node_manager` is an object that can yield a node client via
    one of:

        - get_best_node()
        - get_active_client()
        - get_preferred_node()
        - .client   (attribute)

    The node client used in tests usually exposes:

        - send_dgb(wallet_id, account_id, amount_units)
        - mint_dd(wallet_id, account_id, amount_units)
        - redeem_dd(wallet_id, account_id, amount_units)
    """

    def __init__(
        self,
        *,
        guardian_adapter: Optional[GuardianAdapter] = None,
        guardian: Optional[GuardianAdapter] = None,
        node_manager: Any,
    ) -> None:
        # Allow both guardian_adapter= and guardian=
        if guardian_adapter is None and guardian is not None:
            guardian_adapter = guardian

        if guardian_adapter is None:
            raise ValueError("WalletService requires a GuardianAdapter (guardian_adapter= or guardian=)")
        if node_manager is None:
            raise ValueError("WalletService requires a node_manager")

        self.guardian: GuardianAdapter = guardian_adapter
        self.node_manager: Any = node_manager

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_node_client(self) -> Any:
        """
        Helper to obtain a node client from the node manager.

        Supports several naming styles so tests can plug in simple fakes.
        """
        mgr = self.node_manager

        if hasattr(mgr, "get_best_node"):
            return mgr.get_best_node()
        if hasattr(mgr, "get_active_client"):
            return mgr.get_active_client()
        if hasattr(mgr, "get_preferred_node"):
            return mgr.get_preferred_node()
        if hasattr(mgr, "client"):
            return mgr.client

        raise RuntimeError("Node manager does not expose a node getter")

    @staticmethod
    def _status_from_decision(decision: GuardianDecision) -> Optional[str]:
        """
        Convert a GuardianDecision into an early status where appropriate.

        Returns:
            "blocked" | "needs_approval" | None
        """
        if decision.is_blocked():
            return "blocked"
        if decision.needs_approval():
            return "needs_approval"
        return None

    # ------------------------------------------------------------------
    # Public API — DGB sends
    # ------------------------------------------------------------------

    def send_dgb(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
        description: str = "DGB send",
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Orchestrate a DGB send with Guardian checks.

        Returns one of:
            "blocked" | "needs_approval" | "broadcasted" | "failed"
        """
        meta = meta or {}

        decision: GuardianDecision = self.guardian.evaluate_send_dgb(
            wallet_id=wallet_id,
            account_id=account_id,
            value_dgb=amount_units,
            description=description,
            meta=meta,
        )

        early = self._status_from_decision(decision)
        if early is not None:
            # BLOCKED or REQUIRE_APPROVAL – do not call the node.
            return early

        # Allowed → talk to node
        client = self._get_node_client()
        try:
            client.send_dgb(
                wallet_id=wallet_id,
                account_id=account_id,
                amount_units=amount_units,
            )
            return "broadcasted"
        except Exception:
            return "failed"

    # ------------------------------------------------------------------
    # Public API — DigiDollar (DD) mint / redeem operations
    # ------------------------------------------------------------------

    def mint_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
        description: str = "Mint DigiDollar (DD)",
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Guarded DigiDollar mint (DGB -> DD).

        Returns:
            "blocked" | "needs_approval" | "broadcasted" | "failed"
        """
        meta = meta or {}

        decision: GuardianDecision = self.guardian.evaluate_mint_dd(
            wallet_id=wallet_id,
            account_id=account_id,
            dgb_value_in=amount_units,
            description=description,
            meta={"flow": "dd_mint", **meta},
        )

        early = self._status_from_decision(decision)
        if early is not None:
            return early

        client = self._get_node_client()
        try:
            client.mint_dd(
                wallet_id=wallet_id,
                account_id=account_id,
                amount_units=amount_units,
            )
            return "broadcasted"
        except Exception:
            return "failed"

    def redeem_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
        description: str = "Redeem DigiDollar (DD)",
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Guarded DigiDollar redeem (DD -> DGB).

        Returns:
            "blocked" | "needs_approval" | "broadcasted" | "failed"
        """
        meta = meta or {}

        decision: GuardianDecision = self.guardian.evaluate_redeem_dd(
            wallet_id=wallet_id,
            account_id=account_id,
            dd_amount=amount_units,
            description=description,
            meta={"flow": "dd_redeem", **meta},
        )

        early = self._status_from_decision(decision)
        if early is not None:
            return early

        client = self._get_node_client()
        try:
            client.redeem_dd(
                wallet_id=wallet_id,
                account_id=account_id,
                amount_units=amount_units,
            )
            return "broadcasted"
        except Exception:
            return "failed"

    # ------------------------------------------------------------------
    # Public API — DigiDollar (DD) *previews* (your original helpers)
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

        # 2) Guardian policy check
        guardian_decision: GuardianDecision = self.guardian.evaluate_mint_dd(
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
            ),
            "guardian_needs_approval": guardian_decision.needs_approval(),
            "guardian_is_blocked": guardian_decision.is_blocked(),
            "guardian_request": (
                asdict(guardian_decision.approval_request)
                if guardian_decision.approval_request is not None
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

        # 2) Guardian policy check
        guardian_decision: GuardianDecision = self.guardian.evaluate_redeem_dd(
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
            ),
            "guardian_needs_approval": guardian_decision.needs_approval(),
            "guardian_is_blocked": guardian_decision.is_blocked(),
            "guardian_request": (
                asdict(guardian_decision.approval_request)
                if guardian_decision.approval_request is not None
                else None
            ),
        }
