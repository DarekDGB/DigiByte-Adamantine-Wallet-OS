"""
Tests for WalletService orchestration.

We check that:

- BLOCK verdict from Guardian -> no node call, status="blocked"
- REQUIRE_APPROVAL verdict -> no node call, status="needs_approval"
- ALLOW verdict -> node broadcast is called, status="broadcasted"
- broadcast error -> status="failed"
"""

from core.wallet_service import WalletService
from core.guardian_wallet.adapter import GuardianDecision
from core.guardian_wallet.models import GuardianVerdict, ApprovalRequest


# -------------------------------------------------------------------------
# Fakes / helpers
# -------------------------------------------------------------------------


class _FakeNodeClient:
    def __init__(self, txid: str | None = None, should_fail: bool = False):
        self.txid = txid or "deadbeef" * 4
        self.should_fail = should_fail
        self.broadcast_called = False

    def broadcast_transaction(self, tx_hex: str) -> str:
        self.broadcast_called = True
        if self.should_fail:
            raise RuntimeError("network error")
        return self.txid


class _FakeNodeManager:
    """
    Minimal stand-in for the real NodeManager.

    WalletService only needs `get_best_node_client`, so we expose that.
    """

    def __init__(self, client: _FakeNodeClient):
        self.client = client
        self.get_best_called = False

    def get_best_node_client(self, priorities: dict | None = None) -> _FakeNodeClient:
        self.get_best_called = True
        return self.client


class _BaseGuardianAdapter:
    """
    Base fake GuardianAdapter – subclasses override `_verdict`.
    """

    _verdict: GuardianVerdict

    def __init__(self):
        self.last_ctx = None

    def evaluate_send_dgb(
        self,
        wallet_id: str,
        account_id: str,
        value_dgb: int,
        description: str = "test send",
        meta: dict | None = None,
    ) -> GuardianDecision:
        self.last_ctx = {
            "wallet_id": wallet_id,
            "account_id": account_id,
            "value_dgb": value_dgb,
            "description": description,
            "meta": meta or {},
        }
        # For tests we don't care about a real ApprovalRequest;
        # just pass a placeholder when needed.
        req = ApprovalRequest(
            id="req1",
            rule_id="rule1",
            wallet_id=wallet_id,
            account_id=account_id,
            value=value_dgb,
            description=description,
            required_guardians=[],
        )
        approval = req if self._verdict == GuardianVerdict.REQUIRE_APPROVAL else None
        return GuardianDecision(verdict=self._verdict, approval_request=approval)


class _GuardianBlock(_BaseGuardianAdapter):
    _verdict = GuardianVerdict.BLOCK


class _GuardianNeedsApproval(_BaseGuardianAdapter):
    _verdict = GuardianVerdict.REQUIRE_APPROVAL


class _GuardianAllow(_BaseGuardianAdapter):
    _verdict = GuardianVerdict.ALLOW


# -------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------


def test_block_verdict_does_not_call_node_and_returns_blocked_status():
    guardian = _GuardianBlock()
    fake_client = _FakeNodeClient()
    nodes = _FakeNodeManager(client=fake_client)

    service = WalletService(guardian_adapter=guardian, node_manager=nodes)

    result = service.send_dgb(
        wallet_id="w1",
        account_id="a1",
        value_dgb=1_000,
        description="blocked send",
        tx_hex="00" * 10,
    )

    assert result["status"] == "blocked"
    assert not nodes.get_best_called
    assert not fake_client.broadcast_called


def test_require_approval_verdict_returns_needs_approval_and_no_node_call():
    guardian = _GuardianNeedsApproval()
    fake_client = _FakeNodeClient()
    nodes = _FakeNodeManager(client=fake_client)

    service = WalletService(guardian_adapter=guardian, node_manager=nodes)

    result = service.send_dgb(
        wallet_id="w1",
        account_id="a1",
        value_dgb=50_000,
        description="needs approval",
        tx_hex="11" * 10,
    )

    assert result["status"] == "needs_approval"
    # GuardianDecision with an ApprovalRequest should be present
    assert result["guardian"].needs_approval()
    assert not nodes.get_best_called
    assert not fake_client.broadcast_called


def test_allow_verdict_broadcasts_and_returns_broadcasted_status():
    guardian = _GuardianAllow()
    fake_client = _FakeNodeClient(txid="abc123")
    nodes = _FakeNodeManager(client=fake_client)

    service = WalletService(guardian_adapter=guardian, node_manager=nodes)

    result = service.send_dgb(
        wallet_id="w1",
        account_id="a1",
        value_dgb=10_000,
        description="normal send",
        tx_hex="22" * 10,
    )

    assert result["status"] == "broadcasted"
    assert result["txid"] == "abc123"
    assert nodes.get_best_called
    assert fake_client.broadcast_called


def test_broadcast_failure_returns_failed_status():
    guardian = _GuardianAllow()
    fake_client = _FakeNodeClient(should_fail=True)
    nodes = _FakeNodeManager(client=fake_client)

    service = WalletService(guardian_adapter=guardian, node_manager=nodes)

    result = service.send_dgb(
        wallet_id="w1",
        account_id="a1",
        value_dgb=5_000,
        description="failing send",
        tx_hex="33" * 10,
    )

    assert result["status"] == "failed"
    assert "error" in result
    assert nodes.get_best_called
    assert fake_client.broadcast_called
