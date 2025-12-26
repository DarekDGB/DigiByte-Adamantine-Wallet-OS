from core.eqc.context import (
    EQCContext,
    ActionContext,
    DeviceContext,
    NetworkContext,
    UserContext,
)
from core.eqc.engine import EQCEngine
from core.eqc.verdicts import VerdictType


def _base_ctx(
    action: str = "send",
    asset: str = "DGB",
    amount: int | None = 1000,
    recipient: str | None = "DGB1-test-recipient",
    device_type: str = "mobile",
    trusted: bool = True,
    biometric: bool = True,
    pin: bool = True,
) -> EQCContext:
    return EQCContext(
        action=ActionContext(action=action, asset=asset, amount=amount, recipient=recipient),
        device=DeviceContext(
            device_id="device-1",
            device_type=device_type,
            os="ios",
            trusted=trusted,
            first_seen_ts=1700000000,
        ),
        network=NetworkContext(network="testnet", fee_rate=10, peer_count=8),
        user=UserContext(user_id="user-1", biometric_available=biometric, pin_set=pin),
        extra={},
    )


def test_default_allows_safe_send_on_trusted_device():
    engine = EQCEngine()
    decision = engine.decide(_base_ctx())
    assert decision.verdict.type == VerdictType.ALLOW


def test_browser_context_is_denied():
    engine = EQCEngine()
    decision = engine.decide(_base_ctx(device_type="browser"))
    assert decision.verdict.type == VerdictType.DENY


def test_extension_context_is_denied():
    engine = EQCEngine()
    decision = engine.decide(_base_ctx(device_type="extension"))
    assert decision.verdict.type == VerdictType.DENY


def test_mint_requires_step_up():
    engine = EQCEngine()
    decision = engine.decide(_base_ctx(action="mint", asset="DigiDollar"))
    assert decision.verdict.type == VerdictType.STEP_UP
    assert decision.verdict.step_up is not None
    assert len(decision.verdict.step_up.requirements) >= 1


def test_redeem_requires_step_up():
    engine = EQCEngine()
    decision = engine.decide(_base_ctx(action="redeem", asset="DigiDollar"))
    assert decision.verdict.type == VerdictType.STEP_UP


def test_context_hash_is_stable_for_same_context():
    ctx = _base_ctx()
    h1 = ctx.context_hash()
    h2 = ctx.context_hash()
    assert h1 == h2
