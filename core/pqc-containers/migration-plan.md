# PQC Containers — Migration Plan

Status: draft v0.1

This document explains **how existing Adamantine Wallet users migrate**
from classical‑only keys to the new PQC container model without a hard
fork or loss of funds.

The plan is intentionally gradual and shield‑driven.

---

## 1. Phases Overview

1. **Phase 0 – Observation only**  
   PQC containers exist but are optional; shield only observes.

2. **Phase 1 – Opt‑in PQC**  
   Users can generate PQC containers and start hybrid signing.

3. **Phase 2 – Recommended for high‑risk actions**  
   Shield begins to **warn** when PQC is missing on sensitive flows.

4. **Phase 3 – Policy‑enforced PQC**  
   Guardian rules and ADN can **block or require extra approval** if
   PQC is missing for configured operations.

5. **Phase 4 – Ecosystem standardisation**  
   Other DigiByte wallets can adopt the same container layout so users
   can move with minimal friction.

---

## 2. Phase 0 — Observation Only

- Wallet ships with PQC container support **disabled by default**.  
- Sentinel & Adaptive Core include placeholders for PQC metrics.  
- No keys are generated and no UI is exposed yet.  
- This phase is mainly for internal testing on testnet / devnet.

Success criteria:

- No regressions in classical wallet behaviour.  
- Shield telemetry remains stable.

---

## 3. Phase 1 — Opt‑in PQC

New “Security → Quantum readiness” screen:

- Explains PQC benefits and current status (experimental / optional).  
- Lets the user generate PQC key containers for:
  - wallet signing
  - Enigmatic chat
  - DigiDollar mint / redeem
  - Guardian approvals

Migration steps per user:

1. User enables PQC in settings.  
2. Wallet derives PQC keys from the existing seed (new paths).  
3. Key containers are created and stored in the PQC keystore.  
4. Shield policies switch from “unknown” to “PQC available”.

All classical behaviour continues to work; signatures become **hybrid**
where the flow supports it.

---

## 4. Phase 2 — Recommended for High‑Risk Actions

Shield policy update:

- High‑value transactions, DD redemptions, guardian rule edits and
  device‑binding operations are marked as **high‑risk**.  
- If a high‑risk action is initiated **without PQC**, the wallet:
  - shows a clear warning, and  
  - logs the event for Adaptive Core.

Users can still proceed, but they are gently pushed towards enabling
PQC if they have not already done so.

---

## 5. Phase 3 — Policy‑Enforced PQC

Once PQC usage proves stable in the field, operators / power users may
opt into stronger rules:

Examples:

- “Block any outgoing transaction above X DGB unless PQC is present.”  
- “Require PQC for all DigiDollar mint / redeem operations.”  
- “Require PQC for new device pairing or guardian rule changes.”

Enforcement points:

- Guardian Wallet – prompts for additional confirmation or denies.  
- ADN – can automatically quarantine / defer actions that violate
  policy.  
- DQSN – can flag nodes that consistently ignore PQC policy.

These rules are **per‑wallet configuration**, not network hard forks.

---

## 6. Phase 4 — Ecosystem Standardisation

After the container model matures:

- Reference documentation for PQC containers is published in the
  Adamantine docs (and eventually DigiByte dev portal).  
- Other wallet developers can implement compatible containers so:
  - backups can be imported/exported, and  
  - shield‑aware behaviours remain consistent across clients.

Long‑term, this enables a **PQC‑aware DigiByte ecosystem** without a
mandatory signature‑scheme fork.

---

## 7. Rollback & Safety Nets

If anything goes wrong during rollout:

- Users can temporarily **disable PQC signing** while keeping their
  classical wallet intact.  
- PQC containers can be marked as “revoked” without touching on‑chain
  UTXOs.  
- Shield policies can fall back to “recommendation only” mode.

At every step, funds remain under the user’s classical keys; PQC adds
a **second layer of protection**, never a single point of failure.

---

This migration plan lets Adamantine grow from today’s reality into a
quantum‑aware future **one safe step at a time**, guided by shield
telemetry and real‑world usage data.
