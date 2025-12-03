# DigiAssets — Transaction Rules

Status: draft v0.1

This document defines **wallet-side validation rules** for DigiAssets
transactions (issue, transfer, burn, reissue) in the Adamantine Wallet.

These rules sit on top of standard DigiByte validation and integrate
with QWG, Guardian, and the risk-engine.

---

## 1. Common Rules

Before sending any DigiAssets TX:

- all involved UTXOs must be fully synced in local index  
- resulting asset balances must not go negative  
- DGB funding must satisfy fee and dust limits  
- PQC container validation must PASS (QWG)  
- risk-engine decision must be PASS or WARN (never BLOCK)  

If any check fails → the wallet blocks TX creation or submission.

---

## 2. Issue TX Rules

- must include a valid DigiAssets envelope with `ISSUE` operation  
- issuer must control the funding address keys  
- amount encoded in envelope must match resulting asset UTXOs  
- supply must obey the chosen supply model (see `minting-rules.md`)  

Optional: Guardian may require multi-step approval for public issuance.

---

## 3. Transfer TX Rules

- asset inputs selected must belong to the sending account  
- total output asset amount ≤ sum of input assets for the same `asset_id`  
- change asset outputs (if any) must return to wallet-controlled scripts  
- cross-asset mixing is not allowed inside a single logical transfer
  unless explicitly supported by the protocol

Risk-engine may enforce:

- address whitelists / blacklists  
- per-TX and per-day volume caps  

---

## 4. Burn TX Rules

- burn amount must be explicitly flagged in the envelope  
- burned quantity is removed from `wallet_balances` and, where tracked,
  from `assets` supply statistics  
- when `burn_guardian_required = true`, Guardian approval is mandatory  

Wallet UI must show irreversible consequences clearly before signing.

---

## 5. Reissue TX Rules

For `capped` or `reissuable` assets:

- issuer must match original issuer (same controlling keys)  
- new total supply must respect cap for `capped` model  
- reissue operation must be allowed by asset policy flags  

Reissue TXs are typically high risk and should be strongly guarded by:

- Guardian multi-approval  
- high risk thresholds in the risk-engine  
- optional time-lock windows

---

## 6. Mempool & Pending State

While a DigiAssets TX is unconfirmed:

- balances use `pending_delta` to show “incoming / outgoing” states  
- a TX replaced via RBF or chain reorg must roll back those deltas  
- final state is only committed after block confirmation

---

## 7. UX Signals

The wallet surfaces rule outcomes as:

- **Green**: all checks pass, low risk  
- **Amber**: WARN from risk-engine or Guardian, user must confirm  
- **Red**: BLOCK – TX cannot be sent from this wallet configuration  

This keeps DigiAssets operations transparent and safe for end users.
