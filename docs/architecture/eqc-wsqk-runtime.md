# Adamantine Wallet OS — EQC · WSQK · Runtime Architecture

This document describes the **core security architecture** of Adamantine Wallet OS.

It defines how **decisions**, **authority**, and **execution** are separated and
enforced by design.

This is an **OS-level model**, not a browser wallet model.

---

## Core Principle

> **EQC decides. WSQK executes. Runtime enforces.**

No cryptographic operation, signing action, mint, or authorization may occur
unless this flow is satisfied.

This rule is enforced in **code**, **tests**, and **architecture**.

---

## High-Level Flow

```
[ Request ]
     |
     v
[ EQC — Equilibrium Confirmation ]
     |
     |  (VerdictType.ALLOW only)
     v
[ WSQK — Wallet-Scoped Quantum Key ]
     |
     |  (Scoped · Context-bound · Single-use)
     v
[ Runtime Orchestrator ]
     |
     v
[ Execution ]
```

There is **no bypass path**.

---

## EQC — Equilibrium Confirmation

EQC is the **decision brain** of Adamantine Wallet OS.

It:
- evaluates an immutable execution context
- runs deterministic classifiers
- applies explicit policy rules
- returns a deterministic verdict:
  - `ALLOW`
  - `DENY`
  - `STEP_UP`

EQC:
- has no side effects
- does not sign
- does not generate keys
- does not execute actions

EQC produces:
- a verdict
- a `context_hash`
- a signal bundle

---

## WSQK — Wallet-Scoped Quantum Key

WSQK is the **execution authority model**.

WSQK is **not** a static private key.

Instead, WSQK authority is:

- scoped to a wallet
- scoped to a specific action
- bound to an EQC-approved `context_hash`
- time-limited (TTL)
- single-use (nonce enforced)
- non-reusable across contexts

WSQK cannot exist unless EQC has already returned `ALLOW`.

---

## WSQK Guard (Single-Use Authority)

WSQK execution is protected by:

- scope validation
- session TTL
- one-time nonce consumption (replay protection)

Once a WSQK execution succeeds:
- the nonce is consumed
- replay is impossible by construction

This turns authority into **one-time permission**, not a reusable secret.

---

## Runtime Orchestrator

The runtime orchestrator is the **enforcement layer**.

It guarantees:
- EQC is always evaluated first
- WSQK cannot be reached without EQC approval
- execution is blocked otherwise

Even internal developers cannot “accidentally” bypass EQC or WSQK.

---

## Why Browser Wallets Cannot Enforce This

Browser wallets and extensions:

- run inside hostile execution environments
- rely on long-lived keys or seeds
- cannot enforce OS-level invariants
- cannot prevent bypass by design

Adamantine Wallet OS enforces security **architecturally**, not by convention.

---

## Crypto Is an Implementation Detail

Cryptography (including PQC) is intentionally **not hardcoded** here.

Instead:
- crypto is injected behind stable interfaces
- architecture remains unchanged
- contributors can implement:
  - classical signing
  - PQC KEM wrapping
  - hardware enclave backends

This allows development **without heavy toolchains**, including mobile-only workflows.

---

## Design Philosophy

Security does not come from:
- trust
- reputation
- extensions
- static secrets

Security comes from:
- separation of concerns
- explicit authority
- context binding
- enforced execution flow

Adamantine Wallet OS is built as a **security operating system**, not a wallet app.

---

**Author:** DarekDGB  
**License:** MIT
