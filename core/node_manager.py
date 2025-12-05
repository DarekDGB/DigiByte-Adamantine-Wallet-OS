"""
Compatibility wrapper for NodeManager.

Tests and higher-level code import:

    from core.node_manager import NodeConfig, NodeManager

while the actual implementation lives in core.node.node_manager.
"""

from core.node.node_manager import NodeConfig, NodeManager  # type: ignore[F401]
