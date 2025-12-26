"""
WSQK — Wallet-Scoped Quantum Key

WSQK (Wallet-Scoped Quantum Key) defines the key scoping and execution model
for Adamantine Wallet OS.

Core invariant:
- EQC decides
- WSQK executes (only after VerdictType.ALLOW)

WSQK contains no policy/risk decisions. It only executes within an approved scope.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from .scopes import (
    WSQKScope,
    ScopeType,
)

__all__ = [
    "WSQKScope",
    "ScopeType",
]
