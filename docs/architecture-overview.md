# Adamantine Wallet — Architecture Overview  
Status: **draft v0.3**

This document provides a high-level map of the Adamantine Wallet architecture, covering its modules, core systems, security layers, data flows, and platform implementations.

---

## 1. Architectural Goals

Adamantine Wallet is designed to be:

- **DigiByte-native** – first-class support for DGB, DigiAssets, and DigiDollar (DD).  
- **Security-first** – deeply integrated with the 5-layer DigiByte Quantum Shield + Adaptive Core.  
- **Multi-platform** – consistent UX and safety guarantees across **Android**, **iOS**, and **Web**.  
- **Modular & auditable** – each concern (keys, assets, messaging, analytics) lives in its own module.  
- **Future-proof** – ready for Taproot, Enigmatic Layer-0 communication, and post-quantum upgrades.

This file is the “map of the city.” All other docs provide street-level detail.

---

## 2. High-Level Layering

From top (user) to bottom (chain), Adamantine is structured into these layers:

### **1. Client Apps (UI Layer)**
- `clients/android/`  
- `clients/ios/`  
- `clients/web/`  

Responsible for screens, navigation, secure storage integration, biometrics, and notifications.

---

### **2. Wallet Core**
Handles:

- account abstraction  
- key management  
- UTXO selection  
- transaction building  
- fee calculation  
- balance state for DGB, DigiAssets, and DigiDollar  

This layer exposes a stable API shared across all clients.

---

### **3. Security & Guard Rails**
Includes:

- **Guardian Wallet** – local policy engine that turns shield risk into user decisions (PIN, biometric, guardian approval, or hard blocks).
- **Shield Bridge** – glue layer connecting the wallet to DigiByte’s 5-Layer Quantum Shield:  
  - Sentinel AI v2  
  - DQSN v2  
  - ADN v2  
  - QWG  
  - Adaptive Core (DQAC)

Supports both **online mode** (live signals) and **offline mode** (cached profiles).

---

### **4. Assets & Value Layer**
- **DGB (base layer)** – standard UTXO asset.  
- **DigiAssets** – tokens/NFTs; creation, issuance, transfers, burns.  
- **DigiDollar (DD)** – mint/redeem logic, oracle connections, shield-aware risk checks.

---

### **5. Layer-0 Messaging (Enigmatic)**
Wallet-to-wallet communication through UTXO state planes:

- intents  
- requests  
- shield telemetry  
- DD governance messages  

Implemented under `modules/enigmatic-chat/`.

---

### **6. Analytics & Telemetry**
Located in `modules/analytics-telemetry/`.

Collects privacy-respecting, opt-in signals such as:

- error patterns  
- performance  
- shield event summaries  

No personal data or addresses.

---

### **7. Persistence & Configuration**
- secure storage (OS keychain / keystore)  
- encrypted local DB  
- `config/` directory for shield endpoints, node lists, risk profiles, guardian rules  

---

### **8. External Dependencies**
- DigiByte full nodes (local or remote)  
- Digi-Mobile (Android full node)  
- Oracle services  
- Shield infrastructure endpoints  

---

## 3. Module Map

The repository is organised as:

- **`.github/`** – CI workflows, linting, docs validation.  
- **`clients/`** – Android, iOS, and Web UI frontends.  
- **`core/`**
  - `data-models/` – wallet state, contact, message models.  
  - `guardian-wallet/` – configs, policy engine, evaluation logic.  
  - `pqc-containers/` – future post-quantum key formats.  
  - `qwg/` – Quantum Wallet Guard rules & hooks.  
  - `risk-engine/` – scoring, thresholds, guardian integration.  
  - `shield-bridge/` – interface to Shield layers (Sentinel, DQSN, ADN, QWG, Adaptive Core).  
  - `digiassets/` – parsing, indexing, mint, transfer, and burn logic.  
- **`modules/`**
  - `dd-minting/` – DigiDollar mint/redeem flows.  
  - `enigmatic-chat/` – Layer-0 messaging and dialect integration.  
  - `analytics-telemetry/` – privacy model and analytics spec.  
- **`docs/`** – all architecture, design, narrative specs.  
- **`tests/`** – scenario-driven test plans for all modules.

---

## 4. Key Data Flows

### **4.1 DGB Send**
1. Client initiates send  
2. Wallet Core selects UTXOs and drafts TX  
3. Shield Bridge computes risk  
4. Guardian Wallet applies policies  
5. If allowed → sign & broadcast  
6. Optional telemetry logs anonymised events  

---

### **4.2 DigiAsset lifecycle**
1. User initiates creation/issue/transfer  
2. DigiAssets engine builds transaction pattern  
3. Shield Bridge + Guardian validate safety  
4. Enigmatic optionally embeds L0 announcements  
5. Wallet signs + broadcasts  

---

### **4.3 DigiDollar mint/redeem**
1. User selects mint/redeem  
2. DD engine orchestrates oracle + shield checks  
3. Guardian policies apply  
4. Safe → sign; unsafe → block / require guardian  
5. Balances update accordingly  

---

### **4.4 Enigmatic Messaging**
1. User creates message  
2. Enigmatic encodes dialect pattern  
3. Shield evaluates detectability & plausibility  
4. Wallet signs  
5. Receiver decodes via same dialect  

---

## 5. Security & Trust Model

- **Device Trust** – keychains, secure enclave, encrypted DB.  
- **Shield Integration** – every critical flow may consult Sentinel, DQSN, ADN, QWG, and Adaptive Core.  
- **Guardian Policies** – UX is shaped by security posture (PIN, biometrics, guardian approval).  
- **Opt-In Telemetry** – no tracking, no identifiers, fully transparent.

---

## 6. Platform Notes

### **Android & iOS**
- native biometric APIs  
- secure storage primitives  
- offline-capable with cached shield profiles  

### **Web**
- hardened UX  
- non-custodial  
- optional integration with browser extensions  

---

## 7. Roadmap Hooks

- PQC signing container implementation  
- DigiAsset gallery + marketplace  
- advanced guardian schemes (travel mode, per-contact trust)  
- more Enigmatic dialects  
- expanded shield heuristics  
- multi-sig and social recovery  

---

## 8. Digi-Mobile Integration (Android)

Adamantine can operate with multiple DigiByte node backends.  
On Android, the preferred backend is a **local Digi-Mobile node** when available.

### **How it works**

1. Digi-Mobile runs a pruned DigiByte Core daemon on the device  
2. Exposes JSON-RPC on `127.0.0.1:<port>`  
3. Adamantine auto-detects the node and uses it for:
   - UTXO set queries  
   - fee estimation  
   - mempool checks  
   - broadcasting  

If available, Adamantine switches into **local full-node mode**:

```
Android Device
┌────────────────────────────┐
│   Digi-Mobile (local node) │  ← Pruned DigiByte Core
└───────────────┬────────────┘
                │ JSON-RPC
┌───────────────▼────────────┐
│     Adamantine Wallet       │
│  (Guardian + Shield Stack)  │
└─────────────────────────────┘
```

If unreachable, Adamantine falls back to the remote nodes defined in  
`config/example-nodes.yml`.

### **Why it matters**

- trustless validation  
- no RPC leakage → maximum privacy  
- protected against censorship/outages  
- perfectly aligned with Guardian + Shield security model  

With Digi-Mobile + Adamantine, Android becomes a **self-contained DigiByte security environment**.

---

*This document is updated as Adamantine evolves from design to implementation.*  
