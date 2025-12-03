# PQC Containers — Design

Status: draft v0.1

This document defines how **post-quantum cryptography (PQC)** is wrapped,
stored, and transported inside the DigiByte Adamantine Wallet without
breaking existing DigiByte consensus or UTXO rules.

The goal is a **container model**, not a hard fork: PQC lives in
wallet-side data structures, metadata and side-channels, while the chain
remains standard DigiByte.

---

## 1. Design Goals

- **Quantum-aware without hard fork**  
  All PQC logic is handled at the wallet / shield layer.

- **Hybrid safety**  
  Allow classic ECDSA + PQC signatures in parallel where possible so
  users are protected even if one algorithm is weakened.

- **Gradual migration**  
  Existing users keep their funds; PQC can be adopted step-by-step.

- **Shield-aware**  
  Sentinel, DQSN, ADN and Adaptive Core can see PQC posture and react.

- **Portable & recoverable**  
  PQC containers can be backed up, restored or moved between devices
  without exposing raw secret material.

---

## 2. Container Types

Adamantine defines three high‑level PQC container classes:

1. **Key containers** – hold PQC keypairs and derivation metadata.  
2. **Signature containers** – wrap PQC signatures attached to wallet
   actions.  
3. **Session containers** – short‑lived envelopes for chats, DD minting,
   guardian approvals and remote shield calls.

All share a common header layout so they can be parsed and scored by the
shield stack.

---

## 3. Common Header Layout

Each container begins with a small typed header:

- `version` – container format version (start at `1`).  
- `type` – `key`, `signature`, or `session`.  
- `algo` – PQC algorithm identifier (e.g. `dilithium3`, `falcon-512`).  
- `kdf_profile` – how secrets are derived from the root seed.  
- `created_at` – timestamp (ISO 8601).  
- `meta` – free‑form JSON for future extensions.

The header is followed by a **payload section** that depends on the
container type.

---

## 4. Key Containers

Represent a **bundle of keys** tied to one DigiByte identity.

Suggested fields:

- `public_key` – PQC public key (base64 / bech32 encoded).  
- `public_fingerprint` – short hash for UI display and verification.  
- `derivation_path` – description of how this key was derived
  (wallet‑local; not written on‑chain).  
- `usage` – allowed usages (e.g. `wallet-sign`, `chat`, `guardian`).  
- `rotation_hint` – suggested rotation interval (e.g. “6 months”).  
- `shield_policy_ref` – link to shield policy that evaluates this key.

Private key material never leaves secure storage; the container only
exposes **handles** to the signing module.

---

## 5. Signature Containers

Signature containers wrap PQC signatures produced by the wallet for a
given action.

Example fields:

- `action_id` – unique identifier of the signed action
  (transaction hash, message id, DD operation id…).  
- `pqc_signature` – raw PQC signature bytes (encoded).  
- `pqc_pubkey_ref` – reference to the key container used.  
- `hybrid_companion` – optional pointer to the classical ECDSA signature
  for the same action.  
- `evidence` – summary of what was signed (hashes only, no PII).

These containers are primarily used by:

- **Guardian Wallet** – to prove user intent.  
- **DQSN / Sentinel** – to confirm that a high‑risk action used PQC.  
- **Adaptive Core** – to learn from signing patterns.

---

## 6. Session Containers

Session containers are short‑lived, encrypted envelopes used by:

- Enigmatic chat sessions  
- DigiDollar mint / redeem flows  
- Guardian rule approvals  
- Remote shield / telemetry calls

Basic structure:

- `session_id` – random identifier.  
- `participants` – public fingerprints of parties / devices.  
- `ephemeral_pqc_key` – one‑time key used for this session only.  
- `cipher_suites` – algorithms used for confidentiality + integrity.  
- `lifetime` – expiry time or block‑height window.  
- `encrypted_payload` – application‑specific payload.

When a session expires, containers may be pruned or archived depending on
the user’s privacy settings.

---

## 7. Storage & Backup

PQC containers are stored in a **wallet‑local keystore**, separate from:

- standard DigiByte addresses, and  
- application settings.

Backup guidance:

- Full backup exports an encrypted bundle of all containers.  
- Lite backup exports only key containers and essential guardian rules.  
- Restore workflows clearly indicate PQC readiness vs legacy‑only mode.

All exports must be encrypted end‑to‑end using a strong KDF anchored in
the user’s seed and device secret.

---

## 8. Interaction with the Shield

PQC containers are first‑class inputs for the **Quantum Shield Network**:

- Sentinel can log PQC usage and drift over time.  
- DQSN can cross‑check PQC posture across multiple nodes.  
- ADN can **block or downgrade** actions that lack PQC when policy
  requires it.  
- Adaptive Core can treat “PQC present” as a strong positive signal,
  feeding long‑term risk scores.

Over time, shield policies can tighten from *“PQC recommended”* to
*“PQC required for high‑risk flows”* without changing the container
format.

---

## 9. Open Questions / Future Work

- Final algorithm choice after NIST and DigiByte core guidance.  
- Hardware‑backed keys on secure elements where available.  
- Cross‑device PQC sync while preserving deniability.  
- Interop with other PQC‑aware DigiByte wallets.

For now, this design gives Adamantine a clear, extensible PQC envelope
that can evolve as the crypto landscape changes.
