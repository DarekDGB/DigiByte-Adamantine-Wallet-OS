import pytest

from core.eqc.engine import EQCEngine
from core.eqc.context import (
    EQCContext,
    ActionContext,
    DeviceContext,
    NetworkContext,
    UserContext,
)
from core.eqc.verdicts import VerdictType

from core.wsqk.context_bind import bind_scope_from_eqc, WSQKBindError


def _ctx(device_type: str = "mobile", trusted: bool = True) -> EQCContext:
    return EQCContext(
        action=ActionContext(action="send", asset="DGB", amount=1000, recipient="DGB1-test"),
        device=DeviceContext(
            device_id="device-1",
            device_type=device_type,
            os="ios",
            trusted=trusted,
            first_seen_ts=1700000000,
        ),
        network=NetworkContext(network="testnet", fee_rate=10, peer_count=8),
        user=UserContext(user_id="user-1", biometric_available=True, pin_set=True),
        extra={},
    )


def test_bind_scope_requires_eqc_allow():
    engine = EQCEngine()
    decision = engine.decide(_ctx(device_type="browser"))  # DENY invariant
    assert decision.verdict.type == VerdictType.DENY

    with pytest.raises(WSQKBindError):
        bind_scope_from_eqc(
            decision=decision,
            wallet_id="wallet-1",
            action="send",
            ttl_seconds=60,
        )


def test_bind_scope_uses_eqc_context_hash():
    engine = EQCEngine()
    decision = engine.decide(_ctx(device_type="mobile", trusted=True))
    assert decision.verdict.type == VerdictType.ALLOW

    bound = bind_scope_from_eqc(
        decision=decision,
        wallet_id="wallet-1",
        action="send",
        ttl_seconds=60,
    )

    assert bound.eqc_context_hash == decision.context_hash
    assert bound.scope.context_hash == decision.context_hash
    assert bound.scope.wallet_id == "wallet-1"
    assert bound.scope.action.lower() == "send"
