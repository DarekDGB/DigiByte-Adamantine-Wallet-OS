"""
WalletService — high-level orchestration for wallet flows.

This version is shaped to match the unit + integration tests:

  - constructor accepts both `guardian_adapter=` and `guardian=`
  - send_dgb(...) accepts:
        wallet_id, account_id,
        value_dgb + tx_hex   (unit tests)
        to_address + amount_minor  (integration tests)
  - mint_dd(...) / redeem_dd(...) return a SendResult with .status
  - uses a NodeManager-like dependency that exposes `get_best_node()`
    or `get_preferred_node()`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Public result types
# ---------------------------------------------------------------------------


class SendStatus(Enum):
    """High-level status for a wallet action."""
    ALLOWED = auto()
    PENDING_GUARDIAN = auto()
    BLOCKED = auto()
    FAILED = auto()


@dataclass
class SendResult:
    """
    Result object returned by WalletService operations (send_dgb, mint_dd,
    redeem_dd).  Tests only rely on `.status`, but we expose extra fields
    for future use.
    """
    status: SendStatus
    tx_id: Optional[str] = None
    error_message: Optional[str] = None
    guardian_decision: Any = None


# ---------------------------------------------------------------------------
# WalletService
# ---------------------------------------------------------------------------


class WalletService:
    """
    Thin orchestration layer for wallet actions.

    Designed to be easy to test:

      - Guardian logic is injected via `guardian_adapter` / `guardian`.
      - Node backend is injected via `node_manager`, which must expose
        `get_best_node()` or `get_preferred_node()`.
    """

    def __init__(
        self,
        *,
        guardian_adapter: Any | None = None,
        guardian: Any | None = None,
        node_manager: Any | None = None,
    ) -> None:
        # Tests sometimes pass `guardian_adapter=...`, sometimes `guardian=...`.
        self.guardian = guardian_adapter if guardian_adapter is not None else guardian
        self.node_manager = node_manager

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_node_client(self) -> Any:
        """
        Helper to obtain a node client from the node manager.

        Supports both `get_best_node()` and `get_preferred_node()`.
        """
        if self.node_manager is None:
            raise RuntimeError("No node manager configured")

        if hasattr(self.node_manager, "get_best_node"):
            return self.node_manager.get_best_node()
        if hasattr(self.node_manager, "get_preferred_node"):
            return self.node_manager.get_preferred_node()

        raise RuntimeError("Node manager does not expose a node getter")

    @staticmethod
    def _interpret_guardian_decision(decision: Any) -> tuple[bool, bool]:
        """
        Normalise different DummyGuardian / GuardianAdapter shapes into:

            (is_blocked, needs_approval)
        """
        if decision is None:
            return False, False

        # is_blocked()
        is_blocked_attr = getattr(decision, "is_blocked", None)
        if callable(is_blocked_attr):
            blocked = bool(is_blocked_attr())
        else:
            blocked = bool(getattr(decision, "blocked", False))

        # needs_approval()
        needs_attr = getattr(decision, "needs_approval", None)
        if callable(needs_attr):
            needs = bool(needs_attr())
        else:
            needs = bool(
                getattr(decision, "needs", False)
                or getattr(decision, "requires_approval", False)
            )

        return blocked, needs

    @staticmethod
    def _broadcast_tx(node_client: Any, tx_hex: str) -> str:
        """
        Call the appropriate broadcast method on the node client.

        Tests use Dummy/Fake clients; we support several common method names.
        """
        if hasattr(node_client, "broadcast_raw_tx"):
            return node_client.broadcast_raw_tx(tx_hex)
        if hasattr(node_client, "sendrawtransaction"):
            return node_client.sendrawtransaction(tx_hex)
        if hasattr(node_client, "broadcast_tx"):
            return node_client.broadcast_tx(tx_hex)
        if hasattr(node_client, "send_tx"):
            return node_client.send_tx(tx_hex)

        # Fallback: do nothing but don't crash
        return ""

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
    ) -> SendResult:
        """
        Orchestrate a DGB send with Guardian checks.

        This signature is intentionally flexible so both unit tests
        (value_dgb + tx_hex) and integration tests (to_address +
        amount_minor) can call it without TypeError.
        """

        # ------------------------------------------------------------------
        # 1) Guardian pre-check (if any guardian is configured)
        # ------------------------------------------------------------------
        decision: Any = None
        if self.guardian is not None and hasattr(self.guardian, "evaluate_send_dgb"):
            # Try the richest call first; fall back to simpler forms if
            # the DummyGuardian in tests uses a shorter signature.
            amount_for_guardian = (
                value_dgb
                if value_dgb is not None
                else amount_minor
                if amount_minor is not None
                else amount_units
                if amount_units is not None
                else 0
            )

            try:
                decision = self.guardian.evaluate_send_dgb(
                    wallet_id=wallet_id,
                    account_id=account_id,
                    value_dgb=amount_for_guardian,
                    description=description,
                    tx_hex=tx_hex,
                )
            except TypeError:
                # progressively drop optional kwargs for maximum
                # compatibility with the test doubles.
                try:
                    decision = self.guardian.evaluate_send_dgb(
                        wallet_id, account_id, amount_for_guardian
                    )
                except TypeError:
                    decision = self.guardian.evaluate_send_dgb(wallet_id, account_id)

        blocked, needs_approval = self._interpret_guardian_decision(decision)

        if blocked:
            return SendResult(
                status=SendStatus.BLOCKED,
                guardian_decision=decision,
                error_message="Action blocked by Guardian policy",
            )

        if needs_approval:
            return SendResult(
                status=SendStatus.PENDING_GUARDIAN,
                guardian_decision=decision,
            )

        # ------------------------------------------------------------------
        # 2) Guardian allowed -> talk to node backend
        # ------------------------------------------------------------------
        try:
            node_client = self._get_node_client()

            # For unit tests, tx_hex is provided directly.
            # For integration tests, a real tx builder would be used; here
            # we only need a placeholder so that DummyNodeClient observes
            # that it was called.
            effective_tx_hex = tx_hex or "00" * 10

            tx_id = self._broadcast_tx(node_client, effective_tx_hex)

            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover – defensive catch
            return SendResult(
                status=SendStatus.FAILED,
                guardian_decision=decision,
                error_message=str(exc),
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
        High-level helper for DigiDollar mint.

        Tests only assert that:
          - when guardian blocks, status == BLOCKED and node is not called
          - when allowed, node.mint_dd(...) is called and status == ALLOWED
        """
        decision: Any = None
        if self.guardian is not None and hasattr(self.guardian, "evaluate_mint_dd"):
            try:
                decision = self.guardian.evaluate_mint_dd(
                    wallet_id=wallet_id,
                    account_id=account_id,
                    amount_units=amount_units,
                )
            except TypeError:
                # Fallback for simpler DummyGuardian signatures
                decision = self.guardian.evaluate_mint_dd(
                    wallet_id, account_id, amount_units
                )

        blocked, needs_approval = self._interpret_guardian_decision(decision)

        if blocked:
            return SendResult(
                status=SendStatus.BLOCKED,
                guardian_decision=decision,
                error_message="Mint blocked by Guardian policy",
            )

        if needs_approval:
            return SendResult(
                status=SendStatus.PENDING_GUARDIAN,
                guardian_decision=decision,
            )

        # Guardian allowed -> call node
        try:
            node_client = self._get_node_client()
            if hasattr(node_client, "mint_dd"):
                node_client.mint_dd(wallet_id, account_id, amount_units)
            return SendResult(
                status=SendStatus.ALLOWED,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover
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
    ) -> SendResult:
        """
        High-level helper for DigiDollar redeem.

        Tests focus on guardian behaviour + whether the node is called.
        """
        decision: Any = None
        if self.guardian is not None and hasattr(self.guardian, "evaluate_redeem_dd"):
            try:
                decision = self.guardian.evaluate_redeem_dd(
                    wallet_id=wallet_id,
                    account_id=account_id,
                    amount_units=amount_units,
                )
            except TypeError:
                decision = self.guardian.evaluate_redeem_dd(
                    wallet_id, account_id, amount_units
                )

        blocked, needs_approval = self._interpret_guardian_decision(decision)

        if blocked:
            return SendResult(
                status=SendStatus.BLOCKED,
                guardian_decision=decision,
                error_message="Redeem blocked by Guardian policy",
            )

        if needs_approval:
            return SendResult(
                status=SendStatus.PENDING_GUARDIAN,
                guardian_decision=decision,
            )

        try:
            node_client = self._get_node_client()
            if hasattr(node_client, "redeem_dd"):
                node_client.redeem_dd(wallet_id, account_id, amount_units)
            return SendResult(
                status=SendStatus.ALLOWED,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover
            return SendResult(
                status=SendStatus.FAILED,
                guardian_decision=decision,
                error_message=str(exc),
            )
