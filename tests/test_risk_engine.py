"""
Basic unit tests for the Adamantine Wallet Risk Engine.

These tests are intentionally lightweight:
- They import the risk_engine module directly from core/risk-engine/
- They only assert *behavioural* properties (relative risk, valid levels, etc.)
  so future tuning of the scoring formula won't constantly break the suite.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import sys

# --- Import wiring ---------------------------------------------------------

# Repository root: .../DigiByte-Adamantine-Wallet
ROOT = Path(__file__).resolve().parents[1]

# Folder that contains risk_engine.py
RISK_ENGINE_DIR = ROOT / "core" / "risk-engine"

# Make sure Python can import risk_engine.py as a top-level module
if str(RISK_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(RISK_ENGINE_DIR))

from risk_engine import (  # type: ignore[import]
    RiskEngine,
    RiskInputs,
)


# --- Helpers ---------------------------------------------------------------

def _make_inputs(
    *,
    sentinel_score: float,
    dqsn_score: float,
    adn_score: float,
    adaptive_score: float,
    anomaly_flags: list[str] | None = None,
    quantum_alert: bool = False,
) -> RiskInputs:
    """Convenience factory so tests stay readable."""
    return RiskInputs(
        sentinel_score=sentinel_score,
        dqsn_score=dqsn_score,
        adn_score=adn_score,
        adaptive_score=adaptive_score,
        anomaly_flags=anomaly_flags or [],
        quantum_alert=quantum_alert,
        tx_volume=10,
        timestamp=dt.datetime.utcnow(),
    )


# --- Tests -----------------------------------------------------------------


def test_low_risk_when_shield_healthy() -> None:
    """
    When all shield layers look healthy and no anomalies are present,
    the engine should classify the situation as LOW or MEDIUM risk,
    but never HIGH or CRITICAL.
    """
    engine = RiskEngine()

    inputs = _make_inputs(
        sentinel_score=0.05,
        dqsn_score=0.05,
        adn_score=0.05,
        adaptive_score=0.05,
        anomaly_flags=[],
        quantum_alert=False,
    )

    score = engine.evaluate(inputs)

    assert 0.0 <= score.value <= 100.0
    assert score.level in ("low", "medium")
    assert isinstance(score.reasons, list)


def test_high_risk_when_multiple_alerts() -> None:
    """
    When several layers report trouble, anomaly flags are present
    and quantum_alert is set, risk should be HIGH or CRITICAL and
    higher than the healthy baseline.
    """
    engine = RiskEngine()

    healthy = _make_inputs(
        sentinel_score=0.05,
        dqsn_score=0.05,
        adn_score=0.05,
        adaptive_score=0.05,
        anomaly_flags=[],
        quantum_alert=False,
    )

    under_attack = _make_inputs(
        sentinel_score=0.9,
        dqsn_score=0.9,
        adn_score=0.9,
        adaptive_score=0.9,
        anomaly_flags=["reorg_spike", "double_spend_pattern"],
        quantum_alert=True,
    )

    healthy_score = engine.evaluate(healthy)
    attack_score = engine.evaluate(under_attack)

    assert attack_score.value > healthy_score.value
    assert attack_score.level in ("high", "critical")


def test_reasons_populated_when_anomalies_present() -> None:
    """
    If anomaly flags are present, the RiskScore should expose at least
    one human-readable reason so the UI can explain *why* the score is high.
    """
    engine = RiskEngine()

    inputs = _make_inputs(
        sentinel_score=0.7,
        dqsn_score=0.7,
        adn_score=0.7,
        adaptive_score=0.7,
        anomaly_flags=["mempool_anomaly"],
        quantum_alert=False,
    )

    score = engine.evaluate(inputs)

    assert len(score.reasons) > 0
