from core.eqc.context import (
    EQCContext,
    ActionContext,
    DeviceContext,
    NetworkContext,
    UserContext,
)
from core.eqc.policy import default_policy
from core.eqc.verdicts import VerdictType


def _ctx(
    *,
    action: str = "send",
    asset: str = "DGB",
    amount: int | None = 1000,
    recipient: str | None = "DGB1-test-recipient",
    device_type: str = "mobile",
    trusted: bool = True,
    first_seen_ts: int | None = 1700000000,
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
            first_seen_ts=first_seen_ts,
        ),
        network=NetworkContext(network="testnet", fee_rate=10, peer_count=8),
        user=UserContext(user_id="user-1", biometric_available=biometric, pin_set=pin),
        extra={},
    )


def test_default_policy_allows_safe_send():
    policy = default_policy()
    v = policy.evaluate(_ctx())
    assert v.type == VerdictType.ALLOW


def test_untrusted_device_steps_up():
    policy = default_policy()
    v = policy.evaluate(_ctx(trusted=False, first_seen_ts=1700000000))
    assert v.type == VerdictType.STEP_UP
    assert v.step_up is not None


def test_new_device_steps_up():
    policy = default_policy()
    v = policy.evaluate(_ctx(trusted=False, first_seen_ts=None))
    assert v.type == VerdictType.STEP_UP
    assert v.step_up is not None


def test_large_amount_steps_up():
    policy = default_policy()
    v = policy.evaluate(_ctx(amount=10_000_000))
    assert v.type == VerdictType.STEP_UP
    assert v.step_up is not None


def test_step_up_prefers_biometric_then_pin():
    policy = default_policy()

    v1 = policy.evaluate(_ctx(action="mint", asset="DigiDollar", biometric=True, pin=True))
    assert v1.type == VerdictType.STEP_UP
    assert "biometric" in (v1.step_up.requirements or [])
    assert "pin" in (v1.step_up.requirements or [])

    v2 = policy.evaluate(_ctx(action="mint", asset="DigiDollar", biometric=False, pin=True))
    assert v2.type == VerdictType.STEP_UP
    assert "pin" in (v2.step_up.requirements or [])
    assert "biometric" not in (v2.step_up.requirements or [])

    v3 = policy.evaluate(_ctx(action="mint", asset="DigiDollar", biometric=False, pin=False))
    assert v3.type == VerdictType.STEP_UP
    assert "local_confirmation" in (v3.step_up.requirements or [])
