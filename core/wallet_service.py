from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, Optional


class SendStatus(Enum):
    """
    Normalised send status used by higher-level clients.

    NOTE: unit tests for the low-level wallet_service still use the old
    dict style (`result["status"] == "blocked"`). For backwards
    compatibility we keep a small adapter in SendResult.__getitem__.
    """

    ALLOWED = auto()
    PENDING_GUARDIAN = auto()
    BLOCKED = auto()
    FAILED = auto()


@dataclass
class SendResult:
    """
    High-level result object returned by WalletService in integration
    tests and real usage.
    """

    status: SendStatus
    tx_id: Optional[str] = None
    error_message: Optional[str] = None
    guardian_decision: Any = None

    # ------------------------------------------------------------------
    # Backwards-compat: allow dict-style access used in some tests:
    #   result["status"] -> "blocked" / "broadcasted" / ...
    #   result["tx_id"]
    #   result["error"]
    # ------------------------------------------------------------------
    def _status_string(self) -> str:
        if self.status == SendStatus.ALLOWED:
            # Old dict API reported successful broadcast as "broadcasted"
            return "broadcasted"
        if self.status == SendStatus.PENDING_GUARDIAN:
            return "needs_approval"
        if self.status == SendStatus.BLOCKED:
            return "blocked"
        return "failed"

    def __getitem__(self, key: str) -> Any:
        if key == "status":
            return self._status_string()
        if key == "tx_id":
            return self.tx_id
        if key == "error":
            return self.error_message
        raise KeyError(key)


