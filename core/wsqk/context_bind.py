"""
WSQK Context Binding — Wallet-Scoped Quantum Key

Binds WSQK scopes to EQC-approved context hashes.
This is the bridge between:
- EQC decision outputs (context_hash)
- WSQK execution scopes (context-bound authority)

No key generation happens here.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.eqc import EQCDecision, VerdictType
from .scopes import WSQKScope


class WSQKBindError(Exception):
    """
    Raised when scope binding cannot be created safely.
    """
    pass


@dataclass(frozen=True)
class BoundScope:
    """
    A WSQKScope that has been created from an EQC-approved decision.
    """
    scope: WSQKScope
    eqc_context_hash: str


def bind_scope_from_eqc(
    *,
    decision: EQCDecision,
    wallet_id: str,
    action: str,
    ttl_seconds: int = 60,
) -> BoundScope:
    """
    Create a WSQK scope only when EQC returned ALLOW.

    This function is intentionally strict:
    - if EQC is not ALLOW => no scope
    """
    if decision.verdict.type != VerdictType.ALLOW:
        raise WSQKBindError(f"Cannot bind WSQK scope without EQC ALLOW (got {decision.verdict.type}).")

    scope = WSQKScope.from_ttl(
        wallet_id=wallet_id,
        action=action,
        context_hash=decision.context_hash,
        ttl_seconds=ttl_seconds,
    )

    return BoundScope(scope=scope, eqc_context_hash=decision.context_hash)
