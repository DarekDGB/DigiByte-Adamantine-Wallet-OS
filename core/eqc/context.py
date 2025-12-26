"""
EQC Context

Context is the immutable snapshot of conditions under which an action
is requested inside Adamantine Wallet OS.

EQC decisions must be based ONLY on data present in Context.
No hidden globals. No side effects.

Author: DarekDGB
License: MIT (see root LICENSE)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from hashlib import sha256
import json
import time


@dataclass(frozen=True)
class DeviceContext:
    device_id: str
    device_type: str          # mobile, hardware, airgap, etc.
    os: str                   # ios, android, linux
    trusted: bool = False
    first_seen_ts: Optional[int] = None


@dataclass(frozen=True)
class NetworkContext:
    network: str              # mainnet, testnet
    fee_rate: Optional[int] = None
    peer_count: Optional[int] = None


@dataclass(frozen=True)
class UserContext:
    user_id: Optional[str] = None
    biometric_available: bool = False
    pin_set: bool = False


@dataclass(frozen=True)
class ActionContext:
    action: str               # send, mint, redeem, sign, vote
    asset: str                # DGB, DigiAsset, DigiDollar
    amount: Optional[int] = None
    recipient: Optional[str] = None


@dataclass(frozen=True)
class EQCContext:
    """
    Canonical context passed into EQC.

    This object is hashed and may be bound to WSQK scopes later.
    """
    action: ActionContext
    device: DeviceContext
    network: NetworkContext
    user: UserContext
    timestamp: int = field(default_factory=lambda: int(time.time()))
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.__dict__,
            "device": self.device.__dict__,
            "network": self.network.__dict__,
            "user": self.user.__dict__,
            "timestamp": self.timestamp,
            "extra": dict(self.extra),
        }

    def context_hash(self) -> str:
        """
        Stable hash of the context used for:
        - audit logs
        - WSQK binding
        - replay protection
        """
        encoded = json.dumps(self.to_dict(), sort_keys=True).encode()
        return sha256(encoded).hexdigest()
