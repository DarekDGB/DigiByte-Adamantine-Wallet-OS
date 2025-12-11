# 🔷 DigiByte Adamantine Wallet  
### *Quantum-Secure Wallet OS • Shield-Integrated • Multi-Client Architecture*  
**Architecture by @DarekDGB — MIT Licensed**

---

# 🌌 Overview

**DigiByte Adamantine Wallet** is not a traditional cryptocurrency wallet.  
It is a **full Wallet Operating System (Wallet-OS)** designed to unify:

- Multi-client DigiByte wallet (Android, iOS, Web)  
- DigiAssets v3 engine  
- DigiDollar minting module  
- Q-ID (PQC identity system)  
- Guardian Wallet (User Protection Layer)  
- Quantum Wallet Guard (QWG)  
- Shield Bridge (Sentinel → DQSN → ADN → QWG → Guardian)  
- Enigmatic Layer-0 communications  
- Node integration (local + DigiMobile)  
- Risk Engine  
- Telemetry  
- End-to-end test layers  

Adamantine Wallet is built to serve as the **primary gateway** for DigiByte’s next era:  
quantum-resistant, modular, secure, intelligent, and entirely open-source.

---

## 🔗 External MIT Modules Acknowledgment

Adamantine does **not** reimplement or claim ownership of external DigiByte community projects.  
It provides clean integration layers for existing MIT-licensed modules, including:

- **Enigmatic (Layer-0 messaging)** — created by @JohnnyLaw  
- **DigiMobile / Node tools** — also created by @JohnnyLaw  

Adamantine uses *adapters* to connect with these systems when they are available.  
All credit for the underlying protocols belongs to their original authors.  
Adamantine’s architecture simply enables them to work together within a unified Wallet-OS.

---

# 🧱 Architecture Summary

Adamantine Wallet is structured as:

```
DigiByte-Adamantine-Wallet/
│
├── clients/               # Android, iOS, Web clients (UI & app logic)
├── core/                  # Wallet engine, UTXO logic, shield bridge, assets
├── modules/               # DigiDollar, DigiAssets, Enigmatic, telemetry, integrations
├── docs/                  # Full whitepapers for each subsystem
├── config/                # Guardian rules, network parameters
├── tests/                 # End-to-end and unit tests
└── .github/workflows/     # CI for Android • iOS • Web • Docs
```

Each subsystem is completely modular, versioned, explainable, and independently testable.

---

# 🛡️ Adamantine & The DigiByte Quantum Shield

Adamantine is the **only DigiByte wallet** designed to deeply integrate all 5 layers of the Shield:

```
   Sentinel AI v2        (Anomaly Detection)
   DQSN v2               (Network Health & Entropy)
   ADN v2                (Active Defence Playbooks)
   QWG                   (User-Side Transaction Guard)
   Guardian Wallet       (User Warnings & Protection)
   Adaptive Core v2      (Learning & Fusion)
                ↓
     Adamantine Wallet (Final Execution Layer)
```

Adamantine is where **all shield intelligence becomes real protection**.

---

# 🧬 Wallet OS: Core Philosophy

Adamantine is built on six principles:

1. **Quantum Security First** — PQC support ready via Q-ID and QWG.  
2. **Explainability** — every decision from the shield is logged and human-understandable.  
3. **Modularity** — each subsystem is isolated and upgrade-ready.  
4. **Multi-Client Parity** — Android, iOS, and Web behave identically.  
5. **Separation of Concerns** — UI, wallet engine, shield, assets, and identity are independent.  
6. **Consensus-Neutrality** — Adamantine never changes DigiByte consensus rules.

---

# 📱 Clients (Android • iOS • Web)

```
clients/
├── android/
├── ios/
└── web/
```

Each client receives:

- wallet engine API  
- UI screens  
- Shield & Guardian integration  
- DigiAssets v3 rendering  
- DigiDollar minting UX  
- Node selection via Node Manager  
- PQC identity hooks for Q-ID  

The wallet OS layer guarantees identical behaviour across all three environments.

---

# 🔧 Core Infrastructure

```
core/
├── wallet_engine/
├── digiassets/
├── digiassets_v3/
├── guardian_adapter/
├── shield_bridge/
└── utxo_manager.py, fee_estimator.py, state, builders...
```

### 🔹 **Wallet Engine**
Implements:

- wallet state  
- UTXO selection  
- balance tracking  
- transaction building  
- fee estimation  
- sync interfaces  

### 🔹 **DigiAssets Engine**
`core/digiassets/`

Handles:

- metadata parsing  
- asset creation  
- asset transfer logic  
- asset state tracking  

### 🔹 **DigiAssets v3 Engine**
`core/digiassets_v3/`

