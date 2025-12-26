import pytest

from core.eqc.engine import EQCEngine
from core.eqc.context import (
    EQCContext,
    ActionContext,
    DeviceContext,
    NetworkContext,
    UserContext,
)
from core.wsqk.context_bind import bind_scope_from_eqc
from core.wsqk.session import WSQKSession
from core.wsqk.guard import execute_guarded, WSQKGuardError


def _ctx(device_type: str = "mobile") -> EQCContext:
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


def test_guard_executes_once_and_blocks_replay():
    engine = EQCEngine()
    decision = engine.decide(_ctx("mobile"))
    bound = bind_scope_from_eqc(decision=decision, wallet_id="wallet-1", action="send", ttl_seconds=60)

    session = WSQKSession(ttl_seconds=60)
    nonce = session.issue_nonce()

    called = {"n": 0}

    def executor(_context: EQCContext):
        called["n"] += 1
        return {"ok": True}

    out = execute_guarded(
        scope=bound.scope,
        session=session,
        nonce=nonce,
        context=_ctx("mobile"),
        wallet_id="wallet-1",
        action="send",
        executor=executor,
    )

    assert called["n"] == 1
    assert out.result == {"ok": True}

    # Replay same nonce must fail and must not call executor again
    with pytest.raises(WSQKGuardError):
        execute_guarded(
            scope=bound.scope,
            session=session,
            nonce=nonce,
            context=_ctx("mobile"),
            wallet_id="wallet-1",
            action="send",
            executor=executor,
        )

    assert called["n"] == 1


def test_guard_blocks_when_scope_action_mismatch():
    engine = EQCEngine()
    decision = engine.decide(_ctx("mobile"))
    bound = bind_scope_from_eqc(decision=decision, wallet_id="wallet-1", action="send", ttl_seconds=60)

    session = WSQKSession(ttl_seconds=60)
    nonce = session.issue_nonce()

    def executor(_context: EQCContext):
        return {"ok": True}

    with pytest.raises(WSQKGuardError):
        execute_guarded(
            scope=bound.scope,
            session=session,
            nonce=nonce,
            context=_ctx("mobile"),
            wallet_id="wallet-1",
            action="mint",  # mismatch
            executor=executor,
        )
