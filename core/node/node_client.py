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


@dataclass
class NodeConfig:
    """
    Represents a single node entry from config/example-nodes.yml.
    """

    id: str
    host: str
    rpc_port: int
    tls: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    timeout_ms: int = 3000


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

    def _rpc(self, method: str, params: list[Any]) -> Any:
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
        except Exception as e:
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
