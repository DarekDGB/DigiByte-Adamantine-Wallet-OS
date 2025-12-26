from core.eqc.context import (
    EQCContext,
    ActionContext,
    DeviceContext,
    NetworkContext,
    UserContext,
)
from core.eqc.engine import EQCEngine
from core.eqc.verdicts import VerdictType, ReasonCode


def _ctx(device_type: str) -> EQCContext:
    return EQCContext(
        action=ActionContext(action="send", asset="DGB", amount=1000, recipient="DGB1-test"),
        device=DeviceContext(
            device_id="device-1",
            device_type=device_type,
            os="ios",
            trusted=True,
            first_seen_ts=1700000000,
        ),
        network=NetworkContext(network="testnet", fee_rate=10, peer_count=8),
        user=UserContext(user_id="user-1", biometric_available=True, pin_set=True),
        extra={},
    )


def _has_reason(verdict, code: ReasonCode) -> bool:
    return any(r.code == code for r in verdict.reasons)


def test_invariant_browser_is_denied_with_reason():
    engine = EQCEngine()
    decision = engine.decide(_ctx("browser"))
    assert decision.verdict.type == VerdictType.DENY
    assert _has_reason(decision.verdict, ReasonCode.BROWSER_CONTEXT_BLOCKED)


def test_invariant_extension_is_denied_with_reason():
    engine = EQCEngine()
    decision = engine.decide(_ctx("extension"))
    assert decision.verdict.type == VerdictType.DENY
    assert _has_reason(decision.verdict, ReasonCode.EXTENSION_CONTEXT_BLOCKED)
