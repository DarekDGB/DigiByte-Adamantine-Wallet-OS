# Enigmatic Integration Test Suite — Adamantine Wallet

Status: **Draft v0.1 – specification-level test plan**

This document defines all test scenarios required for validating
integration between **Adamantine Wallet** and **Enigmatic Layer‑0
communication**, including encoding, decoding, planning, and safe
broadcasting of state‑vector messages.

---

# 1. Encoder Tests

## 1.1 Encode basic symbol (HEARTBEAT)

**Goal:** Wallet correctly uses Enigmatic encoder.

**Steps:**
1. Load dialect file `dialects/dialect-showcase.yaml`.
2. Request encoding for symbol `HEARTBEAT`.
3. Extract produced state vector.

**Expect:**
- Value plane matches spec.
- Fee plane cadence = correct pattern (0.21 or as defined).
- Output cardinality matches dialect.
- No forbidden OP_RETURN patterns.
- Deterministic output for same inputs.

---

## 1.2 Encode multi‑frame symbol (triptych_21_21_84)

**Goal:** Multi‑frame sequences produce reproducible frame chains.

**Steps:**
1. Load multi‑frame dialect.
2. Encode symbol.
3. Inspect produced frames.

**Expect:**
- Frames follow exact ordering.
- Block‑placement deltas respected.
- No drift across planes.

---

# 2. Decoder Tests

## 2.1 Decode known HEARTBEAT vector

**Goal:** Wallet decodes real Enigmatic traffic.

**Steps:**
1. Supply canonical HEARTBEAT transaction hex.
2. Run decoder.

**Expect:**
- Correct symbol returned.
- All 5 planes decoded.
- Confidence > 0.95.
- No misalignment warnings.

---

## 2.2 Decode ambiguous vector

**Goal:** Wallet handles near‑collisions gracefully.

**Expect:**
- Decoder returns:
  - symbol = null
  - confidence < 0.5
- Wallet UI shows “Unclassified signal”.

---

# 3. Planner Tests

## 3.1 Planner selects correct UTXOs

**Goal:** Avoids dust, forbidden patterns, bad cardinalities.

**Expect:**
- Required UTXOs selected deterministically.
- Change output created exactly as dialect needs.
- Preview vector matches final tx.

---

## 3.2 Dry‑run before broadcast

**Goal:** Wallet never broadcasts without preview.

**Expect:**
- `dry_run = true` always default.
- Guardian sees preview first.
- No tx is broadcast prematurely.

---

# 4. Executor Tests (Broadcast Layer)

## 4.1 Allowed symbol under safe conditions

**Goal:** End‑to‑end send works.

**Expect:**
- Risk engine returns LOW.
- Guardian allows.
- Broadcast txid returned.

---

## 4.2 Blocked under lockdown (ADN or QAC)

**Expect:**
- Executor stops.
- UI shows “Shield Lockdown”.
- No broadcast attempted.

---

# 5. Shield‑Bridge Tests

## 5.1 Pre‑signal check

**Expect:**  
Wallet calls shield‑bridge:
- `/enigmatic/pre_check`
- Returns normal.

## 5.2 Post‑signal hook

**Expect:**  
Shield logs:
- symbol name
- planes
- confidence
- txid

---

# 6. Risk‑Engine Interaction Tests

## 6.1 High sentinel score

**Expect:**
- Risk escalated to MEDIUM/HIGH.
- Guardian requires confirmation.

## 6.2 Conflict between planes (suspicious topology)

**Expect:**
- Risk engine flags `"topology_anomaly"`.
- Wallet pops warning.

---

# 7. UI Integration Tests

## 7.1 Enigmatic inbox

**Expect:**
- Displays decoded signals.
- Shows symbol + confidence + timestamp.
- Works offline (cache of last signals).

## 7.2 Planner preview screen

**Expect:**
- Shows 5 plane structure.
- Shows Guardian risk level.
- User must confirm.

---

# 8. Negative Tests

- Invalid dialect → graceful error.
- Malformed tx hex → decoder error but no crash.
- Planner missing UTXOs → user notified.
- RPC timeout → retry with warning.
- Device offline → offline mode engaged.

---

# 9. Future Automation

- Fuzz tests across value/fee/cardinality space.
- Multi‑symbol chain planning.
- Group signals (future Layer‑0 feature).

---

# License
MIT — Author: DarekDGB
