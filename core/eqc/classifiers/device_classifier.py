"""
Device Classifier

Extracts device/environment signals from EQCContext.
No decisions. No side effects.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from __future__ import annotations

from typing import Any, Dict

from .base import Classifier, ClassificationResult
from ..context import EQCContext


class DeviceClassifier(Classifier):
    """
    Classifies device/environment-level risk signals.
    """

    name = "device"

    def classify(self, ctx: EQCContext) -> ClassificationResult:
        d = ctx.device
        signals: Dict[str, Any] = {}

        # Identity / trust
        signals["device_id"] = d.device_id
        signals["device_type"] = d.device_type
        signals["os"] = d.os
        signals["trusted"] = bool(d.trusted)
        signals["first_seen_ts"] = d.first_seen_ts
        signals["is_new_device"] = (not d.trusted) and (d.first_seen_ts is None)

        # Environment flags (policy uses these to hard-block)
        dt = (d.device_type or "").lower()
        signals["is_browser"] = dt == "browser"
        signals["is_extension"] = dt in {"extension", "browser_extension"}

        return ClassificationResult(name=self.name, signals=signals)
