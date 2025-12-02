# Risk Engine — Scoring Rules (scoring-rules.md)

Status: **draft v0.1 – internal skeleton**

This document describes the **risk scoring logic** used by the
Adamantine Risk Engine before Guardian Wallet applies policy.

Risk Engine:

- ingests signals from Shield Bridge (Sentinel, DQSN, ADN, QAC, Adaptive Core)
- ingests local signals (device state, contact trust, amount, patterns)
- produces a single **RiskLevel** + **numeric score** per action.

Guardian then maps `(RiskLevel → GuardianAction)` based on profiles.

---

## 1. Outputs

Risk Engine exposes two core outputs:

```ts
type RiskLevel = "unknown" | "low" | "medium" | "high" | "critical"

RiskAssessment {
  level: RiskLevel
  score: number               // 0.0 – 1.0, where 1.0 = maximum risk
  contributing_factors: string[]
  shield_status_snapshot: ShieldStatusSnapshot
}
```

`ShieldStatusSnapshot` is a compact snapshot of Sentinel/DQSN/ADN/QAC
health used for diagnostics and logging.

---

## 2. Input Categories

Risk Engine groups inputs into categories to avoid over-weighting
any single source:

1. **Network & Chain Health**
   - Sentinel summary (reorg risk, mempool state, anomaly level)
   - DQSN node health & fork suspicion
   - ADN mode & lockdown state

2. **Confirmation Quality**
   - QAC confidence level
   - disagreement scores
   - timing anomalies

3. **Action Context**
   - amount bucket (e.g. tiny / small / medium / large / huge)
   - asset type (DGB vs DD)
   - frequency (rapid repeats)

4. **Counterparty & Address Reputation**
   - contact trust level
   - contact risk flags (exchange / scam / internal wallet)
   - address reputation hints (from Sentinel, local history)

5. **Device & App Security**
   - OS trust level (jailbroken / rooted / outdated)
   - app integrity status
   - presence of secure enclave / biometrics

6. **Adaptive Overlays**
   - Adaptive Core policy hints
   - context risk overlays

Each category contributes a partial score in `[0.0, 1.0]`.

---

## 3. Scoring Bands

Final numeric score is mapped to RiskLevel using bands:

```text
0.00 – 0.15  →  low
0.15 – 0.40  →  medium
0.40 – 0.75  →  high
0.75 – 1.00  →  critical
```

`unknown` is used when **insufficient data** is available or when
all shield components are offline.

Bands may be adjusted in future, but must remain monotonic.

---

## 4. Example Heuristics

### 4.1 Network & Chain Health

- Sentinel `anomaly.level = "high"` → +0.25
- Sentinel `network.reorg_risk = "high"` → +0.25
- DQSN `recommendation.status = "unsafe"` → +0.30
- ADN `mode = "lockdown"` → force at least `high` (score ≥ 0.6)

### 4.2 Confirmation Quality

For **outgoing** TXs:

- low QAC confidence on **previous related TXs** → +0.1 to +0.2

For **incoming** TXs (not strictly Guardian but for UI safety):

- `confidence.level = "low"` → treat as untrusted / pending
- `disagreement.has_disagreement = true` → raise score to ≥ 0.4

### 4.3 Amount & Frequency

Define amount buckets (example, in DGB-equivalent):

```text
tiny   < 0.01 DGB
small  0.01 – 1 DGB
medium 1 – 100 DGB
large  100 – 10,000 DGB
huge   > 10,000 DGB
```

Example contributions:

- `tiny` or `small` → +0.0
- `medium` → +0.05
- `large`  → +0.15
- `huge`   → +0.25

Rapid repeats:

- N large sends within short window → extra +0.1 to +0.2

### 4.4 Counterparty & Reputation

- Contact `trust_level = "high"` → -0.05 (cap at minimum score 0.0)
- Contact `trust_level = "low"` → +0.1
- Contact `trust_level = "blocked"` or `is_known_scam = true` →
  - force score ≥ 0.75 (critical)

- Address flagged as suspicious by Sentinel → +0.2

### 4.5 Device & App Security

- Device is jailbroken/rooted with known exploit → +0.3
- OS severely outdated → +0.1 to +0.2
- App integrity check failed → force at least `high`

### 4.6 Adaptive Overlays

- Adaptive Core `risk_overlay_level = "medium"` → +0.1
- Adaptive Core `risk_overlay_level = "high"` → +0.2
- Adaptive Core emergency escalation for scope `"mint-dd"` →
  - for that action, force score ≥ 0.75

---

## 5. Missing Data & Degraded Modes

When some inputs are missing:

- **Sentinel offline**:
  - treat network anomaly as `unknown` instead of `low`.
  - do **not** assume chain is fine; leave more weight to DQSN / ADN.

- **DQSN offline**:
  - reduce confidence in node health,
  - avoid classifying environment as fully safe.

- **ADN offline**:
  - remove local node reflex hints,
  - rely more on Sentinel + DQSN.

If **all shield components** are offline:

- produce `RiskLevel = "unknown"`,
- numeric score based primarily on:
  - amount, device security, contact reputation,
  - local heuristics.

Guardian profiles decide how `"unknown"` is treated (see configs).

---

## 6. Tuning & Test Vectors

Exact numeric weights are:

- implementation details,
- expected to evolve over time,
- MUST be accompanied by regression tests.

`tests/risk-engine-tests.md` will define a set of fixtures like:

```json
{
  "name": "large send to known scam contact with healthy network",
  "input": { ... },
  "expected_risk_level": "critical"
}
```

This ensures Risk Engine changes remain auditable and predictable.
