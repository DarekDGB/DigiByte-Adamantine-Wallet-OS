# Adamantine Wallet — Architecture Overview

Status: **draft v0.2**

This document provides a high-level map of the Adamantine Wallet architecture, covering its modules, core systems, security layers, data flows, and platform implementations.

---

## 1. Architectural Goals

Adamantine Wallet is designed to be:

- **DigiByte‑native** – first‑class support for DGB, DigiAssets, and DigiDollar (DD).
- **Security‑first** – deeply integrated with the 5‑layer DigiByte Quantum Shield + Adaptive Core.
- **Multi‑platform** – consistent UX and safety guarantees across **Android**, **iOS**, and **Web**.
- **Modular & auditable** – every major concern (keys, assets, messaging, analytics) lives in its own module with clear, documented boundaries.
- **Future‑proof** – ready for Taproot, Enigmatic Layer‑0 communication, and post‑quantum upgrades.

This file is the “map of the city” – other docs go into street‑level detail.

---

## 2. High‑Level Layering

From top (user) to bottom (chain), Adamantine is organised into these layers:

1. **Client Apps (UI layer)**
   - `clients/android/`
   - `clients/ios/`
   - `clients/web/`
   - Responsible for screens, navigation, and local device capabilities (biometrics, secure storage integration, notifications).

2. **Wallet Core**
   - Key management, account abstraction, UTXO management, transaction building, and fee policies.
   - Responsible for both **DGB** and **DigiAssets/DigiDollar** aware transaction flows.
   - Exposes a stable API to all clients.

3. **Security & Guard Rails**
   - **Guardian Wallet module** – local policy engine that turns shield risk scores into concrete user flows (warnings, extra confirmations, hard blocks).
   - **Shield Bridge** – API glue that connects the wallet to the DigiByte Quantum Shield stack:
     - Sentinel AI v2
     - DigiByte Quantum Shield Network (DQSN)
     - Autonomous Defense Node v2 (ADN v2)
     - Quantum Adaptive Core (QAC)
     - DigiByte Quantum Adaptive Core (DQAC – immune system).
   - Supports both _online_ (live signals from the network) and _offline_ (last known profiles, local heuristics) modes.

4. **Assets & Value Layer**
   - **DigiByte (DGB)** – base UTXO handling.
   - **DigiAssets** – token & NFT functionality, creation, issuance, and transfer flows.
   - **DigiDollar (DD)** – stable‑value asset with:
     - mint / redeem flows,
     - oracle & risk hooks,
     - integration with shield telemetry for anomaly detection.

5. **Layer‑0 Messaging (Enigmatic)**
   - Integration with **Enigmatic** as the DigiByte Layer‑0 communication stack.
   - Uses DigiByte’s UTXO/fee/topology space as a signalling channel for:
     - wallet‑to‑wallet intents,
     - shield signals,
     - DigiDollar governance and telemetry messages.
   - Implemented as a dedicated **Enigmatic Chat & Messaging** module with clear APIs into Wallet Core.

6. **Analytics & Telemetry**
   - `modules/analytics-telemetry/`
   - Collects **privacy‑respecting** metrics:
     - shield risk events,
     - anonymised error telemetry,
     - performance and UX signals.
   - All analytics are opt‑in and shaped by the `privacy-model.md`.

7. **Persistence & Configuration**
   - Local device storage (secure hardware, encrypted databases, keychains).
   - Remote configuration for:
     - shield endpoints,
     - oracle sources,
     - feature flags and rollout stages.

8. **External Dependencies**
   - DigiByte full nodes / light clients.
   - Quantum Shield infrastructure (nodes, APIs, telemetry buses).
   - Oracles, price feeds, and regulatory / compliance endpoints (where applicable).

---

## 3. Module Map

At a coarse level, the repository is organised as:

- **`.github/`** – CI, linting, docs checks, and issue templates.
- **`clients/`**
  - `android/` – Android‑specific README and UI screen maps.
  - `ios/` – iOS‑specific README and UI screen maps.
  - `web/` – Web client README and UI screen maps.
- **`core/`**
  - `data-models/` – contact, message, and wallet‑state models shared across clients.
  - `guardian-wallet/` – configs, flows, and spec for the local safety engine.
  - `pqc-containers/` – post‑quantum aware key and signing containers (design + migration plan).
  - `qwg/` – Quantum Wallet Guard hooks (event hooks, validation rules, and spec).
  - `risk-engine/` – scoring rules, inputs, and guardian thresholds.
  - `shield-bridge/` – wallet‑side API surface for all shield layers (adaptive core, ADN, DQSN, QAC, Sentinel).
- **`modules/`**
  - `analytics-telemetry/` – privacy model + analytics spec.
  - `dd-minting/` – DigiDollar mint, redeem, and oracle integration specs.
  - `enigmatic-chat/` – Enigmatic‑powered chat, message flow, and abuse controls.
  - `digiassets/` – DigiAsset & NFT lifecycle flows (creation, issuance, transfer, burn) – **new module**.
