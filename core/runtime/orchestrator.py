"""
Runtime Orchestrator — Adamantine Wallet OS

This module enforces the core security invariant:

    EQC decides.
    WSQK executes.

No execution path may reach WSQK unless EQC (Equilibrium Confirmation)
returns VerdictType.ALLOW.

This file is intentionally minimal and explicit.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.eqc import (
    EQCEngine,
    EQCContext,
    VerdictType,
)


class ExecutionBlocked(Exception):
    """
    Raised when execution is attempted without EQC approval.
    """
    pass


@dataclass
class OrchestratorResult:
    """
    Result returned after a successful EQC-gated execution.
    """
    context_hash: str
    result: Any


class RuntimeOrchestrator:
    """
    Enforces EQC → WSQK → execution flow.

    WSQK (or any execution callable) must be injected
    and will only be invoked after EQC approval.
    """

    def __init__(self, eqc_engine: EQCEngine | None = None):
        self._eqc = eqc_engine or EQCEngine()

    def execute(
        self,
        *,
        context: EQCContext,
        executor: Callable[[EQCContext], Any],
    ) -> OrchestratorResult:
        """
        Execute an approved action.

        Parameters:
        - context: EQCContext
        - executor: callable that performs execution (WSQK later)

        Raises:
        - ExecutionBlocked if EQC does not return ALLOW
        """

        decision = self._eqc.decide(context)

        if decision.verdict.type != VerdictType.ALLOW:
            raise ExecutionBlocked(
                f"Execution blocked by EQC: {decision.verdict.type}"
            )

        # WSQK will live behind this callable in the future
        result = executor(context)

        return OrchestratorResult(
            context_hash=decision.context_hash,
            result=result,
        )
