# Risk Engine Test Plan — DigiByte Adamantine Wallet

Status: **Draft v0.1 – specification-level test plan (no code yet)**  
Location: `tests/risk-engine-tests.md`

This document defines the **test strategy and concrete scenarios** for the Adamantine
**Risk Engine**, which scores every transaction / action as:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

based on inputs defined in:

- `core/risk-engine/scoring-rules.md`
- `core/risk-engine/inputs.md`
- `core/risk-engine/guardian-thresholds.md`

The goal of this file is to give implementers and auditors a **clear,
reproducible test matrix** before any production code is written.

---

## 1. Scope

These tests cover:

1. **Risk score calculation** from a structured `RiskContext` input.
2. **Threshold mapping** from numeric score → discrete level (`LOW…CRITICAL`).
3. **Guardian mode decisions** (allow / warn / block / require-multi-step).
4. **Integration with Shield Bridge** signals (Sentinel, DQSN, ADN, QAC, Adaptive Core).
5. **Edge cases** (missing data, stale feeds, conflicting signals).
6. **Determinism & idempotence** (same inputs → same outputs).

Out of scope (for this test file):

- UI rendering of warnings.  
- Wallet persistence details.  
- Chain reorg handling (covered by Shield / ADN tests).

---

## 2. Test Data Model

All tests assume a canonical, serialisable structure (pseudo‑schema):

```yaml
RiskContext:
  tx:
    type: "send" | "receive" | "mint_dd" | "redeem_dd" | "internal"
    amount_dgb: float
    fee_dgb: float
    direction: "outgoing" | "incoming"
    to_address: string
    from_address: string
    change_addresses: [string]
    is_multisig: bool
    is_timelocked: bool
  wallet:
    age_days: int
    tx_count_total: int
    known_contacts: [string]
    device_trust: "unknown" | "normal" | "hardened"
  shield_signals:
    sentinel_score: int      # 0–100 anomaly severity
    dqsn_alerts: [string]    # e.g. ["fork_risk", "latency_spike"]
    adn_lockdown: bool
    qac_mode: "normal" | "heightened" | "lockdown"
    adaptive_confidence: float   # 0.0–1.0
  external_feeds:
    dgb_usd_price: float | null
    dd_peg_deviation: float | null  # % off 1.00 for DigiDollar flows
    oracle_status: "healthy" | "degraded" | "offline"
```

Expected engine output:

```yaml
RiskResult:
  score: int          # 0–100
  level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  guardian_action: "ALLOW" | "WARN" | "BLOCK" | "REQUIRE_CONFIRMATION"
  reasons: [string]
```

All test cases below define **inputs** and **expected outputs** in this shape.

---

## 3. Threshold & Mapping Tests

These tests validate that **numeric scores** are mapped correctly to levels and
guardian actions as defined in `guardian-thresholds.md`.

> NOTE: Exact numeric ranges are placeholders until finalised in the thresholds spec.

### 3.1 LOW risk boundary

- **ID:** `RISK-THRESH-LOW-001`  
- **Given:** `score = 19`  
- **Expect:**  
  - `level = "LOW"`  
  - `guardian_action = "ALLOW"`  
  - `reasons` includes `"score_below_medium_threshold"`  

### 3.2 MEDIUM risk lower bound

- **ID:** `RISK-THRESH-MED-001`  
- **Given:** `score = 20`  
- **Expect:**  
  - `level = "MEDIUM"`  
  - `guardian_action = "WARN"`  
  - `reasons` includes `"medium_threshold_reached"`  

### 3.3 MEDIUM → HIGH boundary

- **ID:** `RISK-THRESH-HIGH-001`  
- **Given:** `score = 50`  
- **Expect:**  
  - `level = "HIGH"`  
  - `guardian_action = "WARN"` or `"REQUIRE_CONFIRMATION"` (as per thresholds spec)  

### 3.4 HIGH → CRITICAL boundary

- **ID:** `RISK-THRESH-CRIT-001`  
- **Given:** `score = 80`  
- **Expect:**  
  - `level = "CRITICAL"`  
  - `guardian_action = "BLOCK"`  
  - `reasons` includes `"critical_threshold_reached"`  

### 3.5 Determinism test