- **`docs/`**
  - High‑level documents such as this architecture overview, the risk model, shield integration, DigiDollar overview, Enigmatic overview, roadmap, and vision.
- **`tests/`**
  - Scenario‑driven test descriptions for risk engine, DD minting, Enigmatic, shield bridge, and more.

Each of these directories has its own README/spec file to explain internals.

---

## 4. Key Data Flows

This section sketches how the major flows move through the architecture.

### 4.1 Standard DGB Send

1. User initiates a send from any client (Android/iOS/Web).
2. Client calls **Wallet Core** to:
   - select UTXOs,
   - estimate fees,
   - build a candidate transaction.
3. Wallet Core calls **Shield Bridge** with a transaction draft.
4. Shield Bridge:
   - queries Sentinel / DQSN / ADN risk surfaces,
   - assembles a **risk profile** for this action.
5. Guardian Wallet applies user policy:
   - low risk → proceed with normal biometric / PIN.
   - elevated risk → show warnings, require extra confirmation.
   - extreme risk → block, suggest remediation.
6. If user approves, Wallet Core signs and broadcasts via DigiByte node / light client.
7. Analytics‑Telemetry logs anonymised, policy‑safe events (if enabled).

### 4.2 DigiAsset Creation & Transfer

1. User opens **DigiAssets** module screen.
2. Client calls Wallet Core + DigiAssets module:
   - choose base UTXOs,
   - define asset parameters (name, supply, metadata),
   - construct asset‑aware transactions.
3. Shield Bridge + Guardian evaluate for:
   - unusual issuance patterns,
   - spam / abuse heuristics,
   - policy/compliance constraints (where applicable).
4. Upon approval, transactions are signed and broadcast.
5. Enigmatic can optionally embed **Layer‑0 messages** announcing the new asset to subscribed watchers.

### 4.3 DigiDollar Mint / Redeem

1. User initiates **mint** (DGB → DD) or **redeem** (DD → DGB).
2. DigiDollar module orchestrates:
   - on‑chain transaction building,
   - oracle checks,
   - shield risk checks,
   - off‑chain service calls if required by the DD design.
3. Risk Engine and Shield Bridge ensure that:
   - oracle anomalies,
   - sudden pattern shifts,
   - regulatory rules are all respected.
4. Successful flows update wallet balances; failures surface clear, user‑friendly errors.

### 4.4 Enigmatic Messaging

1. User sends a secure message / intent via **Enigmatic Chat**.
2. Wallet Core encodes the intent as an **Enigmatic dialect symbol**.
3. Enigmatic stack plans UTXOs, state vectors, and transaction shapes.
4. Shield Bridge and Guardian confirm that the pattern is:
   - policy‑compliant,
   - economically plausible,
   - within detectability / deniability bounds.
5. Transaction is signed/broadcast; receivers decode via the same dialect.

---

## 5. Security & Trust Model (High Level)

- **Device security** – leverage secure enclaves, keychains, and OS‑level hardening.
- **Shield‑aligned** – every critical flow can consult:
  - Sentinel AI telemetry,
  - DQSN confirmation patterns,
  - ADN lockdown signals,
  - QAC / DQAC adaptive responses.
- **Policy‑driven UX** – Guardian Wallet is the “face” of all this to the user:
  - configuration profiles (conservative / balanced / aggressive),
  - per‑asset and per‑amount thresholds,
  - travel / jurisdiction modes for future releases.
- **Privacy‑aware analytics** – analytics‑telemetry is explicitly opt‑in and documented in `privacy-model.md`.

---

## 6. Deployment & Platform Notes

- **Android / iOS**
  - Native shells with shared business logic where possible.
  - Platform‑specific secure storage and biometric handling.
  - Offline‑capable for basic operations with cached shield profiles.

- **Web**
  - Browser‑based UI with optional integration into existing DigiByte web wallets or extensions.
  - Hardened against XSS / CSRF via standard best practices.

- **Backend / Services**
  - Adamantine is primarily **non‑custodial**.
  - Optional companion services:
    - notification relays,
    - analytics aggregators,
    - shield proxy endpoints for resource‑constrained clients.

---

## 7. Roadmap Hooks

This architecture is intentionally modular so that future work can plug in cleanly:

- Full implementation of **post‑quantum signing** via `pqc-containers/`.
- Rich **DigiAsset gallery and marketplace views**.
- More sophisticated **guardian policies** (per‑contact trust levels, travel modes).
- Expanded **Enigmatic dialects** for governance, shield telemetry, and community channels.
- Advanced **multi‑sig / social recovery** schemes aligned with PQC containers and shield policies.

---

*This file is a living document. As the Adamantine Wallet moves from design to implementation, this overview will be kept in sync with the actual repository structure and deployed features.*
