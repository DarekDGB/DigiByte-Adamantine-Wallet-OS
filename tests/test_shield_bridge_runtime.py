"""
Tiny runtime sanity test for the Shield Bridge skeleton.

- Imports the runtime modules from core/shield-bridge/
- Builds a RiskPacket using packet_builder
- Evaluates it with ShieldRouter
- Asserts that we get a RiskMap with the default layers

This is intentionally lightweight and deterministic.
"""

from __future__ import annotations

from pathlib import Path
import sys

# --- Import wiring (mirrors test_risk_engine.py style) --------------------

# Repository root: .../DigiByte-Adamantine-Wallet
ROOT = Path(__file__).resolve().parents[1]

# Folder that contains the Shield Bridge runtime modules
SHIELD_BRIDGE_DIR = ROOT / "core" / "shield-bridge"

# Make sure Python can import models.py / shield_router.py etc as top-level modules
if str(SHIELD_BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(SHIELD_BRIDGE_DIR))

from packet_builder import build_risk_packet  # type: ignore[import]
from shield_router import ShieldRouter  # type: ignore[import]


# --- Tests ----------------------------------------------------------------


def test_shield_router_returns_riskmap_with_default_layers() -> None:
    """ShieldRouter should return a RiskMap with all default layers present."""

    # Build a minimal risk packet
    packet = build_risk_packet(
        wallet_id="wallet-test",
        account_id="account-test",
        flow_type="TRANSFER",
        amount_sats=1000,
    )

    router = ShieldRouter()
    risk_map = router.evaluate(packet)

    # Basic shape checks
    assert risk_map.packet_id == packet.packet_id
    assert len(risk_map.results) > 0

    layers = {r.layer for r in risk_map.results}

    # Default adapters from build_default_adapters()
    expected_layers = {"sentinel", "dqsn", "adn", "qwg", "adaptive"}
    assert expected_layers.issubset(layers)

    # With Noop adapters, all default layers should report:
    # - risk_score = 0.0
    # - status = "unreachable"
    for result in risk_map.results:
        if result.layer in expected_layers:
            assert result.risk_score == 0.0
            assert result.status == "unreachable"
