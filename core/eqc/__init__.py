"""
EQC — Equilibrium Confirmation

EQC (Equilibrium Confirmation) is the decision brain of Adamantine Wallet OS.

It evaluates an immutable execution context and returns a deterministic verdict
that gates all sensitive actions.

Core invariant:
- EQC decides
- WSQK executes (only after VerdictType.ALLOW)

EQC never generates keys, never signs, and never executes actions.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from .verdicts import (
    Verdict,
    VerdictType,
    Reason,
    ReasonCode,
    StepUp,
)

from .context import (
    EQCContext,
    ActionContext,
    DeviceContext,
    NetworkContext,
    UserContext,
)

from .engine import (
    EQCEngine,
    EQCDecision,
)

__all__ = [
    # Verdict primitives
    "Verdict",
    "VerdictType",
    "Reason",
    "ReasonCode",
    "StepUp",
    # Context model
    "EQCContext",
    "ActionContext",
    "DeviceContext",
    "NetworkContext",
    "UserContext",
    # Engine API
    "EQCEngine",
    "EQCDecision",
]
