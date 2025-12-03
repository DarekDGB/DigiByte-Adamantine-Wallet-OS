"""
Tests for the DigiAssets indexer skeleton.

Right now the indexer does NOT implement full ownership logic.
These tests make sure:

- the public methods exist,
- they return a list of AssetBalanceDelta,
- they handle basic inputs without crashing.

Later, when real logic is added, these tests will be extended
to check actual balance delta behaviour.
"""

from typing import Set

from core.digiassets.indexer import DigiAssetIndexer, AssetBalanceDelta
from core.digiassets.models import DigiAssetTxView, DigiAssetAmount, DigiAssetOperation


def _make_dummy_tx() -> DigiAssetTxView:
    """
    Helper: create a minimal DigiAssetTxView object for tests.
    """
    return DigiAssetTxView(
        txid="TX_DUMMY",
        block_height=None,
        op_type=DigiAssetOperation.TRANSFER,
        asset_id="ASSET123",
        amounts_in=[
            DigiAssetAmount(asset_id="ASSET123", amount=100),
        ],
        amounts_out=[
            DigiAssetAmount(asset_id="ASSET123", amount=100),
        ],
        from_addresses=["D_FROM_1"],
        to_addresses=["D_TO_1"],
    )


def test_compute_mempool_deltas_returns_list():
    indexer = DigiAssetIndexer()
    tx = _make_dummy_tx()
    wallet_addrs: Set[str] = {"D_FROM_1", "D_TO_1"}

    deltas = indexer.compute_mempool_deltas(tx, wallet_addrs)

    assert isinstance(deltas, list)
    for d in deltas:
        assert isinstance(d, AssetBalanceDelta)


def test_compute_confirmed_deltas_returns_list():
    indexer = DigiAssetIndexer()
    tx = _make_dummy_tx()
    wallet_addrs: Set[str] = {"D_FROM_1", "D_TO_1"}

    deltas = indexer.compute_confirmed_deltas(tx, wallet_addrs)

    assert isinstance(deltas, list)
    for d in deltas:
        assert isinstance(d, AssetBalanceDelta)


def test_indexer_handles_empty_wallet_addresses():
    """
    Indexer should safely handle empty wallet address sets.
    """
    indexer = DigiAssetIndexer()
    tx = _make_dummy_tx()
    wallet_addrs: Set[str] = set()

    mempool_deltas = indexer.compute_mempool_deltas(tx, wallet_addrs)
    confirmed_deltas = indexer.compute_confirmed_deltas(tx, wallet_addrs)

    assert isinstance(mempool_deltas, list)
    assert isinstance(confirmed_deltas, list)
