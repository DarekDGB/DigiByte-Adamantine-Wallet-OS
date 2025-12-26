import pytest

from core.eqc.context import (
    EQCContext,
    ActionContext,
    DeviceContext,
    NetworkContext,
    UserContext,
)
from core.runtime.orchestrator import RuntimeOrchestrator, ExecutionBlocked


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


def test_orchestrator_wsqk_executes_after_eqc_allow():
    orch = RuntimeOrchestrator()
    called = {"n": 0}

    def executor(_context: EQCContext):
        called["n"] += 1
        return {"ok": True}

    out = orch.execute(
        context=_ctx(device_type="mobile", trusted=True),
        executor=executor,
        use_wsqk=True,
        wallet_id="wallet-1",
        action="send",
        ttl_seconds=60,
    )

    assert called["n"] == 1
    assert isinstance(out.context_hash, str)
    assert len(out.context_hash) > 0
    assert out.result == {"ok": True}


def test_orchestrator_wsqk_blocks_when_eqc_denies():
    orch = RuntimeOrchestrator()

    def executor(_context: EQCContext):
        return "should-not-run"

    with pytest.raises(ExecutionBlocked):
        orch.execute(
            context=_ctx(device_type="browser", trusted=True),  # EQC DENY invariant
            executor=executor,
            use_wsqk=True,
            wallet_id="wallet-1",
            action="send",
            ttl_seconds=60,
        )


def test_orchestrator_wsqk_requires_wallet_id_and_action():
    orch = RuntimeOrchestrator()

    def executor(_context: EQCContext):
        return {"ok": True}

    with pytest.raises(ValueError):
        orch.execute(
            context=_ctx(device_type="mobile", trusted=True),
            executor=executor,
            use_wsqk=True,
            wallet_id=None,
            action="send",
        )

    with pytest.raises(ValueError):
        orch.execute(
            context=_ctx(device_type="mobile", trusted=True),
            executor=executor,
            use_wsqk=True,
            wallet_id="wallet-1",
            action=None,
        )
