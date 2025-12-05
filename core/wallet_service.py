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

The actual transaction construction will be implemented later, once the
DigiByte Core / DigiAssets plumbing is in place.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Any, Dict, Optional

from core.guardian_wallet.adapter import GuardianAdapter, GuardianDecision
from modules.dd_minting.engine import DDMintingEngine


class SendStatus(Enum):
    """High-level status for a DGB send attempt."""
    ALLOWED = auto()
    PENDING_GUARDIAN = auto()
    BLOCKED = auto()
    FAILED = auto()


@dataclass
class SendResult:
    """
    Result object returned by WalletService.send_dgb().

    This is intentionally wallet- / UI-friendly and does not expose
    low-level Guardian or node internals.
    """
    status: SendStatus
    tx_id: Optional[str] = None
    guardian_decision: Optional[GuardianDecision] = None
    error_message: Optional[str] = None


@dataclass
class WalletService:
    """
    Thin orchestration layer for wallet actions.

    Dependencies are injected so this can be tested easily and wired up
    differently on Android / iOS / Web:

      - guardian: GuardianAdapter
      - node_manager: an object that can return the "best" node client
        via `get_best_node()` or `get_preferred_node()`.

    The node client itself is expected to expose a `broadcast_tx(tx)`
    method that returns a tx_id string. For now, this is abstract and
    can be mocked in tests.
    """

    guardian: GuardianAdapter
    node_manager: Any  # NodeManager-like object

    # ------------------------------------------------------------------
    # Public API — DGB sends
    # ------------------------------------------------------------------

    def send_dgb(
        self,
        wallet_id: str,
        account_id: str,
        to_address: str,
        amount_minor: int,
        description: str = "DGB send",
    ) -> SendResult:
        """
        Orchestrate a DGB send with Guardian checks.

        Steps:
          1. Ask GuardianAdapter if the action is allowed.
          2. If BLOCKED -> return blocked result.
          3. If REQUIRE_APPROVAL -> return pending result (UI should
             surface guardian approval flow).
          4. If ALLOW -> build a placeholder tx and ask the node client
             to broadcast it.

        NOTE: actual transaction construction is left as a future step.
        Here we only model the control flow and node interaction.
        """
        # 1) Guardian pre-check
        decision = self.guardian.evaluate_send_dgb(
            wallet_id=wallet_id,
            account_id=account_id,
            value_dgb=amount_minor,
            description=description,
            meta={"to_address": to_address},
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

        # 2) Guardian allowed -> talk to node backend
        try:
            node_client = self._get_node_client()
            # Placeholder transaction object. In the future this will be
            # replaced with a real DigiByte transaction structure.
            tx = {
                "from_account": account_id,
                "to_address": to_address,
                "amount": amount_minor,
                "description": description,
            }

            tx_id = node_client.broadcast_tx(tx)  # type: ignore[attr-defined]

            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_node_client(self) -> Any:
        """
        Helper to obtain a node client from the node manager.

        We support both `get_best_node()` and `get_preferred_node()`
        naming to keep this adapter flexible.
        """
        if hasattr(self.node_manager, "get_best_node"):
            return self.node_manager.get_best_node()
        if hasattr(self.node_manager, "get_preferred_node"):
            return self.node_manager.get_preferred_node()

        raise RuntimeError("Node manager does not expose a node getter")
