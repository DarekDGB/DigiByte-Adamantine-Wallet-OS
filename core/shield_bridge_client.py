"""
ShieldBridgeClient — high-level adapter between Adamantine Wallet core
and the DigiByte Quantum Shield stack.

This module is a **pure-Python skeleton** for now.  It defines clear,
typed interfaces so that later we can wire in real network calls to:

- Sentinel AI v2      (telemetry + anomaly signals)
- DQSN v2            (distributed confirmation / gossip)
- ADN v2             (node-side defence)
- QAC                (quantum-aware classifier)
- Adaptive Core      (long-term immune memory)

The rest of the wallet can import these models today without knowing
whether the shield stack is running locally, remotely, or is disabled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ShieldSignal:
    """
    A single signal coming from any shield layer.

    Examples:
        - source = "sentinel"
          kind   = "mempool_anomaly"
          risk_score = 0.72
        - source = "qac"
          kind   = "quantum_like_pattern"
          risk_score = 0.93
    """

    source: str
    kind: str
    risk_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ShieldDecision:
    """
    Aggregated decision coming from the shield stack.

    This is intentionally similar in spirit to GuardianDecision but
    focused on *network / protocol* risk instead of human approvals.
    """

    blocked: bool
    needs_approval: bool
    risk_score: float
    reason: str = ""
    signals: List[ShieldSignal] = field(default_factory=list)

    @classmethod
    def allow(cls, *, reason: str = "", risk_score: float = 0.0) -> "ShieldDecision":
        return cls(
            blocked=False,
            needs_approval=False,
            risk_score=risk_score,
            reason=reason,
            signals=[],
        )

    @classmethod
    def require_approval(
        cls, *, reason: str = "", risk_score: float = 0.0
    ) -> "ShieldDecision":
        return cls(
            blocked=False,
            needs_approval=True,
            risk_score=risk_score,
            reason=reason,
            signals=[],
        )

    @classmethod
    def block(cls, *, reason: str = "", risk_score: float = 1.0) -> "ShieldDecision":
        return cls(
            blocked=True,
            needs_approval=False,
            risk_score=risk_score,
            reason=reason,
            signals=[],
        )


# ---------------------------------------------------------------------------
# Client skeleton
# ---------------------------------------------------------------------------


@dataclass
class ShieldBridgeConfig:
    """
    Lightweight configuration for the bridge.

    In future we can extend this with URLs, auth tokens or Unix-socket
    paths for each layer (sentinel / dqsn / qac / adaptive_core).
    """

    enabled: bool = False
    sentinel_endpoint: Optional[str] = None
    dqsn_endpoint: Optional[str] = None
    qac_endpoint: Optional[str] = None
    adaptive_core_endpoint: Optional[str] = None


class ShieldBridgeClient:
    """
    High-level facade used by the wallet / node manager.

    IMPORTANT:
        - Current implementation is **offline / mock only**.
        - All methods return an "allow" decision so they are SAFE to
          integrate without changing behaviour.
        - Real networking / IPC wiring can be added later behind the
          same interface.
    """

    def __init__(self, config: Optional[ShieldBridgeConfig] = None) -> None:
        self.config = config or ShieldBridgeConfig()

    # ------------------------------------------------------------------ #
    # Public evaluation methods                                          #
    # ------------------------------------------------------------------ #

    def evaluate_send_dgb(
        self,
        *,
        wallet_id: str,
        account_id: str,
        to_address: str,
        amount_minor: int,
        meta: Optional[Dict[str, Any]] = None,
    ) -> ShieldDecision:
        """
        Evaluate a regular DGB send against the shield stack.

        For now this is a **no-op allow** with a zero risk score so
        that wiring this into WalletService later will not change
        existing unit / integration tests.
        """
        _ = (wallet_id, account_id, to_address, amount_minor, meta)
        return ShieldDecision.allow(reason="shield_bridge_mock_allow")

    def evaluate_mint_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
        meta: Optional[Dict[str, Any]] = None,
    ) -> ShieldDecision:
        """
        Evaluate a DigiDollar mint operation.

        Currently returns an "allow" decision placeholder.
        """
        _ = (wallet_id, account_id, amount_units, meta)
        return ShieldDecision.allow(reason="shield_bridge_mock_allow_dd_mint")

    def evaluate_redeem_dd(
        self,
        *,
        wallet_id: str,
        account_id: str,
        amount_units: int,
        meta: Optional[Dict[str, Any]] = None,
    ) -> ShieldDecision:
        """
        Evaluate a DigiDollar redeem operation.

        Currently returns an "allow" decision placeholder.
        """
        _ = (wallet_id, account_id, amount_units, meta)
        return ShieldDecision.allow(reason="shield_bridge_mock_allow_dd_redeem")

    # ------------------------------------------------------------------ #
    # Introspection helpers (nice for debugging / future logging)        #
    # ------------------------------------------------------------------ #

    def is_enabled(self) -> bool:
        """Return True if the shield bridge is configured as enabled."""
        return bool(self.config.enabled)

    def describe(self) -> Dict[str, Any]:
        """
        Return a serialisable snapshot of the current bridge config.

        This is handy for diagnostics and for exposing a `/status`
        endpoint later if the wallet embeds an HTTP API.
        """
        return {
            "enabled": self.config.enabled,
            "sentinel_endpoint": self.config.sentinel_endpoint,
            "dqsn_endpoint": self.config.dqsn_endpoint,
            "qac_endpoint": self.config.qac_endpoint,
            "adaptive_core_endpoint": self.config.adaptive_core_endpoint,
        }
