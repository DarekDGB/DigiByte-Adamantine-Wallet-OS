import pytest
from core.node_manager import NodeConfig, NodeManager


def test_raises_when_no_nodes_configured():
    """NodeManager should fail fast if constructed with an empty node list."""
    manager = NodeManager(nodes=[])

    with pytest.raises(RuntimeError):
        manager.get_best_node()


def test_raises_when_all_nodes_unhealthy(monkeypatch):
    """If every node is unhealthy, get_best_node should raise instead of
    silently choosing one.
    """
    nodes = [
        NodeConfig(name="node_a", host="a", port=1),
        NodeConfig(name="node_b", host="b", port=2),
    ]

    manager = NodeManager(nodes=nodes)

    # Force all health checks to fail
    monkeypatch.setattr(NodeManager, "_is_healthy", lambda self, cfg: False)

    with pytest.raises(RuntimeError):
        manager.get_best_node()
