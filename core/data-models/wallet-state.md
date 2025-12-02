# DigiByte Adamantine Wallet — Wallet State Model

Status: **draft v0.1 – internal skeleton**

This document defines the **canonical in-memory + persisted state** model
for the DigiByte Adamantine Wallet. The goal is to keep the model:

- explicit
- implementation-agnostic (can be used from web / iOS / Android)
- stable over time, so modules (Guardian Wallet, QWG, DD minting, Enigmatic)
  can rely on the same structure.

> NOTE: This is a **conceptual model**, not a database schema. Concrete
> storage layouts (SQLite, CoreData, IndexedDB, etc.) can adapt from this.

---

## 1. Core Concepts

Adamantine tracks wallet state at three main layers:

1. **Profile** – who is using the wallet on this device.
2. **Account** – a logical grouping of keys, addresses and balances
   (e.g. “Main DGB”, “Cold Storage”, “Business”, “DD Treasury”).
3. **Network Integration** – how local state connects to:
   - DigiByte full nodes / light clients
   - Quantum Shield endpoints
   - Oracles (for DD)
   - Enigmatic communication relays

Every other object in the model hangs from these three.

---

## 2. Profile

```ts
Profile {
  id: string                 // locally unique UUID for this profile
  created_at: timestamp
  last_active_at: timestamp

  display_name?: string      // e.g. "DarekDGB"
  avatar_url?: string        // local or remote image

  // UX preferences
  locale: string             // e.g. "en-GB"
  fiat_currency: string      // e.g. "GBP"
  theme: "light" | "dark" | "system"

  // Security posture for the whole profile
  security_level: "standard" | "hardened" | "experimental"
  require_biometric_for_send: boolean
  require_biometric_for_settings: boolean
  require_guardian_for_high_risk: boolean
}
```

A single device MAY support multiple profiles, but the default UX is
**one active profile per device**.

---

## 3. Accounts

An **Account** is a logical container for one or more DigiByte key sets,
balances and Guardian / QWG policies.

```ts
Account {
  id: string
  profile_id: string         // FK → Profile.id

  label: string              // "Main", "Cold", "DD Vault"
  purpose: "personal" | "business" | "cold" | "dd-treasury" | "other"

  creation_origin:
    | "generated"            // keys created inside Adamantine
    | "imported-seed"        // BIP39 / DigiByte seed
    | "imported-wif"         // one or more WIF keys
    | "watch-only"           // xpub / address-only

  // key material or references (see section 4)
  key_sets: KeySetRef[]

  // balances and UTXOs
  balances: BalanceSnapshot
  utxos: UtxoSet

  // guardian / shield state
  guardian_state: GuardianState
  risk_profile: RiskProfileRef
  last_risk_refresh_at?: timestamp

  // DD (DigiDollar) specific state
  dd_state?: DigiDollarState

  // Enigmatic integration
  enigmatic_identity?: EnigmaticIdentityRef

  // Basic flags
  is_archived: boolean
  is_hidden: boolean
}
```

Accounts give the UX structure and let Guardian / QWG treat different
funds with different policies (e.g. “Main” vs “Cold”).

---

## 4. Key Material & Addresses

Adamantine must support different key sources while **never exposing
raw secrets** to modules that don’t need them.

### 4.1 KeySet

```ts
KeySet {
  id: string
  account_id: string

  kind: "seed" | "single-wif" | "xprv" | "xpub" | "hardware-ref"

  // Encrypted or external references
  encrypted_payload?: bytes      // app-specific encrypted blob
  hardware_fingerprint?: string  // if living on hardware wallet

  // Metadata
  derivation_path?: string       // e.g. "m/44'/20'/0'/0"
  network: "DGB-mainnet" | "DGB-testnet"
  is_watch_only: boolean
  created_at: timestamp
  last_used_at?: timestamp
}
```

The **actual decryption keys** for `encrypted_payload` are held by the
platform keychain / secure enclave, not stored directly here.

### 4.2 AddressRecord

```ts
AddressRecord {
  id: string
  account_id: string
  keyset_id: string

  address: string               // DGB address string
  kind: "external" | "change"
  derivation_index?: number

  first_seen_at?: timestamp
  last_used_at?: timestamp

  total_received: number        // in satoshis
  total_sent: number            // in satoshis
  unconfirmed_balance: number   // in satoshis
  confirmed_balance: number     // in satoshis

  labels: string[]              // "Mining", "Cold", etc.
}
```

Addresses are discoverable by the sync engine using standard DigiByte
derivation rules.

---

## 5. Balances & UTXOs

### 5.1 BalanceSnapshot

