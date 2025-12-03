"""
DigiByte Adamantine Wallet — DigiAssets Core Models
---------------------------------------------------

These dataclasses represent the *logical view* of DigiAssets activity
inside the Adamantine Wallet.

They do NOT define the wire / on-chain encoding. That is handled by the
canonical DigiAssets spec and the parsing layer. Instead, these models
are the clean, in-memory representation used by:

- the DigiAssets parser
- the DigiAssets indexer
- the wallet UI
- the risk engine
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class DigiAssetOperation(str, Enum):
    """High-level operation types recognised by the wallet."""

    ISSUE = "ISSUE"
    TRANSFER = "TRANSFER"
    BURN = "BURN"
    REISSUE = "REISSUE"


class SupplyModel(str, Enum):
    """Asset supply model as seen by the wallet."""

    FIXED = "FIXED"
    CAPPED = "CAPPED"
    REISSUABLE = "REISSUABLE"


@dataclass
class DigiAssetDefinition:
    """
    Static properties of a DigiAsset as the wallet understands it.

    This is typically derived from the initial ISSUE transaction and
    optional off-chain metadata.
    """

    asset_id: str
    name: str
    symbol: str
    supply_model: SupplyModel
    decimals: int
    issuer_txid: str
    issuer_address: Optional[str] = None
    metadata_uri: Optional[str] = None


@dataclass
class DigiAssetAmount:
    """
    Amount of a DigiAsset attached to a specific UTXO or output.
    """

    asset_id: str
    amount: int  # smallest unit of the asset
    owner_script: Optional[str] = None  # scriptPubKey, if known
    is_change: bool = False


@dataclass
class DigiAssetTxView:
    """
    Normalised view of a DigiAssets-aware DigiByte transaction.

    This is what the parser produces and what the indexer / UI consume.
    """

    txid: str
    block_height: Optional[int]  # None for mempool
    op_type: DigiAssetOperation
    asset_id: str
    amounts_in: List[DigiAssetAmount] = field(default_factory=list)
    amounts_out: List[DigiAssetAmount] = field(default_factory=list)
    # Optional fields for richer history / UX:
    from_addresses: List[str] = field(default_factory=list)
    to_addresses: List[str] = field(default_factory=list)

    @property
    def total_in(self) -> int:
        """Sum of all incoming asset units for this asset_id."""
        return sum(a.amount for a in self.amounts_in if a.asset_id == self.asset_id)

    @property
    def total_out(self) -> int:
        """Sum of all outgoing asset units for this asset_id."""
        return sum(a.amount for a in self.amounts_out if a.asset_id == self.asset_id)

    @property
    def net_delta(self) -> int:
        """
        Net change in asset amount from the wallet's perspective.

        Interpretation is up to the indexer:
        - ISSUE  : new supply created
        - TRANSFER: incoming / outgoing relative to wallet addresses
        - BURN   : supply destroyed
        - REISSUE: additional supply created under rules
        """
        return self.total_out - self.total_in
