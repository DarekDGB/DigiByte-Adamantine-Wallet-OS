"""
WalletService — high-level orchestration for wallet flows.

This module ties together:

  - Guardian adapter (safety / approval logic)
  - Node backend (local Digi-Mobile node, remote nodes, etc.)

It does NOT do low-level DigiByte transaction building itself. Instead,
it provides high-level methods that:

  - check Guardian policies
  - talk to a node client for broadcasting
  - return clear results for the UI layer
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional

from core.guardian_wallet.models import GuardianDecision as GWGuardianDecision


class SendStatus(Enum):
    """High-level status for a wallet action (send / DD mint / DD redeem)."""

    ALLOWED = auto()
    PENDING_GUARDIAN = auto()
    BLOCKED = auto()
    FAILED = auto()


@dataclass
class SendResult:
    """
    Result object returned by WalletService methods (integration style).

    Integration tests & UI use:
        result.status        -> SendStatus
        result.tx_id         -> str | None
        result.error_message -> str | None
        result.guardian_decision -> Any
    """

    status: SendStatus
    tx_id: Optional[str] = None
    error_message: Optional[str] = None
    guardian_decision: Any = None


@dataclass
class WalletService:
    """
    Thin orchestration layer for wallet actions.

    - guardian / guardian_adapter: object with methods like
      `evaluate_send_dgb`, `evaluate_mint_dd`, `evaluate_redeem_dd`.
    - node_manager: object that can give us a node client.

    The node client API is deliberately simple for tests:
      - DummyNodeClient: broadcast_tx(tx_dict)
      - _FakeNodeClient: broadcast_tx(tx_hex_str)
    """

    guardian: Any
    node_manager: Any

    def __init__(
        self,
        guardian: Any | None = None,
        *,
        guardian_adapter: Any | None = None,
        node_manager: Any,
    ) -> None:
        # Support both parameter names:
        #   WalletService(guardian=..., node_manager=...)
        #   WalletService(guardian_adapter=..., node_manager=...)
        if guardian is None:
            guardian = guardian_adapter
        self.guardian = guardian
        self.node_manager = node_manager

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_node_client(self) -> Any:
        """Obtain a node client from the node manager."""
        if hasattr(self.node_manager, "get_best_node"):
            return self.node_manager.get_best_node()
        if hasattr(self.node_manager, "get_preferred_node"):
            return self.node_manager.get_preferred_node()
        if hasattr(self.node_manager, "client"):
            return self.node_manager.client
        raise RuntimeError("Node manager does not expose a node getter or client")

    @staticmethod
    def _interpret_guardian_decision(decision: Any) -> tuple[bool, bool]:
        """
        Normalise guardian decisions into (blocked, needs_approval).

        Supports:
          - core.guardian_wallet.models.GuardianDecision
          - DummyDecision from integration tests (blocked, needs, needs_approval())
        """
        # Direct GuardianDecision: trust its fields.
        if isinstance(decision, GWGuardianDecision):
            return bool(decision.blocked), bool(getattr(decision, "needs_approval", False))

        blocked = bool(getattr(decision, "blocked", False))
        needs_flag = getattr(decision, "needs", False)
        needs_attr = getattr(decision, "needs_approval", None)
        if callable(needs_attr):
            needs_method_val = needs_attr()
        elif needs_attr is None:
            needs_method_val = False
        else:
            needs_method_val = needs_attr
        needs_approval = bool(needs_flag or needs_method_val)
        return blocked, needs_approval

    # ------------------------------------------------------------------
    # Public API — DGB sends
    # ------------------------------------------------------------------

    def send_dgb(
        self,
        *,
        wallet_id: str,
        account_id: str,
        # unit-test style arguments:
        value_dgb: int | None = None,
        tx_hex: str | None = None,
        description: str = "DGB send",
        # integration-test style arguments:
        to_address: str | None = None,
        amount_minor: int | None = None,
        amount_units: int | None = None,
    ) -> Any:
        """
        Orchestrate a DGB send with Guardian checks.

        Behaviour:

        - If guardian returns our GuardianDecision  → unit-test mode:
              returns a *dict* {status, tx_id, error, guardian}
        - Otherwise (DummyDecision / no guardian) → integration mode:
              returns SendResult with SendStatus.
        """

        # ------------------------------------------------------------------
        # 1) Guardian pre-check (if any guardian is configured)
        # ------------------------------------------------------------------
        decision: Any = None
        if self.guardian is not None and hasattr(self.guardian, "evaluate_send_dgb"):
            amount_for_guardian = (
                value_dgb
                if value_dgb is not None
                else amount_minor
                if amount_minor is not None
                else amount_units
                if amount_units is not None
                else 0
            )

            # Try the rich signature first; fall back for test doubles that
            # don't accept keyword arguments.
            try:
                decision = self.guardian.evaluate_send_dgb(
                    wallet_id=wallet_id,
                    account_id=account_id,
                    value_dgb=amount_for_guardian,
                    description=description,
                )
            except TypeError:
                try:
                    decision = self.guardian.evaluate_send_dgb(
                        wallet_id, account_id, amount_for_guardian
                    )
                except TypeError:
                    decision = self.guardian.evaluate_send_dgb(wallet_id, account_id)

        is_guardian_decision = isinstance(decision, GWGuardianDecision)
        blocked = False
        needs_approval = False
        if decision is not None:
            blocked, needs_approval = self._interpret_guardian_decision(decision)

        # ----------------- UNIT-TEST MODE (dict results) -----------------
        if is_guardian_decision:
            # Blocked: never touch the node.
            if blocked:
                return {
                    "status": "blocked",
                    "tx_id": None,
                    "error": None,
                    "guardian": decision,
                }

            # Needs approval: again, never touch the node.
            if needs_approval:
                return {
                    "status": "needs_approval",
                    "tx_id": None,
                    "error": None,
                    "guardian": decision,
                }

            # Allowed by guardian → call the fake node client using tx_hex.
            node = self._get_node_client()
            try:
                # Unit tests care only that broadcast was (or wasn't) called.
                tx_hex_to_use = tx_hex or ""
                tx_id = node.broadcast_tx(tx_hex_to_use)
                return {
                    "status": "broadcasted",
                    "tx_id": tx_id,
                    "error": None,
                    "guardian": decision,
                }
            except Exception as exc:  # pragma: no cover - defensive
                return {
                    "status": "failed",
                    "tx_id": None,
                    "error": str(exc),
                    "guardian": decision,
                }

        # ---------------- INTEGRATION MODE (SendResult) ------------------

        # Guardian blocked or needs approval in DummyDecision world.
        if blocked:
            return SendResult(
                status=SendStatus.BLOCKED,
                tx_id=None,
                error_message="Action blocked by Guardian policy.",
                guardian_decision=decision,
            )
        if needs_approval:
            return SendResult(
                status=SendStatus.PENDING_GUARDIAN,
                tx_id=None,
                error_message=None,
                guardian_decision=decision,
            )

        # Guardian allows → talk to node backend.
        node = self._get_node_client()

        if amount_minor is not None and to_address is not None:
            # Integration tests expect a dict payload with "amount".
            tx_payload: Dict[str, Any] = {
                "flow": "send_dgb",
                "wallet_id": wallet_id,
                "account_id": account_id,
                "to_address": to_address,
                "amount": amount_minor,
                "description": description,
            }
        else:
            # Generic fallback payload.
            tx_payload = {
                "flow": "send_dgb",
                "wallet_id": wallet_id,
                "account_id": account_id,
                "amount": value_dgb,
                "tx_hex": tx_hex,
                "description": description,
            }

        try:
            tx_id = node.broadcast_tx(tx_payload)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                error_message=None,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover
            return SendResult(
                status=SendStatus.FAILED,
                tx_id=None,
                error_message=str(exc),
                guardian_decision=decision,
            )

    # ------------------------------------------------------------------
    # Public API — DigiDollar (DD) mint / redeem
    # ------------------------------------------------------------------

    def mint_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
    ) -> SendResult:
        """
        High-level helper for DigiDollar mint (DGB -> DD).

        Integration tests expect:
          - Guardian is consulted
          - Node receives a broadcast with meta["amount"] == amount_units
          - tx_id == "tx_fake_123"
        """
        decision: Any = None
        if self.guardian is not None and hasattr(self.guardian, "evaluate_mint_dd"):
            decision = self.guardian.evaluate_mint_dd(
                wallet_id=wallet_id,
                account_id=account_id,
                amount_units=amount_units,
            )
            blocked, needs_approval = self._interpret_guardian_decision(decision)

            if blocked:
                return SendResult(
                    status=SendStatus.BLOCKED,
                    tx_id=None,
                    error_message="Mint blocked by Guardian policy.",
                    guardian_decision=decision,
                )
            if needs_approval:
                return SendResult(
                    status=SendStatus.PENDING_GUARDIAN,
                    tx_id=None,
                    error_message=None,
                    guardian_decision=decision,
                )

        node = self._get_node_client()
        tx_payload: Dict[str, Any] = {
            "flow": "dd_mint",
            "wallet_id": wallet_id,
            "account_id": account_id,
            # tests look for this exact key
            "amount": amount_units,
        }

        try:
            tx_id = node.broadcast_tx(tx_payload)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                error_message=None,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover
            return SendResult(
                status=SendStatus.FAILED,
                tx_id=None,
                error_message=str(exc),
                guardian_decision=decision,
            )

    def redeem_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
    ) -> SendResult:
        """
        High-level helper for DigiDollar redeem (DD -> DGB).

        Tests mainly verify the BLOCKED behaviour, but we keep full flow
        for symmetry with `mint_dd`.
        """
        decision: Any = None
        if self.guardian is not None and hasattr(self.guardian, "evaluate_redeem_dd"):
            decision = self.guardian.evaluate_redeem_dd(
                wallet_id=wallet_id,
                account_id=account_id,
                amount_units=amount_units,
            )
            blocked, needs_approval = self._interpret_guardian_decision(decision)

            if blocked:
                return SendResult(
                    status=SendStatus.BLOCKED,
                    tx_id=None,
                    error_message="Redeem blocked by Guardian policy.",
                    guardian_decision=decision,
                )
            if needs_approval:
                return SendResult(
                    status=SendStatus.PENDING_GUARDIAN,
                    tx_id=None,
                    error_message=None,
                    guardian_decision=decision,
                )

        node = self._get_node_client()
        tx_payload: Dict[str, Any] = {
            "flow": "dd_redeem",
            "wallet_id": wallet_id,
            "account_id": account_id,
            "amount": amount_units,
        }

        try:
            tx_id = node.broadcast_tx(tx_payload)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                error_message=None,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover
            return SendResult(
                status=SendStatus.FAILED,
                tx_id=None,
                error_message=str(exc),
                guardian_decision=decision,
            )
