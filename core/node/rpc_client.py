"""
core/node/rpc_client.py

Lightweight JSON-RPC client for DigiByte Core / Digi-Mobile nodes.

This module is intentionally dependency-free (standard library only) so it can
run in constrained environments (mobile, embedded, etc.).

Typical usage:

    from core.node.rpc_client import RpcConfig, RpcClient, RpcError

    cfg = RpcConfig(
        url="http://127.0.0.1:14022",
        username="digibyte",
        password="secret",
    )
    client = RpcClient(cfg)

    try:
        info = client.call("getblockchaininfo")
        print(info["blocks"])
    except RpcError as exc:
        # surface to logs / UI
        print(f"RPC failed: {exc}")

The higher-level NodeClient / NodeManager can wrap this to implement
health checks, failover, and priority selection between:

    - local Digi-Mobile node on Android
    - local desktop full node
    - remote mainnet nodes
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RpcError(RuntimeError):
    """Base error for all RPC-related failures."""


class RpcConnectionError(RpcError):
    """Failed to connect to the node (network / DNS / timeout, etc.)."""


class RpcResponseError(RpcError):
    """Node responded with a non-success HTTP code or an RPC error object."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RpcConfig:
    """
    Configuration for a single DigiByte JSON-RPC endpoint.

    Attributes
    ----------
    url:
        Full URL including scheme + host + port, e.g.
        "http://127.0.0.1:14022" or "http://10.0.2.15:14022".
    username / password:
        Basic-auth credentials for the RPC endpoint. If both are None, no
        Authorization header is sent (e.g. when using cookie auth or a proxy).
    timeout_seconds:
        Socket timeout for a single HTTP request.
    max_retries:
        How many times to retry on *transport-level* failures (connection
        refused, timeout, DNS error). RPC-level errors are **not** retried.
    retry_backoff_seconds:
        Sleep between retries. Kept simple and constant on purpose.
    """

    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    timeout_seconds: float = 5.0
    max_retries: int = 1
    retry_backoff_seconds: float = 0.5


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class RpcClient:
    """
    Tiny JSON-RPC client suitable for DigiByte Core / Digi-Mobile.

    This client is intentionally synchronous and minimal; higher-level
    orchestration (threading / async / batching) lives in NodeManager or
    platform-specific adapters.
    """

    def __init__(self, config: RpcConfig) -> None:
        self._config = config
        self._next_id = 0

    # ------------------------------ public API ------------------------------

    def call(self, method: str, params: Optional[List[Any]] = None) -> Any:
        """
        Call a JSON-RPC method and return its `result`.

        Raises:
            RpcConnectionError on transport issues.
            RpcResponseError if the node returns an RPC error or bad HTTP code.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params or [],
        }

        body_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
        }

        auth_header = self._build_auth_header()
        if auth_header:
            headers["Authorization"] = auth_header

        request = urllib.request.Request(
            self._config.url,
            data=body_bytes,
            headers=headers,
            method="POST",
        )

        attempt = 0
        last_transport_error: Optional[Exception] = None

        while True:
            try:
                with urllib.request.urlopen(
                    request, timeout=self._config.timeout_seconds
                ) as resp:
                    status = resp.getcode()
                    resp_body = resp.read().decode("utf-8")

                if status != 200:
                    raise RpcResponseError(
                        f"HTTP {status} from node at {self._config.url}"
                    )

                try:
                    decoded = json.loads(resp_body)
                except json.JSONDecodeError as exc:
                    raise RpcResponseError(
                        f"Invalid JSON response from node: {exc}"
                    ) from exc

                if "error" in decoded and decoded["error"] is not None:
                    err = decoded["error"]
                    raise RpcResponseError(
                        f"RPC error for '{method}': {err}"
                    )

                return decoded.get("result")

            except urllib.error.URLError as exc:
                # Transport-level failure; consider retrying.
                last_transport_error = exc
                attempt += 1
                if attempt > self._config.max_retries:
                    raise RpcConnectionError(
                        f"Failed to reach node at {self._config.url} "
                        f"after {attempt} attempt(s): {exc}"
                    ) from exc

                time.sleep(self._config.retry_backoff_seconds)

    # Convenience helpers ----------------------------------------------------

    def ping(self) -> bool:
        """
        Lightweight health check.

        Uses `getblockchaininfo` which is standard across DigiByte/Bitcoin-like
        nodes. Any successful call means the node is reachable and responsive.
        """
        try:
            self.call("getblockchaininfo", [])
            return True
        except RpcError:
            return False

    def get_block_height(self) -> Optional[int]:
        """
        Returns the current block height, or None if the call fails.

        This is intentionally lenient so NodeHealth scorers can use it without
        crashing the whole wallet.
        """
        try:
            info = self.call("getblockchaininfo", [])
            return int(info.get("blocks", 0))
        except (RpcError, ValueError, TypeError):
            return None

    # ------------------------------ internals -------------------------------

    def _next_request_id(self) -> int:
        self._next_id += 1
        return self._next_id

    def _build_auth_header(self) -> Optional[str]:
        user = self._config.username
        pwd = self._config.password
        if not user and not pwd:
            return None

        raw = f"{user or ''}:{pwd or ''}".encode("utf-8")
        token = base64.b64encode(raw).decode("ascii")
        return f"Basic {token}"
