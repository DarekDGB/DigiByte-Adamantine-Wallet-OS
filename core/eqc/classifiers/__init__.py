"""
EQC Classifiers

Classifiers compute signals from context (and later from telemetry inputs)
without making final decisions. They feed EQC policy evaluation.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from .base import Classifier, ClassificationResult

__all__ = ["Classifier", "ClassificationResult"]
