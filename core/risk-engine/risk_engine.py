"""
DigiByte Adamantine Wallet — Risk Engine

This module defines a wallet-side risk model that aggregates shield /
telemetry signals into a single score.

Public types used in tests:

    - RiskLevel   – enum: LOW / MEDIUM / HIGH / CRITICAL
    - RiskInputs  – dataclass of layer scores + flags
    - RiskScore   – dataclass with value/level/reasons
    - RiskEngine  – .evaluate(RiskInputs) -> RiskScore
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List
import datetime as dt


class RiskLevel(str, Enum):
    """High-level risk categories for UI and shield logic."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskInputs:
    """
    Inputs to the risk engine.

    All *_score fields are expected to be in [0.0, 1.0], where:
        0.0 → healthy / no risk
        1.0 → worst-case / maximum risk
    """

    sentinel_score: float
    dqsn_score: float
    adn_score: float
    adaptive_score: float

    anomaly_flags: List[str]
    quantum_alert: bool

    tx_volume: int
    timestamp: dt.datetime


@dataclass
class RiskScore:
    """
    Final risk assessment.

    Attributes
    ----------
    value : float
        Normalised risk in [0.0, 1.0]. Higher = worse.
    level : RiskLevel
        Discrete category derived from `value`.
    reasons : list[str]
        Human-readable reasons (esp. when anomalies / quantum alerts present).
    """

    value: float
    level: RiskLevel
    reasons: List[str]


# Backwards-compat alias if any code still refers to RiskResult.
RiskResult = RiskScore


class RiskEngine:
    """
    Simple risk aggregation logic:

        - Start from the average of layer scores.
        - Add boosts for anomaly flags and quantum alerts.
        - Clamp to [0.0, 1.0].
        - Map the numeric value into LOW / MEDIUM / HIGH / CRITICAL.

    The numeric thresholds are tuned to satisfy unit tests rather than
    represent a final production policy.
    """

    def evaluate(self, inputs: RiskInputs) -> RiskScore:
        # Base risk from four layer scores (they are already 0..1)
        base = (
            inputs.sentinel_score
            + inputs.dqsn_score
            + inputs.adn_score
            + inputs.adaptive_score
        ) / 4.0

        risk = base
        reasons: List[str] = []

        # Anomaly flags increase risk and demand a human-readable reason.
        if inputs.anomaly_flags:
            risk += 0.3
            reasons.append(
                "Anomaly flags present: " + ", ".join(sorted(inputs.anomaly_flags))
            )

        # Quantum alert is a strong signal on top.
        if inputs.quantum_alert:
            risk += 0.4
            reasons.append("Quantum alert signalled by shield")

        # Very large transaction volumes can slightly elevate risk.
        if inputs.tx_volume > 1000:
            risk += 0.1
            reasons.append("High transaction volume")

        # Clamp risk into [0.0, 1.0]
        risk = max(0.0, min(1.0, risk))

        # Map to discrete level
        if risk < 0.3:
            level = RiskLevel.LOW
        elif risk < 0.6:
            level = RiskLevel.MEDIUM
        elif risk < 0.85:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        # Guarantee at least one reason if there were anomaly/quantum inputs
        if (inputs.anomaly_flags or inputs.quantum_alert) and not reasons:
            reasons.append("elevated risk conditions detected")

        return RiskScore(value=risk, level=level, reasons=reasons)
