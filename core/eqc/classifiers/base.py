"""
EQC Classifier Base — Equilibrium Confirmation

Classifiers extract risk/context signals for EQC (Equilibrium Confirmation).
They MUST:
- be deterministic
- have no side effects
- never return Verdicts
- never execute actions or handle key material

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
from abc import ABC, abstractmethod

from ..context import EQCContext


@dataclass(frozen=True)
class ClassificationResult:
    """
    Output of a classifier.

    `signals` are named, testable facts (not opinions).
    Example:
      {
        "new_device": True,
        "velocity": 3,
        "risk_score": 0.72
      }
    """
    name: str
    signals: Dict[str, Any]


class Classifier(ABC):
    """
    Abstract classifier interface.
    """

    name: str

    @abstractmethod
    def classify(self, ctx: EQCContext) -> ClassificationResult:
        """
        Compute signals from context.
        """
        raise NotImplementedError
