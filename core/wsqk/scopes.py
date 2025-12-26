"""
WSQK Scopes — Wallet-Scoped Quantum Key

A WSQKScope defines the allowed boundaries for a WSQK execution key:
- wallet scope
- action scope
- context scope (EQC context_hash)
- time scope (TTL)

WSQK keys must be invalid outside their scope.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import time


class ScopeType(str, Enum):
    """
    High-level scope categories.
    """
    WALLET = "WALLET"
    ACTION = "ACTION"
    CONTEXT = "CONTEXT"
    TIME = "TIME"


@dataclass(frozen=True)
class WSQKScope:
    """
    Defines an execution scope for WSQK.

    - wallet_id: identifies the wallet boundary
    - action: send/mint/redeem/sign/etc
    - context_hash: must match EQC-approved context hash
    - not_before / expires_at: time window constraints (unix seconds)
    """
    wallet_id: str
    action: str
    context_hash: str
    not_before: int
    expires_at: int

    def is_active(self, now: Optional[int] = None) -> bool:
        t = int(now if now is not None else time.time())
        return self.not_before <= t <= self.expires_at

    def assert_active(self, now: Optional[int] = None) -> None:
        if not self.is_active(now=now):
            raise ValueError("WSQK scope is not active (outside permitted time window).")

    def assert_context(self, context_hash: str) -> None:
        if self.context_hash != context_hash:
            raise ValueError("WSQK scope context_hash mismatch.")

    def assert_action(self, action: str) -> None:
        if self.action.lower() != action.lower():
            raise ValueError("WSQK scope action mismatch.")

    def assert_wallet(self, wallet_id: str) -> None:
        if self.wallet_id != wallet_id:
            raise ValueError("WSQK scope wallet_id mismatch.")

    @staticmethod
    def from_ttl(*, wallet_id: str, action: str, context_hash: str, ttl_seconds: int = 60) -> "WSQKScope":
        """
        Create a scope active immediately for a short TTL.
        Default TTL is intentionally small.
        """
        now = int(time.time())
        return WSQKScope(
            wallet_id=wallet_id,
            action=action,
            context_hash=context_hash,
            not_before=now,
            expires_at=now + int(ttl_seconds),
        )