- **ID:** `RISK-THRESH-DET-001`  
- **Given:** Same `RiskContext` evaluated N times.  
- **Expect:** Same `score`, `level`, `guardian_action` for all runs.

Implementation hint: add a unit test that samples the range of scores (0–100)
and ensures mapping is **pure and side‑effect free**.

---

## 4. Core Scenario Tests

### 4.1 Normal everyday outgoing payment

- **ID:** `RISK-SCEN-NORMAL-001`  
- **Context:**  
  - Long‑lived wallet (`age_days > 365`, many historical txs).  
  - Recipient is in `known_contacts`.  
  - Amount is small relative to wallet balance.  
  - No active alerts from Shield layers.  
- **Expect:**  
  - `score` in LOW band (e.g. `< 20`).  
  - `level = "LOW"`.  
  - `guardian_action = "ALLOW"`.  
  - `reasons` list includes `"known_contact"` and `"no_active_alerts"`.

### 4.2 New address, unusually large send

- **ID:** `RISK-SCEN-LARGE-SEND-001`  
- **Context:**  
  - Wallet ageing: `age_days > 180`.  
  - `amount_dgb` exceeds configurable large‑tx threshold.  
  - `to_address` **not** in `known_contacts`.  
  - No Shield alerts.  
- **Expect:**  
  - Elevated `score` (MEDIUM or HIGH, depending on thresholds).  
  - At least `guardian_action = "WARN"`.  
  - `reasons` includes `"unknown_recipient"` and `"large_amount"`.  

### 4.3 Sudden behaviour change after long dormancy

- **ID:** `RISK-SCEN-DORMANT-001`  
- **Context:**  
  - Wallet had `tx_count_total` very low for months, then suddenly initiates a large send.  
  - Shield may also report mild anomaly from Sentinel.  
- **Expect:**  
  - `score` in HIGH band.  
  - `guardian_action = "REQUIRE_CONFIRMATION"` or `"BLOCK"` if combined with other risk factors.  
  - Reasons clearly flag `"behaviour_shift"` and `"dormant_wallet"`.  

### 4.4 Incoming funds from high‑risk cluster

- **ID:** `RISK-SCEN-INCOMING-HIGHCLUSTER-001`  
- **Context:**  
  - `direction = "incoming"`.  
  - Shield / external intelligence tags sender cluster as high‑risk.  
- **Expect:**  
  - `score` at least MEDIUM.  
  - UI will still allow receive, but engine must mark the UTXO as **tainted / flagged**.  
  - `guardian_action` for the *incoming tx* = `ALLOW`, but internal flags are set for downstream spends.

### 4.5 DigiDollar mint under stable conditions

- **ID:** `RISK-SCEN-DD-MINT-STABLE-001`  
- **Context:**  
  - `tx.type = "mint_dd"`.  
  - Oracles healthy, `dd_peg_deviation < 1%`.  
  - No alerts from Shield.  
- **Expect:**  
  - `level = "LOW"` or `MEDIUM` at most.  
  - `guardian_action = "ALLOW"`.  

### 4.6 DigiDollar mint when peg is unstable

- **ID:** `RISK-SCEN-DD-MINT-UNSTABLE-001`  
- **Context:**  
  - `tx.type = "mint_dd"`.  
  - `dd_peg_deviation > 5–10%` OR `oracle_status = "degraded" | "offline"`.  
  - Shield may raise `sentinel_score` due to oracle drift.  
- **Expect:**  
  - `score` bumped into HIGH / CRITICAL depending on policy.  
  - `guardian_action = "BLOCK"` or `"REQUIRE_CONFIRMATION"`.  
  - Clear reason like `"dd_oracle_unstable"` in `reasons`.

---

## 5. Shield‑Signal Integration Tests

These tests validate how the Risk Engine **reacts** when Shield layers send
specific patterns of alerts.

### 5.1 Sentinel anomaly but no ADN lockdown

- **ID:** `RISK-SHIELD-SENT-001`  
- **Inputs:**  
  - `shield_signals.sentinel_score >= 70`.  
  - `adn_lockdown = false`.  
- **Expect:**  
  - Risk `score` receives additive boost (configurable).  
  - At least `level = "MEDIUM"`.  
  - `reasons` includes `"sentinel_anomaly"`.

