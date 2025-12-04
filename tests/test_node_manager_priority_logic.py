import pytest
from core.node_manager import NodeConfig, NodeManager


def test_priority_sorting_prefers_highest():
    """Manager should always choose the highest-priority healthy node."""
    nodes = [
        NodeConfig(name="low", host="x", port=1),
        NodeConfig(name="mid", host="y", port=2),
        NodeConfig(name="high", host="z", port=3),
    ]

    priorities = {
        "low": 10,
        "mid": 50,
        "high": 100,
    }

    manager = NodeManager(nodes=nodes, priorities=priorities)

    # All healthy by default → choose "high"
    best = manager.get_best_node()
    assert best.name == "high"


def test_fallback_when_high_priority_unhealthy(monkeypatch):
    """If the highest priority node is unhealthy, pick the next healthy one."""
    nodes = [
        NodeConfig(name="primary", host="a", port=1),
        NodeConfig(name="secondary", host="b", port=2),
        NodeConfig(name="backup", host="c", port=3),
    ]

    priorities = {
        "primary": 100,
        "secondary": 80,
        "backup": 50,
    }

    mgr = NodeManager(nodes=nodes, priorities=priorities)

    # Health map — primary offline, secondary healthy, backup healthy
    health = {
        "primary": False,
        "secondary": True,
        "backup": True,
    }

    monkeypatch.setattr(
        NodeManager,
        "_is_healthy",
        lambda self, cfg: health[cfg.name]
    )

    best = mgr.get_best_node()
    assert best.name == "secondary"


def test_only_one_healthy_node(monkeypatch):
    """When only a single node is healthy, always return that one."""
    nodes = [
        NodeConfig(name="n1", host="1", port=1),
        NodeConfig(name="n2", host="2", port=2),
        NodeConfig(name="n3", host="3", port=3),
    ]

    mgr = NodeManager(nodes=nodes, priorities={"n1": 10, "n2": 20, "n3": 30})

    health = {
        "n1": False,
        "n2": True,
        "n3": False,
    }

    monkeypatch.setattr(
        NodeManager,
        "_is_healthy",
        lambda self, cfg: health[cfg.name]
    )

    best = mgr.get_best_node()
    assert best.name == "n2"
