"""
Transport client abstraction for calling external shield services.

This skeleton does not define any concrete network protocol.
It only provides a minimal interface that layer adapters can build on.

MIT Licensed.
Author: @Darek_DGB
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTransportClient(ABC):
    """
    Abstract transport client.

    Implementations could use HTTP, gRPC, local IPC, or in-process calls.
    """

    @abstractmethod
    def call(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a synchronous request to the given endpoint.

        Implementations should raise an exception if the underlying
        transport fails (connection refused, timeout, invalid response).
        """


class InProcessTransportClient(BaseTransportClient):
    """
    Simple placeholder client that echoes the payload.

    This keeps the skeleton safe and testable without invoking real network IO.
    """

    def call(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"endpoint": endpoint, "echo": payload, "status": "noop"}
