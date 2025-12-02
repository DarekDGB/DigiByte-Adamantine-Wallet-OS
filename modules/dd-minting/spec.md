# DigiDollar (DD) Module — Specification (spec.md)

Status: **draft v0.1 – internal skeleton**

DigiDollar (DD) inside the Adamantine Wallet is a **synthetic stable-value layer**
backed 1:1 by locked DigiByte UTXOs.

Adamantine does not rely on smart contracts — DD is implemented as:
- deterministic minting & redeeming flows,
- transparent backing UTXO sets,
- audited balance state,
- Guardian‑protected actions,
- optional oracle checks.

---

## 1. Core Concepts

- **DD = DigiByte‑backed synthetic unit**
- **Fully backed**: every DD unit points to locked DGB UTXOs.
- **Non-custodial**: keys never leave Adamantine.
- **Local accounting**: DD balances are tracked inside the wallet.
- **Redeemable**: at any time, user can burn DD → unlock backing DGB.

DD is NOT:
- a token on-chain,
- a new consensus asset,
- a smart contract.

It is a **wallet-side synthetic unit** implemented with strict safety rules.

---

## 2. Data Structures

Linked to `wallet-state.md`.

### 2.1 DigiDollarState

```ts
DigiDollarState {
  total_dd_balance: number
  total_backing_satoshis: number

  positions: DigiDollarPosition[]

  auto_rollover: boolean
  prefer_onchain_mint: boolean
  settlement_address?: string

  last_sync_at?: timestamp
}
```

### 2.2 DigiDollarPosition

```ts
DigiDollarPosition {
  id: string
  created_at: timestamp

  mint_txid: string
  backing_utxos: { txid: string; vout: number }[]

  dd_amount: number
  backing_satoshis: number

  status: "active" | "redeeming" | "redeemed" | "disputed"
}
```

---

## 3. Minting Logic (High Level)

1. User chooses:
   - amount of DGB → convert to DD,
   - which account to use for backing funds.
2. UI fetches eligible UTXOs.
3. Risk Engine evaluates environment.
4. Guardian returns a verdict.
5. If allowed, wallet:
   - creates a locking TX (mint TX),
   - locks selected UTXOs,
   - updates DDState.

Mint mode:
- **on-chain** (preferred): UTXOs explicitly locked.
- **off-chain emulation** (optional future): internal accounting only.

---

## 4. Redeeming Logic (High Level)

1. User selects DD position or amount.
2. Guardian evaluates.
3. If allowed:
   - wallet creates unlock TX,
   - burns equivalent DD amount,
   - unlocks backing UTXOs,
   - updates state.

Safety:
- locked UTXOs cannot be double-spent.
- no DD can exist without backing.

---

## 5. Oracle Inputs (Optional)

Oracle helps with:
- DGB → DD conversion hints,
- stability checks,
- large mint warnings.

Minimal oracle fields:
```ts
OracleSnapshot {
  dgb_usd_rate: number
  volatility_index: number
  timestamp: timestamp
}
```

Adamantine must work **without an oracle**.

---

## 6. Guardian Integration

Guardian evaluates:
- backing amount,
- novelty of addresses,
- shield status,
- patterns from Adaptive Core.

Guardian must enforce:
- higher verification for large DD mints,
- temporary blocks during high-risk conditions,
- stricter policies if device security is weak.

---

## 7. Shield Integration

Sentinel signals:
- mempool stress
- abnormal fees
- anomaly spikes

DQSN signals:
- unsafe nodes
- fork suspicion

ADN signals:
- lockdown modes

QAC signals:
- abnormal confirmation patterns on mint TXs

Adaptive Core:
- can recommend temporary halts for DD mints.

---

## 8. Privacy

DD state:
- stored locally
- encrypted at rest
- backed up only with explicit user approval

No DD history is ever uploaded unless telemetry opt‑in is enabled.

---

## 9. Future Extensions

- multi-account DD baskets
- DD payment requests via Enigmatic
- automated DD rebalancing modes
- multi-party minting (advanced)
- exporting DD positions for auditing
