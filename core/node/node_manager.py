"""
core.node.node_manager

NodeManager — select and manage DigiByte node backends for the wallet
and shield bridge.

This version is tailored to be:

  * Easy to test (tests monkeypatch `_is_healthy` heavily),
  * Simple to extend later with richer health checks,
  * Explicit about Digi-Mobile preference rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

# Name used by tests to identify the local Digi-Mobile node.
DIGIMOBILE_NAME = "digimobile"


@dataclass
class NodeConfig:
    """
    Minimal node configuration used by the wallet / tests.

    Fields are intentionally small; richer config (TLS, auth, etc.) can
    be added later without breaking existing tests, as long as `name`,
    `host` and `port` remain.
    """

    name: str
    host: str
    port: int


@dataclass
class NodeStatus:
    """Runtime health status for a single node."""

    config: NodeConfig
    healthy: bool
    last_error: Optional[str] = None


class NodeManager:
    """
    Manages a pool of node backends and selects the best available one.

    Behaviour expected by tests:

      * If no nodes are configured → raise RuntimeError.
      * If all nodes are unhealthy → raise RuntimeError.
      * Prefer Digi-Mobile (DIGIMOBILE_NAME) when it is healthy.
      * Otherwise choose the highest-priority healthy node.
        - Priority source = `priorities` dict (name -> int).
        - Higher number means more preferred.
        - Ties are resolved by original list order.
    """

    def __init__(
        self,
        nodes: List[NodeConfig],
        priorities: Optional[Dict[str, int]] = None,
    ) -> None:
        self._nodes: List[NodeConfig] = list(nodes)
        self._priorities: Dict[str, int] = dict(priorities or {})
        self._status: List[NodeStatus] = []

    # ------------------------------------------------------------------
    # Health probing
    # ------------------------------------------------------------------

    def _is_healthy(self, cfg: NodeConfig) -> bool:
        """
        Real health check.

        Tests *monkeypatch* this method to control behaviour, so the
        default implementation must be simple and side-effect free.

        For now we assume nodes are healthy by default; deeper checks
        live in `core.node.health` and can be wired in later.
        """
        return True

    def probe_all(self) -> List[NodeStatus]:
        """
        Probe all configured nodes and refresh `_status`.

        Returns:
            A list of NodeStatus entries (one per node).
        """
        statuses: List[NodeStatus] = []

        for cfg in self._nodes:
            try:
                ok = self._is_healthy(cfg)
                statuses.append(
                    NodeStatus(config=cfg, healthy=ok, last_error=None if ok else "unhealthy")
                )
            except Exception as exc:  # pragma: no cover – defensive
                statuses.append(NodeStatus(config=cfg, healthy=False, last_error=str(exc)))

        self._status = statuses
        return statuses

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def get_best_node(self) -> NodeConfig:
        """
        Return the best available node configuration.

        This will trigger a fresh probe if no status is available.
        """
        if not self._nodes:
            raise RuntimeError("No DigiByte nodes configured")

        # If we have no status yet, or nodes list changed, probe afresh.
        if not self._status or len(self._status) != len(self._nodes):
            self.probe_all()

        best_cfg = self._select_best_config(self._status)
        if best_cfg is None:
            raise RuntimeError("No healthy DigiByte nodes available")

        return best_cfg

    def _select_best_config(self, statuses: List[NodeStatus]) -> Optional[NodeConfig]:
        """
        Internal: choose the best node among the given status list.
        """
        healthy = [s for s in statuses if s.healthy]
        if not healthy:
            return None

        # 1) Prefer Digi-Mobile when healthy.
        for s in healthy:
            if s.config.name == DIGIMOBILE_NAME:
                return s.config

        # 2) Otherwise, choose by priority (default = 0).
        def prio(cfg: NodeConfig) -> int:
            return int(self._priorities.get(cfg.name, 0))

        healthy_sorted = sorted(
            healthy,
            key=lambda s: prio(s.config),
            reverse=True,
        )
        return healthy_sorted[0].config
