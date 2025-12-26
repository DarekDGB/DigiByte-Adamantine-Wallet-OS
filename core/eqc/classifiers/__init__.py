"""
EQC Classifiers — Equilibrium Confirmation

Classifiers extract deterministic signals from EQCContext.
They observe only — they never decide and never return Verdicts.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from .base import Classifier, ClassificationResult

__all__ = ["Classifier", "ClassificationResult"]
