# EQC — Execution / Eligibility / Equivalence Quality Control

EQC is the **decision brain** of **Adamantine Wallet OS**.

It evaluates an immutable execution context and returns a **deterministic verdict**
that gates *all* sensitive actions inside the Wallet OS.

---

## Core invariant

> **EQC decides. WSQK executes.**

No signing, no key material, no mint/redeem authority, and no privileged operation
may be reached unless EQC returns `ALLOW`.

This invariant is enforced by architecture *and* by CI tests.

---

## What EQC does

EQC is deliberately narrow and strict.

It:

- Defines a canonical, immutable `EQCContext`
- Produces a stable `context_hash()` for:
  - audit logs
  - replay protection
  - downstream binding (WSQK scopes)
- Runs deterministic classifiers to extract **signals**
- Applies an explicit policy ruleset
- Returns a `Verdict`:
  - `ALLOW`
  - `DENY`
  - `STEP_UP` (additional verification required)

EQC is **side‑effect free**, **deterministic**, and **fully testable**.

---

## What EQC does NOT do

EQC intentionally does **not**:

- Generate cryptographic keys
- Sign transactions
- Handle seed phrases
- Perform network calls
- Store persistent state
- Execute actions

EQC observes and decides only.

---

## Context model

EQC decisions are based exclusively on an immutable snapshot:

- Action context (send / mint / redeem / sign, asset, amount, recipient)
- Device context (type, trust, OS, first‑seen)
- Network context (network, fee rate, peers)
- User context (biometric availability, PIN)
- Timestamp + extra metadata

No hidden globals. No ambient state.

---

## Classifiers

Classifiers extract **facts**, not opinions.

They:

- Are deterministic
- Have no side effects
- Never return verdicts
- Never enforce thresholds

Examples of signals:

- device trust / novelty
- browser or extension environment
- transaction shape
- asset type

Policy decides how signals are interpreted.

---

## Policy engine

Policies:

- Are evaluated in order
- Produce the first terminal verdict
- Separate:
  - hard blocks
  - step‑up requirements
  - default allows

### Non‑negotiable rules (v1)

- Browser context → `DENY`
- Extension context → `DENY`
- Mint / Redeem → `STEP_UP`

These are enforced by CI and must never be weakened silently.

---

## Public API

Recommended imports:

```python
from core.eqc import (
    EQCEngine,
    EQCContext,
    VerdictType,
)
```

Single entrypoint:

```python
decision = EQCEngine().decide(context)

if decision.verdict.type == VerdictType.ALLOW:
    # WSQK may be invoked
```

---

## Relationship to WSQK

EQC **never** calls WSQK directly.

EQC produces:
- a verdict
- a context hash
- a structured signal bundle

WSQK may only be invoked by a runtime orchestrator **after**
EQC returns `ALLOW`.

This separation is intentional and permanent.

---

## Design philosophy

EQC is not an AI black box.

It is:
- explicit
- inspectable
- auditable
- predictable

Security comes from **architecture**, not from trust.

---

**Author:** DarekDGB  
**License:** MIT
