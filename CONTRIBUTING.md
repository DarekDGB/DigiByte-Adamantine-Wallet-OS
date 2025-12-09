# Contributing to DigiByte Adamantine Wallet

**Adamantine Wallet** is not a traditional wallet.  
It is a **full DigiByte Wallet OS**, architected as a modular, multi-client, multi-layer system integrating:

- DigiAssets v3  
- DigiDollar minting  
- Q-ID (PQC identity)  
- Enigmatic Layer-0 messenger  
- Guardian Wallet user-protection layer  
- Quantum Wallet Guard (QWG)  
- Shield Bridge (Sentinel, DQSN, ADN, Adaptive Core)  
- Node & DigiMobile integration  
- iOS, Android, and Web client code  
- Wallet engine, UTXO logic, parsing, builders, risk engine

This repository contains critical architecture for DigiByte’s long-term upgrade path.  
Because of this, **contributions must be extremely disciplined**.

---

## ✅ What Contributions ARE Welcome

### ✔️ 1. Client Improvements (Android / iOS / Web)
- better UI documentation  
- safer flows for send/receive  
- structure improvements  
- performance optimizations  
- non-breaking architectural enhancements  

### ✔️ 2. Wallet Engine & UTXO Logic
- improvements to `balance.py`, `utxo_manager.py`, `wallet_state.py`  
- safer transaction builders  
- fee estimator refinements  
- extended test coverage  

### ✔️ 3. DigiAssets v3 & DigiDollar
- parser enhancements  
- metadata validation  
- safe minting logic  
- better state management  

### ✔️ 4. Shield Integration
- expansions to `shield_bridge`  
- safer node-health interpretation  
- runtime guard improvements  
- hardened risk-response routing  

### ✔️ 5. Guardian Wallet & QWG Bridges
- clearer advice messages  
- improved rule mappings  
- UX-safe escalation logic  

### ✔️ 6. Documentation
- architecture diagrams  
- step-by-step flows  
- clarification of module responsibilities  
- test examples  

### ✔️ 7. Test Suite Expansion
- new wallet engine tests  
- node manager simulations  
- DigiAssets edge-case tests  
- shield bridge integration tests  
- regression prevention  

---

## ❌ What Will NOT Be Accepted

### 🚫 1. Any Attempt to Remove or Rewrite Core Architecture
The modular layout and each folder’s purpose is **non-negotiable**:

```
clients/  
core/  
modules/  
docs/  
config/  
tests/  
```

No flattening, merging, or repurposing without architectural approval.

---

### 🚫 2. Mixing Layers or Responsibilities  
**Examples of forbidden changes:**

- putting UI logic inside the wallet engine  
- placing shield logic inside client code  
- embedding Guardian or QWG logic into network modules  
- moving DigiAssets parsing into unrelated modules  

Adamantine follows strict separation principles.

---

### 🚫 3. Consensus or Node Logic
Adamantine Wallet:

- does **NOT** modify consensus  
- does **NOT** act as a validator  
- does **NOT** influence node rules  

Any PR trying to do this is rejected instantly.

---

### 🚫 4. Replacing Explainable Logic With Black-Box AI
Adamantine uses **deterministic, auditable logic**.

No neural networks.  
No black-box ML.  
No opaque scoring systems.

---

### 🚫 5. Breaking Cross-Client Behaviour
Android, iOS, and Web must stay aligned.

Any change that breaks parity is rejected.

---

### 🚫 6. Removing Safety Layers
The following must never be weakened:

- Guardian Wallet  
- QWG  
- Shield Bridge  
- Risk Engine  
- Node Health Logic  

These are mandatory components.

---

## 🧱 Design Principles

1. **Security First** — Adamantine protects users by default.  
2. **Modularity** — every function belongs in the correct module.  
3. **Cross-Client Consistency** — behaviour must match across Android/iOS/Web.  
4. **Explainability** — every defence decision must be understandable.  
5. **Determinism** — same inputs → same outputs.  
6. **Upgrade-Safe** — DigiAssets v3, Q-ID, PQC, DigiDollar must remain future-proof.  
7. **Interoperability** — integrates cleanly with Sentinel, DQSN, ADN, QWG, Guardian, Adaptive Core.  

---

## 🔄 Pull Request Requirements

Every PR **must include**:

- a clear description  
- the motivation for the change  
- documentation updates if needed  
- passing test suite (`tests/`)  
- verification that no client behaviour breaks  
- confirmation that no safety or shield logic is removed  

Architect (@DarekDGB) approves **direction**.  
Developers approve **technical correctness**.

---

## 🧪 Testing Expectations

Contributors must:

- add tests for any new module  
- never reduce test coverage  
- test wallet flows end-to-end when changed  
- test shield integration when relevant  

CI must stay green.

---

## 📝 License

By contributing, you agree your work is licensed under the MIT License.

© 2025 **DarekDGB**
