# DigiByte Adamantine Wallet — DigiDollar Minting Test Plan

This document defines a **manual + automated test plan** for the
`modules/dd-minting` component of the DigiByte Adamantine Wallet.

The goal is to validate that DigiDollar (DD) minting, redeeming and
risk‑gated flows behave exactly as specified in the module docs, and
that all transactions remain:

- economically sane (no dust, no free mints)
- ledger‑consistent (1 DD ≈ 1 USD–backed reserve unit)
- shield‑aware (respecting Guardian Wallet + Quantum Wallet Guard
  decisions)
- observable and auditable for operators

---

## 1. Scope

These tests cover:

1. **Mint flows**
   - single‑user mint
   - repeated mints
   - high‑value mints
2. **Redeem flows**
   - full redeem
   - partial redeem
3. **Oracle + peg guards**
   - stale price feeds
   - conflicting feeds
   - extreme volatility
4. **Risk engine integration**
   - score calculation
   - thresholds and blocking
5. **Shield bridge behaviour**
   - Sentinel / DQSN / ADN / QAC hooks firing
   - escalations on critical risk

Out of scope (covered by other suites):

- generic wallet send / receive
- core Guardian Wallet behaviour
- generic node / network health (Sentinel AI v2 tests)

---

## 2. Test Environments

### 2.1 Local devnet / regtest

- **Chain**: DigiByte regtest / devnet
- **Nodes**: at least two DGB nodes
- **Wallet**: Adamantine reference wallet with DD module enabled
- **Oracle**: local mock oracle service exposing deterministic prices
- **Shield**: test endpoints for Sentinel, DQSN, ADN, QAC, Adaptive Core

Used for **fast iteration** and CI.

### 2.2 Staging (testnet)

- DigiByte testnet node(s)
- Deployed Adamantine staging wallet
- Staging oracle infrastructure
- Standard monitoring via Sentinel AI v2

Used for **pre‑production sign‑off**.

---

## 3. Test Data

### 3.1 Accounts / wallets

- `W_USER_A` — normal user
- `W_USER_B` — second user (peer testing)
- `W_OPERATOR` — treasury / reserve operator

### 3.2 Example values

- Small mints: 10, 25, 50 DD
- Medium mints: 100, 250, 500 DD
- Large mints: 1 000, 5 000 DD

Use round values to ease reconciliation.

---

## 4. Mint Flow Tests

### 4.1 Happy‑path mint

**Goal:** A user can mint DD when all pre‑conditions are healthy.

1. Ensure oracle is healthy and returns a fresh price.
2. Ensure Shield risk score for `W_USER_A` is **Low**.
3. From `W_USER_A`, run *Mint 100 DD*.
4. Confirm risk‑engine pre‑check passes.
5. Broadcast mint transaction.

**Expected:**

- Transaction confirmed on DigiByte.
- `W_USER_A` DD balance increases by 100.
- Treasury / reserve state reflects equivalent backing.
- Shield logs a **mint_ok** event with correlation ID.

---

### 4.2 Repeated mints

**Goal:** Multiple sequential mints remain consistent.

1. From `W_USER_A`, mint 3 × 50 DD in a row.
2. Wait for confirmation of each transaction.

**Expected:**

- Final DD balance increased by 150.
- No rounding drifts beyond configured tolerance.
- No duplicate correlation IDs.
- Shield logs three separate mint events.

---

### 4.3 Large‑value mint (limit test)

**Goal:** Test configured maximum per‑mint amount.

1. Configure max mint per transaction (e.g. 5 000 DD).
2. Attempt to mint **4 999 DD**.

**Expected:** Succeeds, tagged as **High** value but allowed.

3. Attempt to mint **5 001 DD**.

**Expected:**

- Risk engine returns **Blocked – value limit**.
- No transaction is broadcast.
- UI shows clear error message.

---

### 4.4 Insufficient backing / treasury check

**Goal:** Prevent mints if the reserve is under‑collateralised.

1. Simulate reserve level below required threshold.
2. From `W_USER_A`, attempt to mint 100 DD.

**Expected:**

- Mint blocked with **Reserve low** status.
- Shield receives a **mint_blocked_reserve_low** signal.
- Operator dashboard shows an alert.

---

## 5. Redeem Flow Tests

### 5.1 Full redeem

**Goal:** A user can redeem all DD back to base currency / DGB channel.

1. Ensure `W_USER_A` holds 100 DD.
2. Trigger *Redeem 100 DD*.
3. Confirm redemption transaction(s).

**Expected:**

