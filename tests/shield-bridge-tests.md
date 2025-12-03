# Shield Bridge Test Suite — DigiByte Adamantine Wallet

Status: **Draft v0.1 – spec-level test plan**

`Shield Bridge` is the narrow, auditable interface between the Adamantine
Wallet and external defence layers:

- Sentinel AI v2
- DigiByte Quantum Shield Network (DQSNet)
- ADN v2
- DigiByte Quantum Adaptive Core (QAC)
- Adaptive Core overlays / analytics

This document defines tests that ensure:

- correct request/response wiring,
- conservative failure behaviour,
- clear propagation of risk signals,
- and no accidental data leakage.

---

## 1. Scope

These tests cover:

1. API request/response shapes.
2. Timeouts, errors, and degraded modes.
3. Interaction with:
   - Risk Engine
   - Guardian Wallet
   - QWG policies
4. Logging and observability behaviour.

Out of scope:

- Internal correctness of Sentinel / DQSN / ADN / QAC – each has its own suite.
- Node-level behaviour under deep reorgs (covered elsewhere).

---

## 2. Conceptual API Overview

High-level conceptual endpoints (implementation-agnostic):

```ts
interface ShieldBridge {
  // For outgoing actions (send, mint, redeem, Layer-0 signals)
  preActionCheck(input: PreActionContext): PreActionResult

  // For finalised actions (after broadcast / commit)
  postActionRecord(input: PostActionContext): void

  // For periodic status snapshots
  fetchShieldStatus(): ShieldStatusSnapshot
}
```

Tests in this file assume serialisable JSON/YAML shapes defined in
`core/shield-bridge/*.md`.

---

## 3. Pre-Action Check Tests

### 3.1 Happy-path low risk

**ID:** `SB-PRE-LOW-001`  
**Context:**

- Action: normal DGB send
- Shield layers report:
  - Sentinel: low anomaly
  - DQSN: no fork risk
  - ADN: no lockdown
  - QAC: normal mode

**Expect:**

- `preActionCheck` returns:
  - `risk_overlay = "none"`
  - `recommendation = "allow"`
- Risk Engine can safely keep or lower its base score.
- No warnings attached.

---

### 3.2 Sentinel anomaly, but no lockdown

**ID:** `SB-PRE-SENT-ANOM-001`  
**Context:**

- Sentinel returns anomaly score ≥ configured threshold.
- Other layers normal.

**Expect:**

- `risk_overlay = "elevated"`
- `sentinel_reason` present in metadata.
- Guardian shifts from ALLOW → WARN for borderline risk scores.

---

### 3.3 DQSN fork risk

**ID:** `SB-PRE-DQSN-FORK-001`  
**Context:**

- DQSN flags `"fork_risk"` or `"deep_reorg_risk"`.
- Action: high-value send.

**Expect:**

- `risk_overlay = "critical_chain_risk"`
- `recommendation = "delay"` or `"block"`.
- Wallet surfaces a clear message: "Network instability detected."

---

### 3.4 ADN lockdown

**ID:** `SB-PRE-ADN-LOCK-001`  
**Context:**

- ADN in lockdown mode.

**Expect:**

- All outgoing actions:
  - `recommendation = "block"`
  - `lockdown_flag = true`
- Guardian converts into `BLOCK` regardless of base Risk Engine score.

---

### 3.5 QAC heightened or lockdown modes

**ID:** `SB-PRE-QAC-MODES-001`  
**Context:**

- `qac_mode = "heightened"` or `"lockdown"`.

**Expect:**

- In `heightened`:
  - `risk_overlay = "heightened"`
  - Multi-sig / guardian confirmation may be required.
- In `lockdown`:
  - Equivalent to ADN lockdown for outgoing actions:
    - `recommendation = "block"`.

---

### 3.6 ShieldBridge partial failure (one service down)

**ID:** `SB-PRE-PARTIAL-FAIL-001`  
**Context:**

- Sentinel reachable, DQSN reachable, ADN times out.

**Expect:**

- `ShieldStatusSnapshot` marks ADN as `status = "unreachable"`.
- `preActionCheck` returns **conservative** overlay (e.g. elevated or block, per policy).
- Clear `reasons` include `"adn_unreachable"`.

---

### 3.7 Full failure (ShieldBridge cannot contact any service)

**ID:** `SB-PRE-FULL-FAIL-001`  
**Context:**

- All requests time out or fail.

**Expect:**

- `risk_overlay` must **never** misleadingly report `"none"`.
- Implementation policy:
  - Either:
    - Block all high-risk or high-value actions, or
    - Require explicit override + warning for anything non-trivial.
- Diagnostics log clearly: `"shield_bridge_unreachable"`.

---

## 4. Post-Action Record Tests

### 4.1 Standard record after broadcast

**ID:** `SB-POST-RECORD-001`  
**Context:**

- A DGB send or DD mint action successfully confirmed on-chain.

**Expect:**