### 5.2 ADN lockdown engaged

- **ID:** `RISK-SHIELD-ADN-LOCK-001`  
- **Inputs:**  
  - `adn_lockdown = true`.  
  - Any outgoing tx attempt.  
- **Expect:**  
  - `level = "CRITICAL"`.  
  - `guardian_action = "BLOCK"`.  
  - Reason `"adn_lockdown_active"`.

### 5.3 QAC heightened mode

- **ID:** `RISK-SHIELD-QAC-001`  
- **Inputs:**  
  - `qac_mode = "heightened"`.  
  - Normal looking payment.  
- **Expect:**  
  - Slight increase in `score` but not automatic block.  
  - Guardian action may move from `ALLOW` → `WARN` for borderline txs.

### 5.4 QAC full lockdown

- **ID:** `RISK-SHIELD-QAC-LOCK-001`  
- **Inputs:**  
  - `qac_mode = "lockdown"`.  
  - Any outgoing tx.  
- **Expect:**  
  - `level = "CRITICAL"`.  
  - `guardian_action = "BLOCK"`.  
  - Reason `"qac_lockdown"`.

### 5.5 Adaptive Core low confidence

- **ID:** `RISK-SHIELD-ADAPTIVE-001`  
- **Inputs:**  
  - `adaptive_confidence < 0.3`.  
  - No explicit external anomaly.  
- **Expect:**  
  - Risk score nudged into MEDIUM.  
  - Engine must treat low confidence as **"we know less than usual"**, not a false sense of safety.

---

## 6. Edge Case & Failure‑Mode Tests

### 6.1 Missing oracle data

- **ID:** `RISK-EDGE-ORACLE-MISSING-001`  
- **Inputs:**  
  - `dgb_usd_price = null`, `dd_peg_deviation = null`, `oracle_status = "offline"`.  
  - User tries DigiDollar mint or redeem.  
- **Expect:**  
  - `guardian_action != "ALLOW"` (WARN or BLOCK depending on policy).  
  - Reasons include `"oracle_data_missing"`.

### 6.2 Conflicting signals from Shield

- **ID:** `RISK-EDGE-CONFLICT-001`  
- **Inputs:**  
  - Sentinel score low, but DQSN reports `"fork_risk"`.  
- **Expect:**  
  - Engine chooses **conservative** interpretation (elevate risk).  
  - Deterministic resolution order documented in `reasons` (e.g. `"dqsn_fork_risk_overrides_low_sentinel"`).

### 6.3 Extreme amount but internal transfer

- **ID:** `RISK-EDGE-INTERNAL-HUGE-001`  
- **Inputs:**  
  - Very large `amount_dgb`.  
  - All outputs still owned by the same wallet (internal re‑sharding).  
- **Expect:**  
  - Engine recognises internal transfer and does **not** push into CRITICAL.  
  - Possibly MEDIUM with reason `"internal_consolidation"`.

### 6.4 Corrupted / invalid context

- **ID:** `RISK-EDGE-INVALID-CONTEXT-001`  
- **Inputs:**  
  - Missing required fields or nonsensical values (negative amounts, etc.).  
- **Expect:**  
  - Engine returns a controlled error state or refuses to score.  
  - No crash, no undefined behaviour.

---

## 7. Regression & Fuzz Tests (Future)

When the implementation exists, add:

- **Fuzz tests** that feed randomised `RiskContext` values within bounds to ensure:
  - No crashes.
  - Scores stay within [0, 100].
- **Regression suite** for previously discovered bugs, each with:
  - Original failing context.
  - Expected corrected `RiskResult`.

---

## 8. How to Use this File

1. For each `ID:` scenario above, create a concrete JSON/YAML fixture in the
   future `tests/fixtures/risk-engine/` directory.
2. Implement unit tests (language TBD: Rust/TypeScript/etc.) that:
   - Load the fixture.
   - Call the Risk Engine.
   - Assert that `score`, `level`, `guardian_action`, and key `reasons`
     match this specification.
3. Keep this file as the **human‑readable truth** and update it whenever
   scoring rules or thresholds change.

Adamantine’s philosophy: **“No magic”** — every guardian decision must be
**auditable back to a scenario here**.
