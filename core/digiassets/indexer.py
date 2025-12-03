"""
DigiByte Adamantine Wallet — DigiAssets Indexer
-----------------------------------------------

This module defines a *skeleton* indexer for DigiAssets activity.

Responsibilities (future fully-featured version):

- consume DigiAssetTxView objects from the parser
- determine which parts of the TX belong to the local wallet
- compute per-account, per-asset balance deltas
- feed those deltas into the WalletState model
- keep a lightweight in-memory view (or delegate to storage layer)

Right now this is intentionally minimal and safe. It defines:

- data structures for balance deltas
- a clear API surface for future logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set

from .models import DigiAssetTxView, DigiAssetOperation, DigiAssetAmount


@dataclass
class AssetBalanceDelta:
    """
    Represents the net change in a single asset for the wallet.

    For now this is wallet-wide; later we may extend it to be
    per-account if needed.
    """

    asset_id: str
    confirmed_delta: int = 0
    unconfirmed_delta: int = 0


class DigiAssetIndexer:
    """
    Stateless helper that converts DigiAssetTxView + wallet-owned
    address set into balance deltas.

    In a full implementation, this would also:
      - write into a database / storage layer,
      - maintain per-account history,
      - handle reorg rollbacks.

    Here we focus only on defining the interface and basic flow.
    """

    def compute_mempool_deltas(
        self,
        tx: DigiAssetTxView,
        wallet_addresses: Set[str],
    ) -> List[AssetBalanceDelta]:
        """
        Compute *unconfirmed* balance deltas for a mempool transaction.

        For now this skeleton does not implement detailed ownership
        logic; it assumes that once we know which amounts belong to
        the wallet, we can aggregate them into per-asset deltas.

        Args:
            tx: DigiAssets-aware transaction view.
            wallet_addresses: set of addresses owned by the wallet.

        Returns:
            List of AssetBalanceDelta describing unconfirmed changes.
        """
        # Placeholder: real implementation will inspect DigiAssetAmount.owner_script
        # and wallet address set to determine which in/out amounts apply.
        # For now we just return an empty list so integration code has
        # a stable type to work with.
        _ = (tx, wallet_addresses)
        return []

    def compute_confirmed_deltas(
        self,
        tx: DigiAssetTxView,
        wallet_addresses: Set[str],
    ) -> List[AssetBalanceDelta]:
        """
        Compute *confirmed* balance deltas for a block-confirmed transaction.

        This function mirrors compute_mempool_deltas but is used after
        the transaction is included in a block.

        Args:
            tx: DigiAssets-aware transaction view.
            wallet_addresses: set of addresses owned by the wallet.

        Returns:
            List of AssetBalanceDelta describing confirmed changes.
        """
        # Same as above: future logic will map in/out flows against
        # wallet ownership. For now, we provide the method signature.
        _ = (tx, wallet_addresses)
        return []

    # ------------------------------------------------------------------
    # Future extension points (documented but not yet implemented)
    # ------------------------------------------------------------------

    def _aggregate_for_wallet(
        self,
        amounts_in: List[DigiAssetAmount],
        amounts_out: List[DigiAssetAmount],
        wallet_addresses: Set[str],
        is_confirmed: bool,
    ) -> List[AssetBalanceDelta]:
        """
        INTERNAL: aggregate in/out amounts that belong to the wallet
        into per-asset deltas.

        This is where the real logic will live in a later step.
        For now, this method is only a design placeholder and is not
        invoked from the public API.
        """
        _ = (amounts_in, amounts_out, wallet_addresses, is_confirmed)
        return []
