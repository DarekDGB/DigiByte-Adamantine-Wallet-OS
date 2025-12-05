"""
Tests for WalletState / AccountState / AssetBalance models.

These tests are intentionally small and scenario-driven so future
contributors can see how the in-memory wallet view is expected to work.
"""

from core.data_models.wallet_state import (  # type: ignore[import]
    WalletState,
    AccountState,
    AssetBalance,
    AssetKind,
    Network,
)


def test_account_state_creates_asset_balances_on_demand():
    acc = AccountState(id="a1", label="Main")

    # No balances at first
    assert acc.balances == {}

    dgb_bal = acc.get_balance("DGB")
    assert dgb_bal.asset_id == "DGB"
    assert dgb_bal.kind == AssetKind.DGB
    assert dgb_bal.confirmed == 0

    # Asking again returns the same object, not a new one
    dgb_bal_2 = acc.get_balance("DGB")
    assert dgb_bal_2 is dgb_bal


def test_asset_balance_apply_delta_updates_totals():
    bal = AssetBalance(asset_id="DGB", kind=AssetKind.DGB)

    bal.apply_delta(confirmed_delta=100, pending_delta=20, locked_delta=5)

    assert bal.confirmed == 100
    assert bal.pending == 20
    assert bal.locked == 5
    assert bal.total == 125


def test_wallet_state_auto_creates_accounts_and_updates_dgb():
    wallet = WalletState(id="w1", label="Test wallet", network=Network.MAINNET)

    # No accounts initially
    assert wallet.accounts == {}

    # Apply DGB delta – this should create account "a1" on the fly
    wallet.apply_dgb_delta(account_id="a1", delta_minor=1_000)

    assert "a1" in wallet.accounts
    acc = wallet.accounts["a1"]

    dgb_bal = acc.get_balance("DGB")
    assert dgb_bal.confirmed == 1_000


def test_wallet_state_updates_dd_and_snapshot_balances():
    wallet = WalletState(id="w1", label="With DD")

    # Create an account and adjust both DGB and DD
    wallet.apply_dgb_delta(account_id="a1", delta_minor=2_500)
    wallet.apply_dd_delta(account_id="a1", delta_units=300)

    snapshot = wallet.snapshot_balances()

    assert "a1" in snapshot
    assert snapshot["a1"]["DGB"] == 2_500
    assert snapshot["a1"]["DD"] == 300