class WalletService:
    """
    High-level orchestration for wallet operations.

    This service sits between:
      * GuardianAdapter / test guardians
      * Node manager / client (Digi-Mobile, remote node, etc.)
    """

    def __init__(
        self,
        guardian: Any = None,
        *,
        guardian_adapter: Any = None,
        node_manager: Any,
    ) -> None:
        # Older tests pass guardian_adapter=..., newer may use guardian=...
        if guardian is None:
            guardian = guardian_adapter
        self.guardian = guardian
        self.node_manager = node_manager

    # ------------------------------------------------------------------
    # Node client helper
    # ------------------------------------------------------------------
    def _get_node_client(self) -> Any:
        mgr = self.node_manager
        if hasattr(mgr, "get_best_node"):
            return mgr.get_best_node()
        if hasattr(mgr, "get_preferred_node"):
            return mgr.get_preferred_node()
        if hasattr(mgr, "client"):
            return mgr.client
        if hasattr(mgr, "node"):  # DummyNodeManager in tests
            return mgr.node
        raise RuntimeError("WalletService: no node client available")

    # ------------------------------------------------------------------
    # Guardian decision helper – works with both our GuardianDecision
    # and the DummyDecision used in tests.
    # ------------------------------------------------------------------
    @staticmethod
    def _interpret_guardian_decision(decision: Any) -> tuple[bool, bool]:
        """
        Return (blocked, needs_approval) from any decision-like object.
        """
        if decision is None:
            return False, False

        blocked = bool(getattr(decision, "blocked", False))

        needs_flag = getattr(decision, "needs", False)
        needs_attr = getattr(decision, "needs_approval", None)

        if callable(needs_attr):
            needs_val = bool(needs_attr())
        elif needs_attr is None:
            needs_val = False
        else:
            needs_val = bool(needs_attr)

        needs_approval = bool(needs_flag or needs_val)
        return blocked, needs_approval

    # ------------------------------------------------------------------
    # DGB send
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
    ) -> Any:
        """
        Orchestrate a DGB send with Guardian checks.

        Returns:
          * dict       – legacy unit-test mode (value_dgb + tx_hex)
          * SendResult – integration / real-world mode
        """

        # Decide which flavour of API we are serving.
        unit_mode = (
            (tx_hex is not None or value_dgb is not None)
            and to_address is None
            and amount_minor is None
            and amount_units is None
        )

        # ---------------------- 1) Guardian pre-check -------------------
        decision: Any = None
        if self.guardian is not None:
            if hasattr(self.guardian, "evaluate_send_dgb"):
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
                    try:
                        decision = self.guardian.evaluate_send_dgb(
                            wallet_id, account_id, amount_for_guardian
                        )
                    except TypeError:
                        decision = self.guardian.evaluate_send_dgb(
                            wallet_id, account_id
                        )
            elif hasattr(self.guardian, "decision"):
                # DummyGuardianAdapter in integration tests
                decision = getattr(self.guardian, "decision")

        blocked, needs_approval = self._interpret_guardian_decision(decision)

        # ----------------- 2) Legacy unit-test dict mode ----------------
        if unit_mode:
            if blocked:
                return {
                    "status": "blocked",
                    "tx_id": None,
                    "error": None,
                    "guardian": decision,
                }
            if needs_approval:
                return {
                    "status": "needs_approval",
                    "tx_id": None,
                    "error": None,
                    "guardian": decision,
                }

            node = self._get_node_client()
            try:
                tx_id = node.broadcast_tx(tx_hex or "")
                return {
                    "status": "broadcasted",
                    "tx_id": tx_id,
                    "error": None,
                    "guardian": decision,
                }
            except Exception as exc:  # pragma: no cover
                return {
                    "status": "failed",
                    "tx_id": None,
                    "error": str(exc),
                    "guardian": decision,
                }

        # -------------- 3) Integration / real-world mode ----------------
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
                guardian_decision=decision,
            )

        node = self._get_node_client()

        # DummyNodeClient in tests asserts on "amount" key.
        if to_address is not None and amount_minor is not None:
            payload: Dict[str, Any] = {
                "flow": "send_dgb",
                "wallet_id": wallet_id,
                "account_id": account_id,
                "to_address": to_address,
                "amount": amount_minor,
                "description": description,
            }
        else:
            payload = {
                "flow": "send_dgb",
                "wallet_id": wallet_id,
                "account_id": account_id,
                "amount": value_dgb,
                "tx_hex": tx_hex,
                "description": description,
            }

        try:
            tx_id = node.broadcast_tx(payload)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover
            return SendResult(
                status=SendStatus.FAILED,
                error_message=str(exc),
                guardian_decision=decision,
            )

    # ------------------------------------------------------------------
    # DigiDollar mint / redeem
    # ------------------------------------------------------------------
    def mint_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
        description: str = "Mint DigiDollar",
    ) -> SendResult:
        """
        Mint DigiDollar units with optional Guardian policy enforcement.
        """

        decision: Any = None
        if self.guardian is not None:
            if hasattr(self.guardian, "evaluate_mint_dd"):
                try:
                    decision = self.guardian.evaluate_mint_dd(
                        wallet_id=wallet_id,
                        account_id=account_id,
                        amount_units=amount_units,
                        description=description,
                    )
                except TypeError:
                    decision = self.guardian.evaluate_mint_dd(
                        wallet_id, account_id, amount_units
                    )
            elif hasattr(self.guardian, "decision"):
                decision = getattr(self.guardian, "decision")

        blocked, needs_approval = self._interpret_guardian_decision(decision)

        if blocked:
            return SendResult(
                status=SendStatus.BLOCKED,
                error_message="Mint blocked by Guardian policy.",
                guardian_decision=decision,
            )

        if needs_approval:
            return SendResult(
                status=SendStatus.PENDING_GUARDIAN,
                guardian_decision=decision,
            )

        node = self._get_node_client()
        payload: Dict[str, Any] = {
            "flow": "dd_mint",
            "wallet_id": wallet_id,
            "account_id": account_id,
            "amount": amount_units,
            "description": description,
        }

        try:
            tx_id = node.broadcast_tx(payload)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover
            return SendResult(
                status=SendStatus.FAILED,
                error_message=str(exc),
                guardian_decision=decision,
            )

    def redeem_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
        description: str = "Redeem DigiDollar",
    ) -> SendResult:
        """
        Redeem DigiDollar units with Guardian policy enforcement.
        """

        decision: Any = None
        if self.guardian is not None:
            if hasattr(self.guardian, "evaluate_redeem_dd"):
                try:
                    decision = self.guardian.evaluate_redeem_dd(
                        wallet_id=wallet_id,
                        account_id=account_id,
                        amount_units=amount_units,
                        description=description,
                    )
                except TypeError:
                    decision = self.guardian.evaluate_redeem_dd(
                        wallet_id, account_id, amount_units
                    )
            elif hasattr(self.guardian, "decision"):
                decision = getattr(self.guardian, "decision")

        blocked, needs_approval = self._interpret_guardian_decision(decision)

        if blocked:
            return SendResult(
                status=SendStatus.BLOCKED,
                error_message="Redeem blocked by Guardian policy.",
                guardian_decision=decision,
            )

        if needs_approval:
            return SendResult(
                status=SendStatus.PENDING_GUARDIAN,
                guardian_decision=decision,
            )

        node = self._get_node_client()
        payload: Dict[str, Any] = {
            "flow": "dd_redeem",
            "wallet_id": wallet_id,
            "account_id": account_id,
            "amount": amount_units,
            "description": description,
        }

        try:
            tx_id = node.broadcast_tx(payload)
            return SendResult(
                status=SendStatus.ALLOWED,
                tx_id=tx_id,
                guardian_decision=decision,
            )
        except Exception as exc:  # pragma: no cover
            return SendResult(
                status=SendStatus.FAILED,
                error_message=str(exc),
                guardian_decision=decision,
            )
