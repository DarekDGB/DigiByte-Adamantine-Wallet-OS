import pytest
from core.node_manager import NodeConfig, NodeManager


DIGIMOBILE_NAME = "digimobile_local"


def _make_manager():
    """Helper: build a manager with one local Digi-Mobile node + 2 remotes."""
    nodes = [
        NodeConfig(name=DIGIMOBILE_NAME, host="127.0.0.1", port=8332),
        NodeConfig(name="dgb_mainnet_1", host="node1.example.com", port=8332),
        NodeConfig(name="dgb_mainnet_2", host="node2.example.com", port=8332),
    ]

    priorities = {
        DIGIMOBILE_NAME: 100,      # Prefer local full node when healthy
        "dgb_mainnet_1": 60,
        "dgb_mainnet_2": 50,
    }

    return NodeManager(nodes=nodes, priorities=priorities)


def test_prefers_digimobile_when_healthy(monkeypatch):
    """If Digi-Mobile is healthy, it should always be selected first."""
    mgr = _make_manager()

    health = {
        DIGIMOBILE_NAME: True,
        "dgb_mainnet_1": True,
        "dgb_mainnet_2": True,
    }

    monkeypatch.setattr(
        NodeManager,
        "_is_healthy",
        lambda self, cfg: health[cfg.name],
    )

    best = mgr.get_best_node()
    assert best.name == DIGIMOBILE_NAME


def test_falls_back_when_digimobile_unhealthy(monkeypatch):
    """
    If Digi-Mobile is down, manager should choose the next-best healthy remote.
    """
    mgr = _make_manager()

    health = {
        DIGIMOBILE_NAME: False,  # local node offline
        "dgb_mainnet_1": True,
        "dgb_mainnet_2": True,
    }

    monkeypatch.setattr(
        NodeManager,
        "_is_healthy",
        lambda self, cfg: health[cfg.name],
    )

    best = mgr.get_best_node()
    assert best.name == "dgb_mainnet_1"