Next-generation asset protocol:

- improved metadata structure  
- deterministic encoding  
- new ownership rules  
- future-proof PQC adaptability  

### 🔹 **Guardian Adapter**
Connects wallet actions to:

- Guardian Wallet warnings  
- QWG behavioural rules  
- Shield risk conditions  

### 🔹 **Shield Bridge**
The critical module linking Adamantine to the **Quantum Shield**:

- reads Sentinel, DQSN, ADN outputs  
- evaluates node health  
- evaluates safe mode  
- updates wallet runtime guard decisions  

---

# 🪙 DigiDollar (DD) — Native Minting Engine

```
modules/dd_minting/
```

**DigiDollar is a concept originally introduced by DigiByte founder Jared Tate.**  
Adamantine implements an open-source minting engine to support and extend that vision.

Capabilities:

- mint DigiDollar tokens (DD)  
- update ledgers  
- validate supply rules  
- integrate with the wallet engine  
- expose a clean API for clients  

DigiDollar in Adamantine is:

- **non-inflationary**  
- **deterministic**  
- **fully auditable**  

Concept credit: **Jared Tate**  
Architecture and engine implementation: **@DarekDGB (MIT-licensed)**

---

# 🧩 DigiAssets v3

```
core/digiassets_v3/
```

Includes:

- new parsing engine  
- new metadata layer  
- new execution engine  
- examples & reference spec  

This is one of the strongest future-facing upgrades in the entire repo.

---

# 🔐 Q-ID (Quantum Identity System)

```
docs/identity/
```

Q-ID provides:

- PQC identity  
- signature layering  
- recovery paths  
- identity-bound asset permissions  

100% ready for Falcon / Dilithium.

---

# 💬 Enigmatic Layer-0 Messenger

```
modules/enigmatic_chat/
```

Integrated via JohnnyLaw’s MIT-licensed Layer-0 messaging stack.

Adamantine includes:

- message encoder  
- channel manager  
- protocol adapter  

This enables **encrypted, fee-based, blockchain-aligned messaging** inside the wallet.

---

# 📡 Analytics & Telemetry

```
modules/analytics_telemetry/
```

Lightweight, anonymised, and optional.

Tracks:

- crashes  
- UI patterns  
- performance metrics  
- shield interaction signals  

Always compliant with user privacy.

---

# 🌐 Node Integration

```
core/shield_bridge/
core/node_manager.py
modules/integrations/digimobile.py
```

Adamantine connects to:

- local DigiByte Core nodes  
- DigiMobile nodes (MIT-licensed by JohnnyLaw)  
- fallback node pools  
- node reputation scoring  
- health-based priority selection  

Tests include:

- `test_node_manager_priority_logic.py`  
- `test_node_manager_errors.py`  
- `test_node_manager_digimobile_preference.py`

This is **enterprise-grade node routing**.

---

# 🛡️ Risk Engine

```
core/shield_bridge/risk_engine.py
docs/risk/*
```

Evaluates:

- network risk  
- reorg probability  
- mempool anomalies  
- timing patterns  
- node health  

Outputs flow into:

- Guardian Wallet warnings  
- QWG  
- Adaptive Core signals  

---

# 🔄 Shield Integration (Full Stack)

Adamantine is the **execution layer** of the shield:

```
DQSN  →  Sentinel  →  ADN  →  QWG  →  Guardian Wallet  →  Adamantine Wallet
```

Receives:

- metrics  
- anomalies  
- defence strategies  
- transaction decisions  
- guardianship actions  
- adaptive learning signals  

Making Adamantine the **first quantum-secure wallet OS** in DigiByte history.

---

# 🔍 Documentation

Located in:

```
docs/
```

Includes:

- architecture  
- shield layers  
- risk model  
- identity system  
- DigiAssets v3 spec  
- DigiDollar  
- node design  

➡️ Security Simulation Reports (01–03) are available in docs/security/

sim-attack-01-wallet-takeover.md
sim-attack-02-insider-supply-chain.md
sim-attack-03-quantum-harvest.md

---

# 🧪 Test Suite

```
tests/
```

Includes coverage for:

- wallet engine  
- node manager  
- risk engine  
- DigiAssets v3  
- shield bridge  
- guardian adapter  
- full wallet flows  

Production-level test depth.

---

# 🧙 Contribution Guidelines

See `CONTRIBUTING.md`.

Key rules:

- no module removal  
- no collapsing structure  
- no consensus changes  
- no black-box ML  
- no breaking shield layers  
- tests must stay green  

Only structured improvements accepted.

---

# 📜 License

MIT License  
© 2025 **DarekDGB**

This architecture is free to use with mandatory attribution.
