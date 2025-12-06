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
from typing import Dict, List, Optional

from .node_client import NodeClient, NodeClientError, NodeConfig


# Name used by tests and configs to identify the local Digi-Mobile node.
# If a node has this name and is healthy, it will receive a strong
# priority boost so it is preferred over ordinary remotes.
DIGIMOBILE_NAME: str = "digi-mobile"


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

    Selection rules:

    1. Only consider nodes that respond successfully to get_block_count().
    2. Among healthy nodes, choose the one with the highest effective priority:
         - NodeConfig.priority if present (default 0),
         - optionally overridden by the `priorities` mapping,
         - with an additional boost for the Digi-Mobile node
           (name == DIGIMOBILE_NAME).
    3. Callers use `get_best_node()` if they want the chosen configuration,
       or `get_active_client()` to obtain a NodeClient bound to that node.
    """

    def __init__(
        self,
        nodes: List[NodeConfig],
        priorities: Optional[Dict[str, int]] = None,
    ):
        """
        Args:
            nodes:
                List of NodeConfig entries to manage.
            priorities:
                Optional override mapping: key -> priority (int).
                The key is typically the node's `name` or `id`.
                Higher number = more preferred.
        """
        self._nodes = list(nodes)
        self._priorities: Dict[str, int] = priorities or {}
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
                statuses.append(
                    NodeStatus(
                        config=cfg,
                        healthy=True,
                        last_error=None,
                        last_height=height,
                    )
                )
            except NodeClientError as e:
                statuses.append(
                    NodeStatus(
                        config=cfg,
                        healthy=False,
                        last_error=str(e),
                        last_height=None,
                    )
                )

        self._status = statuses
        # Also refresh the cached active client based on latest health
        best_cfg = self._select_best_config(statuses)
        self._active_client = NodeClient(best_cfg) if best_cfg is not None else None
        return statuses

    def get_best_node(self) -> NodeConfig:
        """
        Return the best available node configuration.

        Behaviour expected by tests:

          * If no nodes are configured → raise RuntimeError.
          * If all nodes are unhealthy → raise RuntimeError.
          * Otherwise, return the NodeConfig of the healthiest,
            highest-priority node (with Digi-Mobile preference).

        This method will trigger a probe if no recent status is available.
        """
        if not self._nodes:
            raise RuntimeError("No DigiByte nodes configured")

        # If we have no status yet, or nodes list has changed, probe afresh.
        if not self._status or len(self._status) != len(self._nodes):
            self.probe_all()

        best_cfg = self._select_best_config(self._status)
        if best_cfg is None:
            # All nodes unhealthy
            raise RuntimeError("No healthy DigiByte nodes available")

        # Keep the active client in sync so get_active_client() works.
        self._active_client = NodeClient(best_cfg)
        return best_cfg

    def get_active_client(self) -> NodeClient:
        """
        Return the currently selected NodeClient.

        If no client has been selected yet, this will select the best node
        (via get_best_node()) and construct a client for it.
        """
        if self._active_client is None:
            best_cfg = self.get_best_node()
            self._active_client = NodeClient(best_cfg)
        return self._active_client

    def get_status(self) -> List[NodeStatus]:
        """Return the last known status list (may be empty if not probed yet)."""
        return list(self._status)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _effective_priority(self, cfg: NodeConfig) -> int:
        """
        Compute an effective priority for a node.

        Order of precedence:

          1. External overrides in `self._priorities` keyed by
             cfg.name (if present) then cfg.id.
          2. cfg.priority attribute if present.
          3. Default priority 0.

        Digi-Mobile node (name == DIGIMOBILE_NAME) receives a large
        bonus so it is preferred when healthy, unless tests explicitly
        override with higher priorities for other nodes.
        """
        base = 0

        # Try to read a `priority` attribute from the config, if present.
        if hasattr(cfg, "priority"):
            try:
                base = int(getattr(cfg, "priority"))
            except (TypeError, ValueError):
                base = 0

        # External override: by name, then by id.
        key_name = getattr(cfg, "name", None)
        key_id = getattr(cfg, "id", None)

        if key_name is not None and key_name in self._priorities:
            base = int(self._priorities[key_name])
        elif key_id is not None and key_id in self._priorities:
            base = int(self._priorities[key_id])

        # Digi-Mobile gets a strong boost by default.
        if key_name == DIGIMOBILE_NAME:
            base += 1_000

        return base

    def _select_best_config(self, statuses: List[NodeStatus]) -> Optional[NodeConfig]:
        """
        Choose the best node among healthy ones using priority rules.

        Returns:
            NodeConfig of the best node, or None if no healthy nodes.
        """
        healthy_nodes = [s for s in statuses if s.healthy]
        if not healthy_nodes:
            return None

        def sort_key(status: NodeStatus) -> int:
            return self._effective_priority(status.config)

        # Highest effective priority wins; if equal, first in list wins.
        best_status = max(healthy_nodes, key=sort_key)
        return best_status.config
