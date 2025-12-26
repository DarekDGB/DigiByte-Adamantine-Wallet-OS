"""
Classifier Context Aggregator

Runs a set of classifiers against an EQCContext and returns a unified signals map.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List

from .base import Classifier, ClassificationResult
from .tx_classifier import TransactionClassifier
from .device_classifier import DeviceClassifier
from ..context import EQCContext


@dataclass
class ClassificationBundle:
    """
    Unified classifier output.
    """
    results: List[ClassificationResult] = field(default_factory=list)

    def to_signals(self) -> Dict[str, Any]:
        """
        Flatten results into a nested dict: {classifier_name: signals}
        """
        out: Dict[str, Any] = {}
        for r in self.results:
            out[r.name] = dict(r.signals)
        return out


def default_classifiers() -> List[Classifier]:
    """
    Baseline classifier set for EQC v1.
    """
    return [
        TransactionClassifier(),
        DeviceClassifier(),
    ]


def classify_all(ctx: EQCContext, classifiers: List[Classifier] | None = None) -> ClassificationBundle:
    """
    Run all classifiers deterministically in order.
    """
    clfs = classifiers if classifiers is not None else default_classifiers()
    results: List[ClassificationResult] = [c.classify(ctx) for c in clfs]
    return ClassificationBundle(results=results)
