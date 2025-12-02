# DigiDollar (DD) Redeeming — Flow (redeem-flow.md)

Status: **draft v0.1 – internal skeleton**

This document describes the **end-to-end flow** for redeeming DigiDollar (DD)
back into unlocked DigiByte (DGB) inside the Adamantine Wallet.

Redeem is the **mirror** of mint, but treated as highly sensitive because it
moves locked backing funds and may be targeted by attackers.

---

## 1. Preconditions

- Wallet has loaded `DigiDollarState` for the relevant account.
- There is at least one **active** DD position.
- Node / network connectivity is sufficient to broadcast transactions
  (or user is warned about degraded mode).
- Device is not in a hard-block security state (see thresholds doc).

---

## 2. Redeem Modes

Two UX modes:

1. **Redeem specific position**
   - user chooses an individual `DigiDollarPosition` from history.

2. **Redeem by amount**
   - user enters a DD amount,
   - wallet selects one or more positions to redeem or partially redeem.

Internal representation:

```ts
RedeemIntent {
  account_id: string

  // either:
  position_ids?: string[]
  // or:
  dd_amount?: number

  target_address?: string      // DGB address to receive unlocked funds
}
```

If `target_address` is omitted, wallet uses a default DGB receive address
for the account.

---

## 3. Position & UTXO Resolution

From `RedeemIntent`, wallet resolves:

- which positions are involved,
- which backing UTXOs correspond to those positions.

Output:

```ts
RedeemSelection {
  positions: DigiDollarPosition[]
  total_dd_amount: number
  total_backing_satoshis: number
  backing_utxos: { txid: string; vout: number }[]
  change_address: string
}
```

For partial redeems, the selection logic MAY split positions or create
new positions (implementation detail, to be defined later).

If no valid positions or insufficient DD available:
- UI error: “Not enough DD to redeem this amount.”

---

## 4. Guardian ActionRequest

The wallet builds an `ActionRequest` for Guardian:

```ts
ActionRequest {
  id: string
  timestamp: timestamp

  kind: "redeem-dd"
  profile_id: string
  account_id: account_id

  amount_dd: total_dd_amount
  amount_sats: total_backing_satoshis

  from_address?: string           // optional backing/source hint
  to_address?: string             // target_address if provided

  extras: {
    "position_count": number,
    "backing_utxo_count": number,
    "is_full_redeem": boolean,
    "time_since_last_redeem_s": number
  }

  device_security_state: DeviceSecuritySnapshot
  network_state: NetworkStateSnapshot
}
```

This is passed into the Risk Engine and then Guardian, as described in
`guardian-wallet/spec.md` and `risk-engine/inputs.md`.

---

## 5. Risk & Guardian Verdict

Special attention is given to:

- large redeems after long inactivity,
- redeems to **new, unseen addresses**,
- clusters of rapid redeems,
- shield conditions (ADN lockdown, DQSN unsafe, Sentinel anomalies),
- Adaptive Core escalations targeted at DD.

Guardian verdict options are the same as for mint:

- `allow`
- `require-local-confirmation`
- `require-biometric`
- `require-passphrase`
- `delay-and-retry`
- `block-and-alert`

UI must clearly display when a redeem is blocked due to network or
shield conditions vs user-configured profile.

---

## 6. Transaction Construction (On-Chain Redeem)

If Guardian allows:

1. TX Builder constructs a **redeem transaction** that:
   - spends backing UTXOs from the positions involved,
   - sends unlocked DGB to the `target_address` and/or change address.

2. Wallet signs with appropriate keys (same security as normal sends).

3. TX is broadcast through the connected DGB node.

Output:

```ts
RedeemTxResult {
  txid: string
  raw_tx_hex: string
  broadcast_time: timestamp
}
```

If broadcast fails:
- wallet must **not** mark positions as redeemed,
- user is informed and given option to retry after network recovers.

---

## 7. DD State Update

Once redeem TX is successfully submitted:

- Mark positions as:
  - `"redeeming"` immediately after submission,
  - `"redeemed"` when sufficient confirmations & QAC confidence are reached.

- Update `DigiDollarState`:

  ```text
  total_dd_balance      -= total_dd_amount
  total_backing_satoshis -= total_backing_satoshis
  ```

- Remove or archive fully redeemed positions.

Some implementations may show “Redeeming…” status until QAC reports
healthy confirmations for the redeem TX.

---

## 8. Confirmation & UI

QAC is used to determine when redeemed funds are considered **safe**:

- low confidence or disagreements → UI may show a warning,
- high confidence + sufficient confs → show as “Settled Redeem”.

UI states (example):

- “Redeem pending” (broadcast but 0 confs)
- “Redeem confirming” (1–2 confs)
- “Redeem settled” (N confs + high QAC confidence)

---

## 9. Error & Special Cases

- **Partial broadcast** (rare):
  - node accepts TX but later reports conflict;
  - wallet re-syncs UTXOs and reconciles positions carefully.
- **User cancels during Guardian challenge**:
  - no TX built or broadcast,
  - DD state unaffected.
- **Shield emergency (mid-flow)**:
  - if shield enters emergency state before broadcast,
    wallet may abort and require user to restart flow later.

All redeem flows should log anonymised events for Adaptive Core,
especially blocks and escalations.

---

## 10. Future Enhancements

- Redeeming directly to **cold addresses** with stricter policy.
- Scheduling redeems (e.g. staged exit from DD over time).
- Combining multiple small positions into a single redeem for cleaner UX.
