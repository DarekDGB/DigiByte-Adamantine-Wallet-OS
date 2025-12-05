"""
Core account models for Adamantine Wallet.

These models are intentionally small and framework-agnostic so they can
be reused by Android, iOS, Web, and backend tools.

They do NOT contain any persistence, networking, or UI logic.
"""


from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional


class AssetKind(Enum):
    """
    High-level asset types that Adamantine understands.

    - DGB        : native DigiByte coin (UTXO)
    - DIGIASSET  : DigiAssets (tokens / NFTs on top of DGB)
    - DIGIDOLLAR : DigiDollar (DD) representation
    """

    DGB = auto()
    DIGIASSET = auto()
    DIGIDOLLAR = auto()


@dataclass
class AssetBalance:
    """
    Generic balance container for a single asset in an account.

    All numbers are stored as integers in "minor units" (e.g. satoshi-like
    for DGB, smallest unit for DD or DigiAssets). Conversion to human-readable
    units is done at the UI layer.
    """

    confirmed: int = 0
    pending_in: int = 0
    pending_out: int = 0

    @property
    def effective(self) -> int:
        """
        Effective spendable balance approximation.

        For now we model it as:

            confirmed + pending_in - pending_out

        This may be refined later when we have more detailed UTXO / lock
        information available.
        """
        return self.confirmed + self.pending_in - self.pending_out


@dataclass
class Account:
    """
    A single logical account inside the wallet.

    Examples:
      - "Main DGB"
      - "Cold Storage"
      - "Business Account"

    Each account can hold:
      - native DGB balance
      - multiple DigiAssets
      - optional DigiDollar (DD) positions
    """

    id: str
    label: str
    receive_address: str

    # Native DGB balance for this account
    dgb_balance: AssetBalance = field(default_factory=AssetBalance)

    # DigiAssets by asset_id -> balance
    digiassets: Dict[str, AssetBalance] = field(default_factory=dict)

    # DigiDollar (DD) balance / positions for this account.
    # Key can be a position id or just "DD" for a single bucket,
    # depending on how the DD module evolves.
    digidollar: Dict[str, AssetBalance] = field(default_factory=dict)

    # Optional metadata for UI tags, categories, etc.
    metadata: Dict[str, str] = field(default_factory=dict)

    def get_asset_balance(self, kind: AssetKind, asset_id: Optional[str] = None) -> Optional[AssetBalance]:
        """
        Generic accessor for balances.

        - DGB: ignore asset_id, return native DGB balance
        - DIGIASSET: asset_id must be provided
        - DIGIDOLLAR: asset_id can be a position id or "DD"
        """
        if kind is AssetKind.DGB:
            return self.dgb_balance

        if kind is AssetKind.DIGIASSET:
            if asset_id is None:
                return None
            return self.digiassets.get(asset_id)

        if kind is AssetKind.DIGIDOLLAR:
            if asset_id is None:
                asset_id = "DD"
            return self.digidollar.get(asset_id)

        return None

    def ensure_digiasset(self, asset_id: str) -> AssetBalance:
        """
        Ensure that a DigiAsset balance bucket exists and return it.
        """
        if asset_id not in self.digiassets:
            self.digiassets[asset_id] = AssetBalance()
        return self.digiassets[asset_id]

    def ensure_digidollar(self, position_id: str = "DD") -> AssetBalance:
        """
        Ensure that a DigiDollar balance bucket exists and return it.
        """
        if position_id not in self.digidollar:
            self.digidollar[position_id] = AssetBalance()
        return self.digidollar[position_id]


@dataclass
class AccountPortfolio:
    """
    Collection of accounts for a single wallet.

    This is a thin convenience wrapper around a dict so that wallet_state.py
    (and future services) have a clear type to work with.
    """

    accounts: Dict[str, Account] = field(default_factory=dict)

    def add_account(self, account: Account) -> None:
        self.accounts[account.id] = account

    def get_account(self, account_id: str) -> Optional[Account]:
        return self.accounts.get(account_id)

    def all_accounts(self) -> Dict[str, Account]:
        return dict(self.accounts)
