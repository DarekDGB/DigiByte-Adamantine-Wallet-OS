# 📊 Guardian Wallet — Scoring Rules
Status: **draft v0.2 – aligned with Adamantine v0.2**

This document explains **how Guardian converts raw signals into a single
`guardian_risk_score` and `guardian_risk_level`.**

Numbers are reference values; operators may tune them in future versions.

---

## 1. Score Range & Levels

- Score range: **0.0 – 1.0**
- Levels:

  | Level    | Range          | Default Behaviour             |
  |----------|----------------|-------------------------------|
  | low      | 0.00 – 0.24    | allow                         |
  | medium   | 0.25 – 0.49    | warn / maybe 2FA              |
  | high     | 0.50 – 0.74    | require_second_factor / limit |
  | critical | 0.75 – 1.00    | block / lockdown candidate    |

---

## 2. Source Layers & Base Scores

Each Shield layer returns a **0.0–1.0 sub‑score** plus textual signals.

```text
S_sentinel, S_dqsn, S_adn, S_qwg, S_adaptive ∈ [0, 1]
```

Aggregated score:

```text
guardian_risk_score =
  W_sentinel * S_sentinel +
  W_dqsn     * S_dqsn     +
  W_adn      * S_adn      +
  W_qwg      * S_qwg      +
  W_adaptive * S_adaptive
```

Weights come from `guardian-config.yml`.

---

## 3. Example Heuristics per Layer

### 3.1 Sentinel AI v2 (Network / Telemetry)

- normal mempool, no reorg alerts → `S_sentinel = 0.05`
- elevated reorg activity or chain instability → `0.40`
- active attack pattern detected (e.g. large spam flood) → `0.70+`

### 3.2 DQSN v2 (Distributed Confirmation)

- majority of nodes healthy, no conflicting views → `0.05`
- mixed opinions on recent blocks / forks → `0.40`
- strong fork / eclipse / split indicators → `0.80+`

### 3.3 ADN v2 (Node‑Level Reflex)

- node fully synced, good peers, no local anomalies → `0.05`
- partial sync, abnormal resource use, peer churn → `0.40`
- node in self‑lockdown, suspected compromise → `0.90`

### 3.4 QWG (Quantum Wallet Guard)

- keys PQC‑wrapped, no export, device clean → `0.05`
- some keys in legacy form or exported → `0.40`
- high suspicion of key leakage / device compromise → `0.85`

### 3.5 Adaptive Core (Immune Memory)

- behaviour matches long‑term profile → `0.05`
- unusual timing / destination / size patterns → `0.40`
- strong anomaly vs. user profile (e.g. draining entire wallet at 3AM from new device) → `0.90`

---

## 4. Policy Mapping

Guardian uses the aggregated score + policy rules to decide:

```text
if score < 0.25 → verdict = allow
if 0.25 ≤ score < 0.50 → verdict = warn / maybe 2FA
if 0.50 ≤ score < 0.75 → verdict = require_second_factor
if score ≥ 0.75 → verdict = block (and maybe trigger lockdown)
```

Overrides based on **absolute conditions** (regardless of score):

- if node in `hard_lockdown` → always `block`
- if transaction exceeds hard maximum → always `block`
- if Shield Network issues **critical remote override** → `block`

---

## 5. Human‑Readable Reasons

Every decision should provide a short explanation, e.g.:

- `"network instability detected via Sentinel / DQSN"`
- `"new device and unusual destination pattern"`
- `"keys not yet upgraded to PQC; large transfer blocked"`

These reasons are derived from:

- which per‑layer scores crossed thresholds
- any triggered policy rules (limits, 2FA, lockdown)

---

## 6. Tuning & Future Work

- expose weight & threshold tuning via operator console
- allow different profiles: **conservative / balanced / aggressive**
- feed real‑world incident data back into Adaptive Core to improve
  heuristics over time
