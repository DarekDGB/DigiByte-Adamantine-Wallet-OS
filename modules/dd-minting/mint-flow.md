# DigiDollar (DD) Minting — Flow (mint-flow.md)

Status: **draft v0.1 – internal skeleton**

This document describes the **end-to-end flow** for minting DigiDollar (DD)
inside the Adamantine Wallet.

It expands the high-level logic from `spec.md` into a concrete sequence
of steps involving:

- UI
- WalletStore (state)
- Risk Engine
- Guardian Wallet
- Shield Bridge
- UTXO / TX Builder
- DD State updates

---

## 1. Preconditions

- Wallet is synced enough to:
  - know balances / UTXOs for the chosen account,
  - know current ShieldIntegrationState (even if degraded).
- User has selected:
  - **backing account** (source of DGB),
  - DD amount OR DGB amount to convert.
- Device security: no hard “block” conditions (e.g. known exploit)
  OR user has been informed and acknowledged risk (implementation detail).

---

## 2. Amount Handling

Two possible UX paths:

1. **User enters DGB amount**
   - wallet computes corresponding DD amount (1 DD ≈ 1 DGB, or other rule),
   - exact conversion logic documented in `oracle-and-risks.md`.

2. **User enters DD amount**
   - wallet computes required backing_satoshis using either:
     - static rate (1:1),
     - or oracle hint with safety margins.

Both paths produce:

```ts
MintIntent {
  backing_account_id: string
  dd_amount: number
  backing_satoshis: number
  settlement_address?: string  // optional, may default to a DD-specific addr
}
```

---

## 3. UTXO Selection

Using `UtxoSet` from `wallet-state.md`, the wallet selects backing UTXOs:

Goals:
- avoid dust,
- avoid mixing suspicious UTXOs (if flagged by shield),
- keep number of inputs reasonable.

Output:

```ts
MintBackingSelection {
  selected_utxos: Utxo[]
  total_backing_satoshis: number
  change_address: string
}
```

If no suitable UTXOs are available:
- UI shows error: “Insufficient clean funds for DD mint”.

---

## 4. Build ActionRequest for Guardian

The UI (or application core) builds:

```ts
ActionRequest {
  id: string
  timestamp: timestamp

  kind: "mint-dd"
  profile_id: string
  account_id: backing_account_id

  amount_dd: dd_amount
  amount_sats: backing_satoshis

  from_address?: string          // may be omitted or one of the backing addrs
  to_address?: string            // optional settlement address

  extras: {
    "backing_utxo_count": number,
    "has_suspicious_utxos": boolean,
    "oracle_snapshot"?: { ... },
    "mint_mode": "onchain"
  }

  device_security_state: DeviceSecuritySnapshot
  network_state: NetworkStateSnapshot
}
```

`DeviceSecuritySnapshot` and `NetworkStateSnapshot` come from the local
context described in `risk-engine/inputs.md`.

---

## 5. Risk Evaluation & Guardian Verdict

Flow:

```text
1. Risk Engine builds RiskInput:
     - action = ActionRequest
     - shield = ShieldStatusSnapshot (Sentinel, DQSN, ADN, QAC)
     - local  = LocalContextSnapshot
     - adaptive_overlay = AdaptiveOverlaySnapshot (if any)

2. Risk Engine → RiskAssessment { level, score, contributing_factors }

3. Guardian takes:
     - RiskAssessment
     - account’s risk profile & overrides
     - global / profile guardian configs
   and produces GuardianVerdict.
```

Possible outcomes:

- `allow`
- `require-local-confirmation`
- `require-biometric`
- `require-passphrase`
- `delay-and-retry`
- `block-and-alert`

UI behaviour:

- For `allow` → proceed.
- For `require-*` → run challenge flow, then proceed if passed.
- For `delay-and-retry` → inform user and possibly schedule retry.
- For `block-and-alert` → abort, display clear reason.

---

## 6. Transaction Construction (On-Chain Mint)

If Guardian allows:

1. TX Builder prepares a **mint transaction** with:
   - inputs = `selected_utxos`
   - outputs:
     - 1 or more outputs representing **locked backing**:
       - could send to a dedicated “backing script” (implementation detail),
       - or mark as reserved by internal metadata if no custom script used.
     - change output → `change_address`.

2. Wallet signs transaction using appropriate keys.
3. Node / backend broadcasts transaction to the DGB network.

Output:

```ts
MintTxResult {
  txid: string
  raw_tx_hex: string
  broadcast_time: timestamp
}
```

If broadcast fails:
- UI shows error,
- DD position is **not** created,
- UTXOs remain unlocked in model (or re-synced).

---

## 7. DD Position Creation

Once broadcast is accepted (or at least reliably submitted):

```ts
DigiDollarPosition {
  id: string
  created_at: timestamp

  mint_txid: txid
  backing_utxos: [{ txid, vout }, ...]

  dd_amount: dd_amount
  backing_satoshis: total_backing_satoshis

  status: "active"
}
```

Wallet updates:

- `DigiDollarState.total_dd_balance += dd_amount`
- `DigiDollarState.total_backing_satoshis += total_backing_satoshis`
- add `position` to `DigiDollarState.positions`
- mark backing UTXOs as `is_locked = true` in `UtxoSet`.

---

## 8. Confirmation Tracking

QAC and Sentinel are used to track:

- confirmation count for `mint_txid`,
- confirmation quality and timing.

UI states (example):

- **Pending** (0 conf, low confidence)
- **Confirming** (1–2 conf, medium confidence)
- **Secure** (N conf, high QAC confidence)

`status` remains `"active"` but UI can show a visual badge for
“under-confirmation” vs “settled”.

---

## 9. Error & Edge Cases

- **Insufficient funds**:
  - Immediately abort in step 3 (UTXO selection).
- **High-risk environment**:
  - Guardian returns `block-and-alert`.
- **Node / network failure**:
  - TX broadcast fails → show error, do not create DD position.
- **User cancels after Guardian challenge**:
  - Action stops, nothing written to DD state.

All outcomes should log anonymised decision data for Adaptive Core.

---

## 10. Future Enhancements

Possible future additions:

- multi-step mint wizards (educational UX),
- advanced mint modes (e.g. portfolio-based backing),
- partial mint cancellation before broadcast,
- scheduled mints (DCA into DD).
