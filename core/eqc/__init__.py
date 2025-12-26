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

__all__ = [
    "Verdict",
    "VerdictType",
    "Reason",
    "ReasonCode",
    "StepUp",
]
