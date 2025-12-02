# Risk Engine — Guardian Thresholds (guardian-thresholds.md)

Status: **draft v0.1 – internal skeleton**

This document explains how **Risk Engine outputs** are mapped into
**Guardian thresholds** and how certain hard limits are enforced.

It bridges:

- `RiskAssessment` (score + level)
- `guardian-wallet/configs.md` (profiles & actions)
- **hard-coded safety invariants** that cannot be disabled.

---

## 1. Conceptual Flow

```text
RiskInput
   ↓
Risk Engine → RiskAssessment { level, score }
   ↓
Guardian Profile Config (YAML)
   ↓
GuardianAction (allow / challenge / block)
   ↓
UI + TX Builder behaviour
```

This file focuses on:

- special cases where RiskLevel alone is not enough,
- minimum actions for certain conditions,
- emergency overrides.

---

## 2. Threshold Helpers

Guardian may use helper functions like:

```ts
function isLargeAmount(amount_sats: number, profile: ProfileGuardianConfig): boolean
function isHugeAmount(amount_sats: number, profile: ProfileGuardianConfig): boolean
```

These use either:

- fixed bucket thresholds, or
- user-defined thresholds per profile.

Example (conceptual):

```text
large = > 100 DGB
huge  = > 10,000 DGB
```

Exact values are implementation details but must be clearly documented
in developer docs / UI help.

---

## 3. Hard Safety Invariants

Regardless of profile settings:

1. If **contact is flagged as known scam**:
   - RiskEngine MUST set `level = "critical"`.
   - Guardian MUST choose an action equivalent to `"block-and-alert"`.

2. If **ADN mode = "lockdown"** and its scope includes:
   - `"no-large-broadcasts"`
   - `"no-dd-operations"`

   then Guardian MUST:
   - block affected actions for the duration of lockdown,
   - or force user-visible explicit override flows (if ever allowed).

3. If **device is known-compromised** (`has_known_exploit = true`):
   - Guardian MUST refuse to:
     - perform DD operations,
     - approve huge DGB sends,
   - until the user migrates keys or the state changes.

4. If **Adaptive Core signals emergency escalation** for a scope:
   - Guardian MAY temporarily override user preferences to stricter
     actions (never looser), as long as:
     - decisions are logged,
     - user can see this state in diagnostics,
     - escalations are time-bounded.

---

## 4. Example Mapping Rules

### 4.1 Normal Conditions

Under normal network + device conditions, Guardian simply applies:

```text
(RiskLevel, ActionKind) → GuardianAction
```

using the mapping tables from `risk-profiles.yml`.

### 4.2 Elevated Network Risk

If Sentinel anomaly level = high OR DQSN status = unsafe:

- RiskEngine likely outputs `high` or `critical`.
- Even if the numeric score is borderline, Guardian SHOULD:
  - treat as at least `high` for large or huge amounts,
  - avoid auto-downgrading to `medium` based on contact trust alone.

### 4.3 DD-Specific Tightening

For `mint-dd` and `redeem-dd`:

- if Adaptive overlay flags abnormal DD patterns, then:
  - large mints / redeems should be escalated to at least `high` risk,
  - GuardianAction should be at least `"require-passphrase"`,
  - for some profiles, `"block-and-alert"`.

---

## 5. Offline Mode Thresholds

When **all shield components** are offline:

- RiskEngine returns `level = "unknown"`.
- Guardian profiles decide behaviour:

Example policy (Safe Default):

```text
- tiny / small amounts:
    allow or require-local-confirmation
- medium amounts:
    require-local-confirmation or biometric
- large / huge amounts:
    require-passphrase or block
```

The key principle:

> When blind, do not treat the world as perfectly safe.

Guardian MUST never assume `"low"` risk purely due to lack of data.

---

## 6. Diagnostics & Transparency

For each decision, the combination of:

- RiskAssessment
- selected GuardianAction
- profile used
- shield status snapshot

SHOULD be visible (in simplified form) in a diagnostics view so that:

- advanced users can understand “why”,
- developers can debug thresholds,
- auditors can reason about safety behaviour.

Logging MUST respect the privacy constraints laid out in the telemetry
and analytics documents.
