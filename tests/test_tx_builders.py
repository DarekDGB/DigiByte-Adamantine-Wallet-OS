"""
Tests for core/tx_builders.py

We verify that the high-level builders:

- create WalletTransaction with the correct TxKind
- wire wallet/account IDs and amounts correctly
- leave inputs/fees in a skeleton state (to be filled by node layer)
"""

from decimal import Decimal

from core.tx_builders import (
    TxBuildRequest,
    build_dgb_send_skeleton,
    build_dd_mint_skeleton,
    build_dd_redeem_skeleton,
    build_digiasset_skeleton,
    build_enigmatic_message_skeleton,
)
from core.transactions import TxKind, TxStatus, WalletTransaction, PaymentOutput


def _req(overrides: dict | None = None) -> TxBuildRequest:
    base = dict(
        wallet_id="w1",
        account_id="a1",
        to_address="dgb1testaddress",
        amount_sats=123_000,
        description="test tx",
        meta={"source": "unit-test"},
    )
    if overrides:
        base.update(overrides)
    return TxBuildRequest(**base)


# ---------------------------------------------------------------------------
# DGB send
# ---------------------------------------------------------------------------


def test_build_dgb_send_skeleton_basic():
    req = _req()
    tx = build_dgb_send_skeleton(tx_id="tx1", req=req, fee_rate_hint=1.5)

    assert isinstance(tx, WalletTransaction)
    assert tx.id == "tx1"
    assert tx.kind == TxKind.DGB_SEND
    assert tx.wallet_id == "w1"
    assert tx.account_id == "a1"
    assert tx.status == TxStatus.DRAFT
    assert tx.description == "test tx"

    # Outputs
    assert len(tx.outputs) == 1
    out: PaymentOutput = tx.outputs[0]
    assert out.address == "dgb1testaddress"
    assert out.value_sats == 123_000

    # Fee skeleton
    assert tx.fee.total_sats is None
    assert tx.fee.rate_sats_per_vbyte == Decimal("1.5")

    # Meta should include to_address and our custom key
    assert tx.meta["to_address"] == "dgb1testaddress"
    assert tx.meta["source"] == "unit-test"


# ---------------------------------------------------------------------------
# DigiDollar skeletons
# ---------------------------------------------------------------------------


def test_build_dd_mint_skeleton_sets_kind_and_meta():
    req = _req()
    tx = build_dd_mint_skeleton(tx_id="tx_dd_mint", req=req, oracle_price_hint=0.12)

    assert tx.id == "tx_dd_mint"
    assert tx.kind == TxKind.DIGIDOLLAR_MINT
    assert tx.wallet_id == "w1"
    assert tx.account_id == "a1"
    assert tx.status == TxStatus.DRAFT

    # DD mint skeleton: outputs left to DD engine
    assert tx.outputs == []

    # Fee is still a skeleton
    assert tx.fee.total_sats is None

    # Meta carries oracle hint
    assert tx.meta["oracle_price_hint"] == 0.12
    assert tx.meta["to_address"] == "dgb1testaddress"


def test_build_dd_redeem_skeleton_sets_kind_and_dd_amount():
    req = _req({"amount_sats": 500_000})
    tx = build_dd_redeem_skeleton(tx_id="tx_dd_redeem", req=req)

    assert tx.id == "tx_dd_redeem"
    assert tx.kind == TxKind.DIGIDOLLAR_REDEEM
    assert tx.status == TxStatus.DRAFT
    assert tx.outputs == []
    assert tx.fee.total_sats is None

    # DD amount should be recorded in meta
    assert tx.meta["dd_amount_units"] == 500_000
    assert tx.meta["to_address"] == "dgb1testaddress"


# ---------------------------------------------------------------------------
# DigiAssets + Enigmatic
# ---------------------------------------------------------------------------


def test_build_digiasset_skeleton_tags_op_kind():
    req = _req()
    tx = build_digiasset_skeleton(
        tx_id="tx_asset_mint",
        req=req,
        op_kind="mint",
    )

    assert tx.id == "tx_asset_mint"
    assert tx.kind == TxKind.DIGIASSET
    assert tx.status == TxStatus.DRAFT
    assert tx.outputs == []
    assert tx.fee.total_sats is None
    assert tx.meta["digiasset_op_kind"] == "mint"


def test_build_enigmatic_message_skeleton_marks_enigmatic():
    req = _req()
    tx = build_enigmatic_message_skeleton(tx_id="tx_enigmatic", req=req)

    assert tx.id == "tx_enigmatic"
    assert tx.kind == TxKind.ENIGMATIC_MESSAGE
    assert tx.status == TxStatus.DRAFT
    assert tx.outputs == []
    assert tx.fee.total_sats is None
    assert tx.meta["enigmatic"] is True
    assert tx.meta["to_address"] == "dgb1testaddress"
