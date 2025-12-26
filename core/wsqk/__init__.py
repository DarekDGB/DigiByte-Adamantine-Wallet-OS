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

from .context_bind import (
    BoundScope,
    bind_scope_from_eqc,
    WSQKBindError,
)

from .executor import (
    WSQKExecutionResult,
    execute_with_scope,
    WSQKExecutionError,
)

__all__ = [
    # Scope model
    "WSQKScope",
    "ScopeType",
    # EQC binding
    "BoundScope",
    "bind_scope_from_eqc",
    "WSQKBindError",
    # Execution stub (no crypto yet)
    "WSQKExecutionResult",
    "execute_with_scope",
    "WSQKExecutionError",
]
