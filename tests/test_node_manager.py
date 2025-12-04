import pytest
from core.node_manager import NodeConfig, NodeManager


def test_prefers_higher_priority_node(monkeypatch):
    # --- Arrange ---
    nodes = [
        NodeConfig(name="low_priority_node", host="a", port=1),
        NodeConfig(name="high_priority_node", host="b", port=2),
    ]

    priorities = {
        "low_priority_node": 10,
        "high_priority_node": 100,
    }

    manager = NodeManager(nodes=nodes, priorities=priorities)

    # Patch _is_healthy to always return True
    monkeypatch.setattr(NodeManager, "_is_healthy", lambda self, cfg: True)

    # --- Act ---
    selected = manager.get_best_node()

    # --- Assert ---
    assert selected.name == "high_priority_node"


def test_fallback_when_unhealthy(monkeypatch):
    # --- Arrange ---
    nodes = [
        NodeConfig(name="preferred_node", host="a", port=1),
        NodeConfig(name="backup_node", host="b", port=2),
    ]

    priorities = {
        "preferred_node": 100,
        "backup_node": 50,
    }

    manager = NodeManager(nodes=nodes, priorities=priorities)

    # preferred node unhealthy, backup healthy
    def fake_is_healthy(self, cfg):
        return cfg.name == "backup_node"

    monkeypatch.setattr(NodeManager, "_is_healthy", fake_is_healthy)

    # --- Act ---
    selected = manager.get_best_node()

    # --- Assert ---
    assert selected.name == "backup_node"
