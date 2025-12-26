"""
EQC — Execution / Eligibility / Equivalence Quality Control

EQC is the decision brain of Adamantine Wallet OS.
It evaluates context, policy, and risk to produce a deterministic Verdict.

Design invariant:
- EQC decides
- WSQK executes (only after VerdictType.ALLOW)

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
