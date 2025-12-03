"""
DigiAssets indexing strategy for Adamantine Wallet.

This module defines how the wallet discovers, groups, and tracks DigiAssets
on top of DigiByte UTXOs.

It stays deliberately generic and *does not* hard-code a particular DigiAssets
protocol dialect. Instead, it gives us:

- simple data structures for on-chain asset events
- an abstract IndexingStrategy interface
- a default "best-effort" implementation that can be replaced later

The goal is to make it easy to plug in:
- a full DigiAssets indexer
- a light-client indexer that only sees our own addresses
- or an external indexer API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Protocol, Sequence


# ---------------------------------------------------------------------------
# Core types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UtxoRef:
    """Reference to a DigiByte transaction output."""

    txid: str
    vout: int


@dataclass
class AssetBalance:
    """
    Logical balance for a single DigiAsset.

    `confirmed` is fully confirmed on-chain.
    `pending` is in mempool or awaiting enough confirmations.
    """

    asset_id: str
    confirmed: int = 0
    pending: int = 0

    def total(self) -> int:
        return self.confirmed + self.pending


@dataclass
class AssetEvent:
    """
    Parsed 'event' extracted from a UTXO or transaction that affects
    DigiAssets balances.

    The IndexingStrategy is responsible for turning low-level DigiByte
    transactions into these higher-level events.
    """

    # unique asset identifier (e.g. DigiAssets asset id / hash)
    asset_id: str

    # how much this event adds (positive) or subtracts (negative)
    # from the owner's balance
    amount_delta: int

    # which UTXO this came from (if any)
    utxo: Optional[UtxoRef] = None

    # whether this event is confirmed on-chain yet
    confirmed: bool = True

    # optional free-form metadata (decoded from OP_RETURN, etc.)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class AddressAssetSnapshot:
    """
    Snapshot of all DigiAssets related to a given wallet address.

    This is what the UI or higher-level wallet code will typically use.
    """

    address: str
    balances: Dict[str, AssetBalance] = field(default_factory=dict)

    def get_balance(self, asset_id: str) -> AssetBalance:
        if asset_id not in self.balances:
            self.balances[asset_id] = AssetBalance(asset_id=asset_id)
        return self.balances[asset_id]


# ---------------------------------------------------------------------------
# Strategy interface
# ---------------------------------------------------------------------------


class IndexingStrategy(Protocol):
    """
    Pluggable interface for DigiAssets indexing.

    Different implementations may:
    - parse raw DigiByte transactions directly
    - call into an external DigiAssets indexer
    - or use a hybrid approach (local filters + remote proofs)
    """

    def index_address_utxos(
        self,
        address: str,
        utxos: Sequence[UtxoRef],
    ) -> AddressAssetSnapshot:
        """
        Build a snapshot of DigiAssets balances for a single address,
        given a list of its UTXOs.

        Implementations are free to hit remote APIs or full nodes as needed.
        """
        ...


# ---------------------------------------------------------------------------
# Default "no-surprises" implementation
# ---------------------------------------------------------------------------


class NoopIndexingStrategy:
    """
    Minimal default implementation.

    This does *not* perform full DigiAssets parsing. Instead it acts as a
    safe placeholder that:

    - always returns an empty snapshot
    - can be swapped out later for a real indexer without touching callers
    """

    def index_address_utxos(
        self,
        address: str,
        utxos: Sequence[UtxoRef],
    ) -> AddressAssetSnapshot:
        # Currently we don't infer any asset balances from UTXOs.
        # This ensures the wallet behaves as a plain DGB wallet
        # until a proper DigiAssets indexer is configured.
        return AddressAssetSnapshot(address=address)


# ---------------------------------------------------------------------------
# In-memory helper for tests / prototypes
# ---------------------------------------------------------------------------


class StaticEventsIndexingStrategy:
    """
    Very small helper strategy used for unit tests or demos.

    You pre-load it with a mapping of address -> list of AssetEvent,
    and it will compute balances deterministically. This lets us test
    DigiAssets-aware UI flows without running a full indexer.
    """

    def __init__(self, events_by_address: Dict[str, Iterable[AssetEvent]]):
        self._events_by_address: Dict[str, List[AssetEvent]] = {
            addr: list(events) for addr, events in events_by_address.items()
        }

    def index_address_utxos(
        self,
        address: str,
        utxos: Sequence[UtxoRef],
    ) -> AddressAssetSnapshot:
        snapshot = AddressAssetSnapshot(address=address)

        for event in self._events_by_address.get(address, []):
            balance = snapshot.get_balance(event.asset_id)
            if event.confirmed:
                balance.confirmed += event.amount_delta
            else:
                balance.pending += event.amount_delta

        return snapshot
