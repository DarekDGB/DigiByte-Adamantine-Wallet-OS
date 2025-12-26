# WSQK — Wallet-Scoped Quantum Key

WSQK (Wallet-Scoped Quantum Key) is the **execution key model** of **Adamantine Wallet OS**.

It defines how cryptographic keys are derived, scoped, bound, and destroyed **after**
EQC (Equilibrium Confirmation) has approved an action.

---

## Core invariant

> **EQC decides. WSQK executes.**

WSQK must never be reachable unless EQC returns `ALLOW`.

This rule is enforced by architecture and will be enforced by the runtime orchestrator.

---

## What WSQK is

WSQK is **not** a single static key.

It is a **key derivation and execution model** where keys are:

- Scoped to a wallet and action
- Bound to an EQC-approved context
- Short-lived (ephemeral)
- Non-exportable
- Non-reusable across contexts
- PQC-ready (quantum-safe containers)

---

## What WSQK does

WSQK:

- Derives cryptographic keys only after EQC approval
- Binds keys to:
  - `context_hash`
  - action type
  - scope and policy constraints
- Wraps keys inside PQC-capable containers
- Executes approved signing or authorization actions
- Destroys key material after use

---

## What WSQK does NOT do

WSQK intentionally does **not**:

- Make decisions
- Evaluate risk or policy
- Accept browser or extension contexts
- Store long-term private keys
- Expose seed phrases
- Operate independently of EQC

WSQK executes only what EQC authorizes.

---

## Scoping model

A WSQK is valid only within a defined scope:

- Wallet scope
- Action scope (send, mint, redeem, sign)
- Context scope (EQC context hash)
- Time scope (session / TTL)

If any scope boundary is violated, the key is invalid.

---

## Quantum readiness

WSQK is designed for a post-quantum world:

- Key material may be wrapped using PQC algorithms
- Containers are algorithm-agnostic
- Execution does not assume classical elliptic curves
- Migration does not require architectural change

---

## Relationship to EQC

EQC produces:

- a verdict
- a context hash
- a signal bundle

WSQK consumes only:

- `VerdictType.ALLOW`
- `context_hash`
- explicit execution scope

WSQK never feeds information back into EQC.

---

## Design philosophy

WSQK replaces the concept of a permanent wallet key with **contextual authority**.

Security comes from:
- scope
- context
- policy
- architecture

Not from blind trust in a static secret.

---

**Author:** DarekDGB  
**License:** MIT
