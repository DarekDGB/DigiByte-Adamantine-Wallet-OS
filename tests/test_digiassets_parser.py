"""
Tests for the DigiAssets transaction parser skeleton.

These tests validate:

- Parser returns None when no DigiAssets envelope is present.
- Parser returns a DigiAssetTxView when a fake envelope is injected.
- Operation type mapping works (ISSUE, TRANSFER, etc.).
- Address extraction produces correct from/to lists.

This is intentionally simple because the full DigiAssets protocol
logic will be added later.
"""

from core.digiassets.tx_parser import DigiAssetTxParser, detect_digiasset_envelope
from core.digiassets.models import DigiAssetOperation, DigiAssetTxView


# -------------------------------------------------------------------------
# Monkey-patch helper for injecting fake envelopes during tests
# -------------------------------------------------------------------------

def fake_envelope_issue(tx):
    return {
        "operation": "ISSUE",
        "asset_id": "ASSET123",
        "payload": {}
    }


def fake_envelope_transfer(tx):
    return {
        "operation": "TRANSFER",
        "asset_id": "ASSET999",
        "payload": {}
    }


# -------------------------------------------------------------------------
# Test cases
# -------------------------------------------------------------------------

def test_parser_returns_none_when_no_envelope(monkeypatch):
    """
    If detect_digiasset_envelope returns None,
    parser must return None.
    """
    parser = DigiAssetTxParser()

    # Force detect_digiasset_envelope to return None
    monkeypatch.setattr(
        "core.digiassets.tx_parser.detect_digiasset_envelope",
        lambda tx: None
    )

    tx = {"txid": "XXX"}
    assert parser.parse(tx) is None


def test_parser_parses_issue_op(monkeypatch):
    """
    Parser must return DigiAssetTxView with correct op_type.
    """
    parser = DigiAssetTxParser()

    # Force envelope
    monkeypatch.setattr(
        "core.digiassets.tx_parser.detect_digiasset_envelope",
        fake_envelope_issue
    )

    raw_tx = {
        "txid": "TX123",
        "vin": [{"address": "D_ADDR_1"}],
        "vout": [{"address": "D_ADDR_2"}],
    }

    view = parser.parse(raw_tx, block_height=100)

    assert isinstance(view, DigiAssetTxView)
    assert view.txid == "TX123"
    assert view.block_height == 100
    assert view.op_type == DigiAssetOperation.ISSUE
    assert view.asset_id == "ASSET123"
    assert view.from_addresses == ["D_ADDR_1"]
    assert view.to_addresses == ["D_ADDR_2"]


def test_parser_parses_transfer_op(monkeypatch):
    """
    Transfer envelope should map to DigiAssetOperation.TRANSFER.
    """
    parser = DigiAssetTxParser()

    monkeypatch.setattr(
        "core.digiassets.tx_parser.detect_digiasset_envelope",
        fake_envelope_transfer
    )

    raw_tx = {"txid": "AAA", "vin": [], "vout": []}
    view = parser.parse(raw_tx)

    assert view.op_type == DigiAssetOperation.TRANSFER
    assert view.asset_id == "ASSET999"
