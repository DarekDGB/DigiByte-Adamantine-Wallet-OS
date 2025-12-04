"""
NodeManager — Select and manage DigiByte node backends.

This component:

- keeps a list of candidate nodes (local Digi-Mobile + remote nodes),
- probes them for basic health (block height),
- prefers the highest-priority healthy node,
- exposes a NodeClient for the rest of the wallet.

It does not parse YAML directly; higher layers can construct NodeConfig
objects from config/example-nodes.yml and pass them in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .node_client import NodeClient, NodeClientError, NodeConfig


@dataclass
class NodeStatus:
    """Runtime status for a single node."""
    config: NodeConfig
    healthy: bool
    last_error: Optional[str] = None
    last_height: Optional[int] = None


class NodeManager:
    """
    Manages a pool of node backends and selects the best available one.

    Selection rules (initial version):

    1. Only consider nodes that respond successfully to get_block_count().
    2. Among healthy nodes, choose the one with the highest "priority"
       (this field can live in the NodeConfig wrapper or external mapping).
    3. Callers use `get_active_client()` to obtain a NodeClient bound
       to the chosen node.

    Note: This class is intentionally simple and can be extended later
    with richer health checks and metrics.
    """

    def __init__(self, nodes: List[NodeConfig], priorities: Optional[dict[str, int]] = None):
        """
        Args:
            nodes: List of NodeConfig entries to manage.
            priorities: Optional override mapping: node_id -> priority (int).
                        Higher number = more preferred.
        """
        self._nodes = nodes
        self._priorities = priorities or {}
        self._status: List[NodeStatus] = []
        self._active_client: Optional[NodeClient] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def probe_all(self) -> List[NodeStatus]:
        """
        Probe all nodes and update health status.

        Returns:
            List of NodeStatus entries (one per node).
        """
        statuses: List[NodeStatus] = []

        for cfg in self._nodes:
            client = NodeClient(cfg)
            try:
                height = client.get_block_count()
                statuses.append(NodeStatus(config=cfg, healthy=True, last_error=None, last_height=height))
            except NodeClientError as e:
                statuses.append(NodeStatus(config=cfg, healthy=False, last_error=str(e), last_height=None))

        self._status = statuses
        self._active_client = self._select_best_client(statuses)
        return statuses

    def get_active_client(self) -> NodeClient:
        """
        Return the currently selected NodeClient.

        If no probe has been run yet, this method triggers one.
        Raises NodeClientError if no healthy nodes are found.
        """
        if self._active_client is None:
            statuses = self.probe_all()
            if self._active_client is None:
                # No healthy node even after probing
                raise NodeClientError("No healthy DigiByte nodes available")

        return self._active_client

    def get_status(self) -> List[NodeStatus]:
        """Return the last known status list (may be empty if not probed yet)."""
        return list(self._status)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _select_best_client(self, statuses: List[NodeStatus]) -> Optional[NodeClient]:
        """
        Choose the best node among healthy ones using priority rules.

        Priority source:
          - priorities dict (if provided): node_id -> priority
          - otherwise, default priority = 0

        Higher priority wins. If priorities tie, first healthy in the list wins.
        """
        healthy_nodes = [s for s in statuses if s.healthy]
        if not healthy_nodes:
            return None

        def node_priority(status: NodeStatus) -> int:
            return int(self._priorities.get(status.config.id, 0))

        # Sort by priority descending
        healthy_sorted = sorted(healthy_nodes, key=node_priority, reverse=True)
        best = healthy_sorted[0]
        return NodeClient(best.config)
