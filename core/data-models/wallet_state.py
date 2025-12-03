"""
DigiByte Adamantine Wallet — Core Wallet State Models
-----------------------------------------------------

This module provides a small, language-agnostic *reference model* of
the Adamantine Wallet state. It is **not** a full implementation and
does not talk to DigiByte nodes or sign transactions. Instead, it
defines clean data structures that other languages (Kotlin, Swift,
TypeScript, Rust) can mirror.

You can safely evolve this file as the `core/data-models/*.md` specs
mature.

Suggested repo path:
    core/data-models/wallet_state.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class AssetKind(str, Enum):
    """Top‑level asset categories supported by the wallet.

    - DGB        : native DigiByte coin (UTXO)
    - DD         : DigiDollar synthetic unit (position-backed)
    - DIGIASSET  : DigiAssets issued on top of DGB
    """

    DGB = "DGB"
    DD = "DD"
    DIGIASSET = "DIGIASSET"


@dataclass
class Balance:
    """Represents the balance of a single asset within an account.

    Amounts are tracked in the *smallest unit*:
    - DGB  : satoshis (1 DGB = 100_000_000 units)
    - DD   : cents of 1.00 DD (or smallest DD unit you decide)
    - DigiAsset : protocol-defined base unit
    """

    asset_id: str
    kind: AssetKind
    confirmed: int = 0
    unconfirmed: int = 0

    @property
    def total(self) -> int:
        """Total spendable + pending units for this asset."""
        return self.confirmed + self.unconfirmed


@dataclass
class RiskSummary:
    """Lightweight risk/health summary for an account or wallet.

    This mirrors what the Adamantine shield surface will show:
    - score: 0–100 (higher is safer)
    - labels: free‑form tags like ["reorg_warning", "pqc_needed"]
    """

    score: int = 100
    labels: List[str] = field(default_factory=list)

    def add_label(self, label: str) -> None:
        if label not in self.labels:
            self.labels.append(label)

    def clamp_score(self) -> None:
        """Keep score in the 0–100 range."""
        if self.score < 0:
            self.score = 0
        elif self.score > 100:
            self.score = 100


@dataclass
class Account:
    """Logical Adamantine account.

    One account can have many underlying DGB addresses (for privacy)
    but appears as a single row in the UI.
    """

    id: str
    label: str
    addresses: List[str] = field(default_factory=list)
    balances: Dict[str, Balance] = field(default_factory=dict)
    risk: RiskSummary = field(default_factory=RiskSummary)

    def get_balance(self, asset_id: str) -> Balance:
        """Return a balance object for the given asset, creating if needed."""
        if asset_id not in self.balances:
            # Default kind is DIGIASSET for unknown IDs; callers can adjust.
            self.balances[asset_id] = Balance(
                asset_id=asset_id,
                kind=AssetKind.DIGIASSET,
            )
        return self.balances[asset_id]

    def total_for_kind(self, kind: AssetKind) -> int:
        """Sum balances for a specific asset kind within this account."""
        return sum(
            b.total for b in self.balances.values() if b.kind == kind
        )


@dataclass
class WalletState:
    """Top‑level Adamantine wallet snapshot.

    This is what gets persisted to disk / secure storage and is the
    main in‑memory model inside the clients.
    """

    version: int = 1
    network: str = "mainnet"  # or "testnet"
    accounts: Dict[str, Account] = field(default_factory=dict)
    active_account_id: Optional[str] = None
    risk: RiskSummary = field(default_factory=RiskSummary)

    # --- Account helpers -------------------------------------------------

    def add_account(self, account: Account) -> None:
        if account.id in self.accounts:
            raise ValueError(f"Account with id {account.id!r} already exists")
        self.accounts[account.id] = account
        if self.active_account_id is None:
            self.active_account_id = account.id

    def get_account(self, account_id: str) -> Account:
        try:
            return self.accounts[account_id]
        except KeyError as exc:
            raise KeyError(f"Unknown account id: {account_id!r}") from exc

    @property
    def active_account(self) -> Optional[Account]:
        if self.active_account_id is None:
            return None
        return self.accounts.get(self.active_account_id)

    # --- Aggregate views -------------------------------------------------

    def total_for_kind(self, kind: AssetKind) -> int:
        """Total units of a given asset kind across all accounts."""
        return sum(a.total_for_kind(kind) for a in self.accounts.values())

    def total_dgb(self) -> int:
        return self.total_for_kind(AssetKind.DGB)

    def total_dd(self) -> int:
        return self.total_for_kind(AssetKind.DD)

    # --- Mutators used by higher‑level transaction logic -----------------

    def apply_balance_delta(
        self,
        account_id: str,
        asset_id: str,
        kind: AssetKind,
        confirmed_delta: int = 0,
        unconfirmed_delta: int = 0,
    ) -> None:
        """Adjust balances in response to a transaction effect.

        Higher‑level transaction parsing should decide which account
        and asset to touch; this function just updates the numbers.
        """

        account = self.get_account(account_id)
        balance = account.get_balance(asset_id)
        balance.kind = kind  # ensure correct category

        balance.confirmed += confirmed_delta
        balance.unconfirmed += unconfirmed_delta

    # --- Simple factory helpers -----------------------------------------

    @classmethod
    def empty_mainnet(cls) -> "WalletState":
        """Convenience constructor for a new mainnet wallet."""
        return cls(version=1, network="mainnet")

    @classmethod
    def empty_testnet(cls) -> "WalletState":
        """Convenience constructor for a new testnet wallet."""
        return cls(version=1, network="testnet")