- DD balance becomes 0.
- Corresponding backing assets released to the user (off‑chain or on‑chain, per design).
- Shield logs **redeem_ok** with correlation ID.

### 5.2 Partial redeem

**Goal:** Partial redemption works and state stays consistent.

1. `W_USER_A` holds 300 DD.
2. Redeem 120 DD.

**Expected:**

- Balance becomes 180 DD.
- Reserve state decreased by equivalent amount.
- No dust DD outputs created unless explicitly allowed.

### 5.3 Redeem under risk / investigation

**Goal:** Redemptions may be blocked or delayed for flagged wallets.

1. Mark `W_USER_A` as **Under review** in the risk engine (or simulate high risk).
2. Attempt to redeem 50 DD.

**Expected:**

- Redeem operation blocked or routed to **manual review** path.
- End‑user sees “Redeem pending / under review” message.
- Shield emits **redeem_flagged** event for operators.

---

## 6. Oracle & Peg Guard Tests

### 6.1 Stale oracle data

**Goal:** Block minting when price feeds are stale.

1. Configure oracle to serve a price older than the allowed staleness window.
2. Attempt to mint 50 DD.

**Expected:**

- Risk engine sets state to **OracleStale**.
- Mint request rejected with user‑friendly explanation.
- Sentinel records an **oracle_stale** anomaly for DD.

### 6.2 Conflicting oracle providers

**Goal:** Detect disagreement between multiple price sources.

1. Provide two oracle feeds with > X% divergence.
2. Attempt to mint 50 DD.

**Expected:**

- System enters **Conflict** mode for the peg.
- Mint blocked until operator resolves discrepancy.
- Shield records **oracle_conflict** with underlying feed details
  (hashes or IDs, not raw prices).

### 6.3 Extreme volatility band

**Goal:** Apply extra guardrails during large price swings.

1. Simulate a rapid price movement beyond configured volatility band.
2. Attempt mints of 10 DD and 1 000 DD.

**Expected:**

- Small mint may pass with warning flag.
- Large mint either blocked or requires explicit operator override.
- Events logged for post‑mortem analysis.

---

## 7. Risk Engine Integration

### 7.1 Score calculation sanity

**Goal:** Ensure risk scores map correctly to decisions.

1. Feed synthetic profiles to the risk engine:
   - Low risk user
   - Medium risk user
   - High risk user
2. Trigger mint and redeem flows for each profile.

**Expected:**

- Low: flows allowed.
- Medium: may require extra checks (2FA, delays).
- High: flows blocked and flagged.

### 7.2 Guardian thresholds

**Goal:** Configurable thresholds behave as defined in
`core/risk-engine/guardian-thresholds.md`.

1. Adjust `Low/Med/High/Critical` bands.
2. Re‑run mint attempts around boundaries.

**Expected:**

- Behaviour changes exactly at boundary values.
- No “flapping” (rapid allow/block) for jittery scores.

---

## 8. Shield Bridge Behaviour

### 8.1 Event hook firing

**Goal:** DD module correctly calls shield‑bridge APIs.

1. Enable debug logging on shield‑bridge.
2. Run a textbook mint and redeem.

**Expected:**

- `pre_mint_check`, `post_mint_record` called.
- `pre_redeem_check`, `post_redeem_record` called.
- Payloads include anonymised but traceable identifiers.

### 8.2 Critical risk escalation

**Goal:** Critical events bubble up to Adaptive Core.

1. Force a **Critical** risk score (e.g. known compromised wallet).
2. Attempt to mint or redeem.

**Expected:**

- Operation blocked.
- Adaptive Core records a **dd_flow_blocked_critical** signal.
- Downstream policies (e.g. wallet lockdown) may trigger per global config.

---

## 9. Negative & Edge Cases

- Mint value **below minimum** (dust) → blocked.
- Redeem causing DD dust remainder → either rounded or disallowed.
- Network outage to oracle → graceful degradation and clear errors.
- Shield bridge offline → conservative fail‑closed behaviour where possible.
- Double‑click / repeated UI submissions → deduplicated by correlation ID.

---

## 10. Automation Notes

- Each scenario above should map to one or more automated tests in
  `tests/dd_minting` (Python / JS / Kotlin, per implementation).
- CI should run the **regtest suite** on every commit affecting:
  - `modules/dd-minting`
  - `core/risk-engine`
  - `core/shield-bridge`
- Staging (testnet) runs can be scheduled nightly with slimmed‑down
  coverage to control costs.

When this test plan is stable, mark coverage progress directly in this
file or in the project tracker (e.g. “✓ automated”, “✓ manual”, “todo”).
