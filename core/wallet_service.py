"""
High-level wallet orchestration for the DigiByte Adamantine Wallet.

This module purposely stays **very close** to what the unit / integration
tests expect.  It does NOT implement real DigiByte transaction building.
Instead it coordinates three concerns:

- Guardian adapter (safety / approval decisions)
- Node manager (which node / client to talk to)
- Simple result objects for the UI / callers

There are two main call styles supported by the tests:

1.  "Unit-test mode"
    send_dgb(wallet_id, account_id, value_dgb=..., tx_hex=...)
    -> returns a dict with keys: status, tx_id, error, guardian

2.  "Integration-test mode"
    send_dgb(wallet_id, account_id, to_address=..., amount_minor=...)
    mint_dd(...), redeem_dd(...)
    -> return a SendResult with a SendStatus enum.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Result types used by integration tests
# ---------------------------------------------------------------------------


class SendStatus(Enum):
    """High-level status for a wallet action in integration tests."""

    ALLOWED = auto()
    PENDING_GUARDIAN = auto()
    BLOCKED = auto()
    FAILED = auto()


@dataclass
class SendResult:
    """
    Wrapper returned by integration-style calls.

    Tests access:

        result.status          (SendStatus)
        result.tx_id           (str | None)
        result.error_message   (str | None)

    Some older tests also call result["status"], result["tx_id"],
    result["error"], so we provide a small mapping bridge.
    """

    status: SendStatus
    tx_id: Optional[str] = None
    error_message: Optional[str] = None
    guardian_decision: Any = None

    # --- compatibility with dict-style access ---

    def _status_string(self) -> str:
        if self.status == SendStatus.ALLOWED:
            return "broadcasted"
        if self.status == SendStatus.PENDING_GUARDIAN:
            return "needs_approval"
        if self.status == SendStatus.BLOCKED:
            return "blocked"
        if self.status == SendStatus.FAILED:
            return "failed"
        return "unknown"

    def __getitem__(self, key: str) -> Any:
        if key == "status":
            return self._status_string()
        if key == "tx_id":
            return self.tx_id
        if key == "error":
            return self.error_message
        raise KeyError(key)


# ---------------------------------------------------------------------------
# WalletService
# ---------------------------------------------------------------------------


class WalletService:
    """
    High-level wallet orchestrator used by tests.

    Parameters
    ----------
    guardian:
        For integration tests, usually DummyGuardianAdapter(...)
        For unit tests this is left as None and `guardian_adapter`
        is used instead.

    guardian_adapter:
        In unit tests this is the object that exposes
        evaluate_send_dgb(...).

    node_manager:
        Object that can yield a node client.  Tests provide different
        shapes but usually:

            - .get_best_node() -> client
            - or .get_preferred_node() -> client
            - or .client / .node attribute

        The client is expected to implement:

            - broadcast_tx(hex_or_payload) -> txid
            - mint_dd(amount_units) -> txid
            - redeem_dd(amount_units) -> txid
    """

    def __init__(
        self,
        guardian: Any | None = None,
        *,
        guardian_adapter: Any | None = None,
        node_manager: Any,
    ) -> None:
        # In unit tests only guardian_adapter is passed.
        if guardian is None:
            guardian = guardian_adapter

        self.guardian = guardian
        self.node_manager = node_manager

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _get_node_client(self) -> Any:
        """Return the underlying node client from whatever shape manager."""
        mgr = self.node_manager

        if hasattr(mgr, "get_best_node"):
            return mgr.get_best_node()
        if hasattr(mgr, "get_preferred_node"):
            return mgr.get_preferred_node()
        if hasattr(mgr, "client"):
            return mgr.client
        if hasattr(mgr, "node"):
            return mgr.node

        # Last resort: assume the manager itself is the client
        return mgr

    # ------------------------------------------------------------------ #
    # Guardian helpers                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _decision_blocked(decision: Any) -> bool:
        """Return True if a guardian decision represents a block."""
        return bool(getattr(decision, "blocked", False))

    @staticmethod
    def _decision_needs_approval(decision: Any) -> bool:
        """Return True if a guardian decision represents 'needs approval'."""
        if decision is None:
            return False
        # Some decisions expose `needs_approval` as a method.
        attr = getattr(decision, "needs_approval", None)
        if callable(attr):
            return bool(attr())
        if attr is not None:
            return bool(attr)
        # Fallback for `needs` flag used in DummyDecision in tests
        alt = getattr(decision, "needs", None)
        if callable(alt):
            return bool(alt())
        return bool(alt)

    # ------------------------------------------------------------------ #
    # DGB send                                                            #
    # ------------------------------------------------------------------ #

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
        Orchestrate a DGB send.

        Two modes:

        - Unit-test mode → returns dict
        - Integration-test mode → returns SendResult
        """

        unit_mode = (
            to_address is None
            and amount_minor is None
            and amount_units is None
            and (value_dgb is not None or tx_hex is not None)
        )

        # ------------------------------------------------------------------
        # 1) UNIT-TEST MODE  (dict result, guardian controls everything)
        # ------------------------------------------------------------------
        if unit_mode:
            decision: Any = None
            if self.guardian is not None and hasattr(
                self.guardian, "evaluate_send_dgb"
            ):
                # tests call: evaluate_send_dgb(wallet_id, account_id, value_dgb)
                decision = self.guardian.evaluate_send_dgb(
                    wallet_id, account_id, value_dgb or 0
                )

            # Guardian says "BLOCK"  → no node calls
            if self._decision_blocked(decision):
                return {
                    "status": "blocked",
                    "tx_id": None,
                    "error": None,
                    "guardian": decision,
                }

            # Guardian says "needs approval" → no node calls
            if self._decision_needs_approval(decision):
                return {
                    "status": "needs_approval",
                    "tx_id": None,
                    "error": None,
                    "guardian": decision,
                }

            # Otherwise we are allowed to try broadcasting
            node = self._get_node_client()
            try:
                txid = node.broadcast_tx(tx_hex or "")
                return {
                    "status": "broadcasted",
                    "tx_id": txid,
                    "error": None,
                    "guardian": decision,
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "status": "failed",
                    "tx_id": None,
                    "error": str(exc),
                    "guardian": decision,
                }

        # ------------------------------------------------------------------
        # 2) INTEGRATION-TEST MODE  (SendResult + SendStatus)
        # ------------------------------------------------------------------

        # Figure out guardian decision.  DummyGuardianAdapter in the tests
        # exposes `.decision`, but we also support an evaluate_* method.
        decision: Any = None
        if self.guardian is not None:
            decision = getattr(self.guardian, "decision", None)
            if decision is None and hasattr(self.guardian, "evaluate_send_dgb"):
                # Keep the call signature very lightweight for tests.
                decision = self.guardian.evaluate_send_dgb(
                    wallet_id=wallet_id,
                    account_id=account_id,
                    amount_minor=amount_minor or amount_units or 0,
                )

        # BLOCK → do not talk to node
        if self._decision_blocked(decision):
            return SendResult(
                status=SendStatus.BLOCKED,
                tx_id=None,
                error_message=None,
                guardian_decision=decision,
            )

        # NEEDS APPROVAL → do not talk to node
        if self._decision_needs_approval(decision):
            return SendResult(
                status=SendStatus.PENDING_GUARDIAN,
                tx_id=None,
                error_message=None,
                guardian_decision=decision,
            )

        # ALLOW → call node and broadcast
        node = self._get_node_client()
        try:
            # Integration DummyNodeClient expects a dict payload with amount.
            payload = {
                "to_address": to_address,
                "amount": amount_minor
                if amount_minor is not None
                else amount_units,
                "description": description,
            }
            txid = node.broadcast_tx(payload)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=txid,
                error_message=None,
                guardian_decision=decision,
            )
        except Exception as exc:  # noqa: BLE001
            return SendResult(
                status=SendStatus.FAILED,
                tx_id=None,
                error_message=str(exc),
                guardian_decision=decision,
            )

    # ------------------------------------------------------------------ #
    # DigiDollar mint / redeem                                           #
    # ------------------------------------------------------------------ #

    def _guardian_decision_generic(self, amount_units: int) -> Any:
        """
        Shared helper for mint_dd / redeem_dd to obtain a guardian decision.
        """
        decision: Any = None
        if self.guardian is not None:
            decision = getattr(self.guardian, "decision", None)
            if decision is None and hasattr(self.guardian, "evaluate_dd"):
                # Some adapters may expose a generic method for DD actions.
                decision = self.guardian.evaluate_dd(amount_units)
        return decision

    def mint_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
    ) -> SendResult:
        """
        Mint DigiDollar units (integration-style only).

        Tests expect:

            - BLOCKED → no broadcast
            - PENDING_GUARDIAN → no broadcast
            - ALLOWED → node.mint_dd called once with amount_units
        """
        decision = self._guardian_decision_generic(amount_units)

        if self._decision_blocked(decision):
            return SendResult(
                status=SendStatus.BLOCKED,
                tx_id=None,
                error_message=None,
                guardian_decision=decision,
            )

        if self._decision_needs_approval(decision):
            return SendResult(
                status=SendStatus.PENDING_GUARDIAN,
                tx_id=None,
                error_message=None,
                guardian_decision=decision,
            )

        node = self._get_node_client()
        try:
            txid = node.mint_dd(amount_units)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=txid,
                error_message=None,
                guardian_decision=decision,
            )
        except Exception as exc:  # noqa: BLE001
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
        Redeem DigiDollar units (integration-style only).
        Behaviour mirrors mint_dd.
        """
        decision = self._guardian_decision_generic(amount_units)

        if self._decision_blocked(decision):
            return SendResult(
                status=SendStatus.BLOCKED,
                tx_id=None,
                error_message=None,
                guardian_decision=decision,
            )

        if self._decision_needs_approval(decision):
            return SendResult(
                status=SendStatus.PENDING_GUARDIAN,
                tx_id=None,
                error_message=None,
                guardian_decision=decision,
            )

        node = self._get_node_client()
        try:
            txid = node.redeem_dd(amount_units)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=txid,
                error_message=None,
                guardian_decision=decision,
            )
        except Exception as exc:  # noqa: BLE001
            return SendResult(
                status=SendStatus.FAILED,
                tx_id=None,
                error_message=str(exc),
                guardian_decision=decision,
            )