```ts
BalanceSnapshot {
  confirmed: number       // satoshis
  unconfirmed: number     // satoshis
  locked: number          // satoshis – reserved by pending TXs or DD
  spendable: number       // satoshis – derived value

  last_updated_at: timestamp
}
````

### 5.2 Utxo

```ts
Utxo {
  txid: string
  vout: number

  address: string
  account_id: string

  amount: number          // satoshis
  script_pub_key: string
  confirmations: number

  // Flags
  is_locked: boolean      // cannot be spent (e.g. DD backing)
  is_dust: boolean
  is_change: boolean

  // Shield / Guardian annotations
  risk_level: "low" | "medium" | "high" | "critical"
  risk_notes?: string
}
```

### 5.3 UtxoSet

```ts
UtxoSet = Utxo[]
```

The coin selection logic operates purely on `UtxoSet` plus the
`GuardianState` rules.

---

## 6. Guardian & Quantum Shield State

### 6.1 GuardianState

```ts
GuardianState {
  mode: "off" | "observe" | "enforce"

  // thresholds keyed by risk level
  send_policy: {
    low: GuardianAction
    medium: GuardianAction
    high: GuardianAction
    critical: GuardianAction
  }

  // cached insight from shield
  last_overall_risk: "unknown" | "low" | "medium" | "high" | "critical"
  last_overall_risk_reason?: string

  // shortcuts for UI
  is_temporarily_locked: boolean
  locked_until?: timestamp
}

GuardianAction = 
  | "allow"
  | "require-local-confirmation"
  | "require-biometric"
  | "require-passphrase"
  | "block-and-alert"
```

### 6.2 RiskProfileRef

```ts
RiskProfileRef {
  id: string                    // matches config/risk-profiles.yml
  label: string                 // "Safe Default", "Paranoid", etc.
}
```

### 6.3 ShieldIntegrationState (per profile)

```ts
ShieldIntegrationState {
  sentinel_endpoint: string
  dqsn_endpoint: string
  adn_endpoint: string
  qac_endpoint: string
  adaptive_core_endpoint: string

  last_heartbeat_at?: timestamp
  last_config_sync_at?: timestamp

  status: "unknown" | "online" | "degraded" | "offline"
}
```

The wallet never needs to know the internals of the shield – only
how to send events and read risk scores.

---

## 7. DigiDollar (DD) State

DD is treated as a **module attached to one or more accounts**.

```ts
DigiDollarState {
  // high-level position
  total_dd_balance: number        // in DD units
  total_backing_satoshis: number  // how much DGB is backing DD

  // detailed positions per mint
  positions: DigiDollarPosition[]

  // operational settings
  auto_rollover: boolean
  prefer_onchain_mint: boolean
  settlement_address?: string     // DGB address dedicated to DD

  last_sync_at?: timestamp
}

DigiDollarPosition {
  id: string
  created_at: timestamp

  // linkage to on-chain TXs
  mint_txid: string
  backing_utxos: { txid: string; vout: number }[]

  dd_amount: number
  backing_satoshis: number

  status: "active" | "redeeming" | "redeemed" | "disputed"
}
```

This structure allows the wallet to always know:

- how much DD the user holds
- which UTXOs are locked as backing
- which mints / redeems are still in-flight

---

## 8. Enigmatic Identity & Messaging State

The wallet integrates with Johnny’s **Enigmatic** protocol for
Layer‑0 communication.

```ts
EnigmaticIdentityRef {
  id: string                    // local UUID
  protocol_version: string      // e.g. "enigmatic-1"

  // binding between wallet and chat
  primary_account_id: string
  primary_address: string       // DGB address used as identity anchor

  // key references (stored securely)
  public_key: string
  encrypted_private_key_ref: string

  // UX
  display_name?: string
  avatar_url?: string
}
```

Message state itself is handled in the **Enigmatic module**, but it
will reuse `message-model.md` for the envelope structure.

---

## 9. Settings & Local Metadata

```ts
Settings {
  // networking
  preferred_nodes: string[]      // custom DigiByte nodes
  use_tor: boolean
  allow_unsafe_nodes: boolean

  // fees
  fee_strategy: "auto" | "slow" | "normal" | "fast" | "custom"
  custom_fee_sats_per_byte?: number

  // privacy
  hide_balance_by_default: boolean
  require_auth_to_show_balance: boolean

  // backups
  last_backup_prompt_at?: timestamp
  has_acknowledged_seed_backup: boolean
}
```

---

## 10. Sync & Cache State

```ts
SyncState {
  last_full_scan_at?: timestamp
  last_incremental_sync_at?: timestamp

  last_known_block_height?: number
  last_known_block_hash?: string

  // per-account markers (for gap limit / discovery)
  account_markers: {
    [account_id: string]: {
      last_external_index: number
      last_change_index: number
    }
  }
}
```

This state allows the sync engine to resume quickly on mobile and
avoid re-scanning from genesis.

---

## 11. Putting It Together (High-Level Aggregates)

In practice, most code will operate on a small set of aggregate
objects instead of raw tables:

```ts
WalletStore {
  profile: Profile
  settings: Settings
  shield_integration: ShieldIntegrationState

  accounts: Account[]
  key_sets: KeySet[]
  addresses: AddressRecord[]
  utxos: Utxo[]

  sync: SyncState
}
```

Modules like Guardian Wallet, QWG, DD Minting and Enigmatic should
treat this **WalletStore** as the single source of truth and expose
read‑only views where possible.

Future versions of this document will:

- add explicit JSON schemas for each type
- define migration rules between versions
- describe how to persist this model on each platform.
```