- `postActionRecord` is called with:
  - txid
  - action_type
  - basic attributes (amount, recipient classification, etc.)
- No sensitive data (passphrases, secrets, local device identifiers).

---

### 4.2 Failure to record

**ID:** `SB-POST-FAIL-001`  
**Context:**

- `postActionRecord` endpoint fails (timeout or error).

**Expect:**

- Wallet must **not** retry infinitely.
- Local action state is not rolled back (user tx is still valid).
- An internal flag marks shield logs as incomplete.
- Optional: a background retry queue with exponential backoff.

---

### 4.3 Layer-0 Enigmatic signals

**ID:** `SB-POST-L0-001`  
**Context:**

- Enigmatic Layer-0 symbol broadcast via Adamantine.

**Expect:**

- `postActionRecord` includes:
  - symbol or label
  - digest of state vector (not raw planes, for privacy)
- Shield can correlate patterns for Adaptive Core, without reconstructing full state planes if not necessary.

---

## 5. Shield Status Snapshot Tests

### 5.1 Healthy snapshot

**ID:** `SB-STATUS-HEALTHY-001`  
**Context:**

- All external layers reachable and responsive.

**Expect:**

- `ShieldStatusSnapshot`:
  - sentinel.status = "healthy"
  - dqsn.status = "healthy"
  - adn.status = "healthy"
  - qac.mode = "normal"
- Client UI shows green/OK status.

---

### 5.2 Mixed status snapshot

**ID:** `SB-STATUS-MIXED-001`  
**Context:**

- Sentinel = degraded
- DQSN = healthy
- ADN = healthy
- QAC = heightened

**Expect:**

- Snapshot returns:
  - sentinel.status = "degraded"
  - qac.mode = "heightened"
- Risk engine gets this and adjusts scores.
- UI shield panel reflects mixed status (not just a single boolean).

---

### 5.3 Stale status data

**ID:** `SB-STATUS-STALE-001`  
**Context:**

- No fresh status update for > configured TTL.

**Expect:**

- Snapshot marks:
  - `is_stale = true`
- Risk engine treats stale data as **unknown**, not safe.
- UI may show "Last updated X minutes ago" warning.

---

## 6. Privacy & Data-Minimisation Tests

### 6.1 No wallet addresses leaked unnecessarily

**ID:** `SB-PRIV-ADDR-001`  
**Context:**

- Pre-action check for normal send.

**Expect:**

- Bridge receives:
  - class of recipient (known / unknown / contact / internal)
  - approximate bucketed amount (small/medium/large)
- It does **not** receive the actual address or full amount by default, unless explicitly specified in the protocol for a justified case.

---

### 6.2 No device identifiers

**ID:** `SB-PRIV-DEVICE-001`  
**Context:**

- Any ShieldBridge call.

**Expect:**

- No IMEI, serial numbers, or unique device fingerprint.
- Only anonymous or bucketed client metadata where absolutely needed.

---

### 6.3 Telemetry opt-out respected

**ID:** `SB-PRIV-TELEMETRY-001`  
**Context:**

- User opts out of all optional telemetry in Settings.

**Expect:**

- ShieldBridge only sends **minimal operational data** strictly required for security decisions.
- No extended analytics or behavioural metrics.

---

## 7. Integration with Risk Engine & Guardian

### 7.1 Risk overlay propagation

**ID:** `SB-INTEG-RISK-001`  
**Context:**

- ShieldBridge returns `risk_overlay = "heightened"`.

**Expect:**

- Risk Engine incorporates overlay → score bumps.
- Guardian shifts from ALLOW → WARN for borderline txs.
- Decision can be traced in logs.

---

### 7.2 Critical overlay leads to block

**ID:** `SB-INTEG-RISK-CRIT-001`  
**Context:**

- ShieldBridge returns `risk_overlay = "critical_chain_risk"`.

**Expect:**

- Guardian returns `BLOCK` for any outgoing action.
- UI shows reason referencing chain risk.

---

### 7.3 No overlay during normal operation

**ID:** `SB-INTEG-RISK-NONE-001`  
**Context:**

- ShieldBridge responds with `"none"` overlay.

**Expect:**

- Risk Engine proceeds with its usual local scoring.
- Guardian decisions are based on local context only.

---

## 8. Negative & Fault Injection Tests

- Malformed JSON from external service → graceful error and conservative mode.
- Extremely high latency → timeout and conservative decision.
- Unexpected new fields in response → ignored or logged, not crash.
- Version mismatch between ShieldBridge and external services → flagged, but no undefined behaviour.

---

## 9. Automation Notes

- Map each scenario `ID:` to fixtures in `tests/fixtures/shield-bridge/`.
- Implement mock services for Sentinel / DQSN / ADN / QAC in CI.
- Run the suite anytime:
  - bridge code changes,
  - risk/guardian thresholds change,
  - shield protocol versions are bumped.

---

MIT License — Author: **DarekDGB**

