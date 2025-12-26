"""
EQC Engine

Single entrypoint that:
1) runs classifiers to extract signals
2) applies policy rules to produce a deterministic Verdict

This module must remain deterministic and side-effect free.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .context import EQCContext
from .policy import EQCPolicy, default_policy
from .verdicts import Verdict
from .classifiers.context import classify_all, ClassificationBundle
from .classifiers.base import Classifier


@dataclass
class EQCDecision:
    """
    Full EQC output: Verdict + classifier signals + context hash.
    """
    verdict: Verdict
    context_hash: str
    signals: Dict[str, Any]


class EQCEngine:
    """
    Default EQC engine (v1).
    """

    def __init__(self, policy: Optional[EQCPolicy] = None, classifiers: Optional[List[Classifier]] = None):
        self._policy = policy or default_policy()
        self._classifiers = classifiers  # if None, classify_all() uses defaults

    def classify(self, ctx: EQCContext) -> ClassificationBundle:
        return classify_all(ctx, classifiers=self._classifiers)

    def evaluate(self, ctx: EQCContext) -> Verdict:
        """
        Returns only the Verdict (minimal API).
        """
        return self._policy.evaluate(ctx)

    def decide(self, ctx: EQCContext) -> EQCDecision:
        """
        Returns Verdict + signals for audit/UI/telemetry.
        """
        bundle = self.classify(ctx)
        signals = bundle.to_signals()
        verdict = self._policy.evaluate(ctx)

        return EQCDecision(
            verdict=verdict,
            context_hash=ctx.context_hash(),
            signals=signals,
        )
