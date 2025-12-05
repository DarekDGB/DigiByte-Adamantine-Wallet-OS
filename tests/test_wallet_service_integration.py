"""
Integration-style tests for WalletService interacting with:

  - GuardianAdapter
  - WalletState
  - NodeManager / node client

These tests validate control-flow correctness:
  ALLOW, BLOCK, PENDING_GUARDIAN and broadcast calls.
"""

from core.wallet_service import WalletService, SendStatus  # type: ignore[import]
from core.guardian_wallet.adapter import GuardianDecision  # type: ignore[import]


class DummyDecision:
    """Simple stub for GuardianDecision-like behavior."""

    def __init__(self, blocked=False, needs=False):
        self._blocked = blocked
        self._needs = needs

    def is_blocked(self):
        return self._blocked

    def needs_approval(self):
        return self._needs


class DummyGuardianAdapter:
    """GuardianAdapter stub with configurable behavior."""

    def __init__(self, decision: DummyDecision):
        self.decision = decision
        self.calls = []

    def evaluate_send_dgb(self, **kwargs):
        self.calls.append(("send_dgb", kwargs))
        return self.decision

    def evaluate_mint_dd(self, **kwargs):
        self.calls.append(("mint_dd", kwargs))
        return self.decision

    def evaluate_redeem_dd(self, **kwargs):
        self.calls.append(("redeem_dd", kwargs))
        return self.decision


class DummyNodeClient:
    """Fake node client returning deterministic tx ids."""

    def __init__(self):
        self.broadcasts = []

    def broadcast_tx(self, tx):
        self.broadcasts.append(tx)
        return "tx_fake_123"


class DummyNodeManager:
    """Returns the dummy node client."""

    def __init__(self, client: DummyNodeClient):
        self.client = client

    def get_best_node(self):
        return self.client


# ---------------------------------------------------------------------
# DGB SEND TESTS
# ---------------------------------------------------------------------

def test_send_dgb_allowed_broadcasts_and_returns_txid():
    node = DummyNodeClient()
    service = WalletService(
        guardian=DummyGuardianAdapter(DummyDecision(blocked=False, needs=False)),
        node_manager=DummyNodeManager(node),
    )

    result = service.send_dgb(
        wallet_id="w1",
        account_id="a1",
        to_address="dgb1xyz",
        amount_minor=1000,
    )

    assert result.status == SendStatus.ALLOWED
    assert result.tx_id == "tx_fake_123"
    assert len(node.broadcasts) == 1
    assert node.broadcasts[0]["amount"] == 1000


def test_send_dgb_blocked_never_broadcasts():
    node = DummyNodeClient()
    service = WalletService(
        guardian=DummyGuardianAdapter(DummyDecision(blocked=True, needs=False)),
        node_manager=DummyNodeManager(node),
    )

    result = service.send_dgb(
        wallet_id="w1",
        account_id="a1",
        to_address="dgb1xyz",
        amount_minor=500,
    )

    assert result.status == SendStatus.BLOCKED
    assert len(node.broadcasts) == 0


def test_send_dgb_needs_approval_returns_pending():
    node = DummyNodeClient()
    service = WalletService(
        guardian=DummyGuardianAdapter(DummyDecision(blocked=False, needs=True)),
        node_manager=DummyNodeManager(node),
    )

    result = service.send_dgb(
        wallet_id="w1",
        account_id="a1",
        to_address="dgb1xyz",
        amount_minor=250,
    )

    assert result.status == SendStatus.PENDING_GUARDIAN
    assert result.tx_id is None
    assert len(node.broadcasts) == 0


# ---------------------------------------------------------------------
# DIGIDOLLAR TESTS (mint + redeem)
# ---------------------------------------------------------------------

def test_mint_dd_allowed_calls_node():
    node = DummyNodeClient()
    g = DummyGuardianAdapter(DummyDecision(blocked=False, needs=False))
    service = WalletService(guardian=g, node_manager=DummyNodeManager(node))

    result = service.mint_dd(
        wallet_id="w1",
        account_id="a1",
        amount_units=50,
    )

    assert result.status == SendStatus.ALLOWED
    assert result.tx_id == "tx_fake_123"
    assert len(node.broadcasts) == 1
    assert node.broadcasts[0]["amount"] == 50


def test_redeem_dd_blocked():
    node = DummyNodeClient()
    g = DummyGuardianAdapter(DummyDecision(blocked=True, needs=False))
    service = WalletService(guardian=g, node_manager=DummyNodeManager(node))

    result = service.redeem_dd(
        wallet_id="w1",
        account_id="a1",
        amount_units=10,
    )

    assert result.status == SendStatus.BLOCKED
    assert len(node.broadcasts) == 0
