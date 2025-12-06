"""
NodeClient — Unified interface for talking to DigiByte nodes.

Adamantine can connect to:
  • Local Digi-Mobile (Android full node)
  • Remote DigiByte Core JSON-RPC nodes
  • Testnet nodes

This client is intentionally simple and fully mockable.
All higher layers (Wallet Core, Guardian, Shield Bridge)
depend ONLY on this abstraction, never on raw RPC calls.
"""

from __future__ import annotations

import json
import base64
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional, List


@dataclass(init=False)
class NodeConfig:
    """
    Represents a single node entry from config/example-nodes.yml.

    Test compatibility:

    The unit tests construct this as:

        NodeConfig(name="node_a", host="host", port=8332)

    while the Adamantine code historically used:

        NodeConfig(id="node_a", host="host", rpc_port=8332)

    This class supports **both** calling styles. Internally we keep
    the original attributes:

        id, host, rpc_port, tls, username, password, timeout_ms
    """

    id: str
    host: str
    rpc_port: int
    tls: bool
    username: Optional[str]
    password: Optional[str]
    timeout_ms: int

    def __init__(
        self,
        *,
        # Adamantine-style parameters
        id: Optional[str] = None,
        rpc_port: Optional[int] = None,
        # Test-style / friendly parameters
        name: Optional[str] = None,
        port: Optional[int] = None,
        # Shared
        host: str,
        tls: bool = False,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout_ms: int = 3000,
    ) -> None:
        """
        Accept both (id + rpc_port) and (name + port).

        Precedence:
          - id takes precedence over name
          - rpc_port takes precedence over port
        """
        effective_port = rpc_port if rpc_port is not None else (port if port is not None else 8332)
        effective_id = id or name or f"{host}:{effective_port}"

        self.id = effective_id
        self.host = host
        self.rpc_port = effective_port
        self.tls = tls
        self.username = username
        self.password = password
        self.timeout_ms = timeout_ms


class NodeClientError(Exception):
    pass


class NodeClient:
    """
    Thin JSON-RPC wrapper used by Adamantine Wallet.
    Works with DigiByte Core and Digi-Mobile identically.
    """

    def __init__(self, config: NodeConfig):
        self.cfg = config

        proto = "https" if config.tls else "http"
        self.base_url = f"{proto}://{config.host}:{config.rpc_port}"

        if config.username and config.password:
            auth_raw = f"{config.username}:{config.password}".encode("utf-8")
            self.auth_header = base64.b64encode(auth_raw).decode("ascii")
        else:
            self.auth_header = None

    # ---------------------------------------------------------
    # Internal helper
    # ---------------------------------------------------------

    def _rpc(self, method: str, params: List[Any]) -> Any:
        """
        Send JSON-RPC request to DigiByte node.
        """
        payload = json.dumps({
            "jsonrpc": "1.0",
            "id": "adamantine",
            "method": method,
            "params": params,
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
        }
        if self.auth_header:
            headers["Authorization"] = "Basic " + self.auth_header

        req = urllib.request.Request(self.base_url, data=payload, headers=headers)
        timeout_sec = self.cfg.timeout_ms / 1000

        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                data = json.load(resp)
        except Exception as e:  # pragma: no cover - safety
            raise NodeClientError(f"RPC error calling {method}: {e}")

        if "error" in data and data["error"]:
            raise NodeClientError(f"RPC method {method} returned error: {data['error']}")

        return data.get("result")

    # ---------------------------------------------------------
    # Public RPC wrappers
    # ---------------------------------------------------------

    def get_block_count(self) -> int:
        return self._rpc("getblockcount", [])

    def get_balance(self) -> float:
        return self._rpc("getbalance", [])

    def list_utxos(self, address: str) -> List[Dict[str, Any]]:
        return self._rpc("listunspent", [0, 9999999, [address]])

    def estimate_fee(self, conf_target: int = 2) -> float:
        return self._rpc("estimatesmartfee", [conf_target]).get("feerate", 0.0)

    def broadcast_raw_tx(self, raw_hex: str) -> str:
        return self._rpc("sendrawtransaction", [raw_hex])

    def get_mempool_info(self) -> Dict[str, Any]:
        return self._rpc("getmempoolinfo", [])

    def get_raw_tx(self, txid: str) -> Dict[str, Any]:
        return self._rpc("getrawtransaction", [txid, True])
