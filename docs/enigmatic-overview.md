# Enigmatic — Layer‑0 Messaging Overview
Status: draft v0.1

This document explains how **Enigmatic**, the DigiByte Layer‑0 communication 
protocol created by JohnnyLaw, integrates into the Adamantine Wallet.  
It highlights architecture, messaging flows, wallet use cases, risk controls, 
and future extensions.

---

## 1. What Enigmatic Is

Enigmatic is a **Layer‑0 signalling system** that uses DigiByte’s existing 
UTXO, fee, and transaction‑topology space to encode *intent*, without 
modifying consensus rules.

Each transaction expresses a **state vector** across five planes:

1. **Value plane**
2. **Fee plane**
3. **Cardinality plane** (inputs/outputs)
4. **Topology plane** (graph shape)
5. **Block‑placement plane** (height patterns)

These patterns form *dialects*—structured symbol sets representing:
- messages  
- events  
- intents  
- confirmations  
- heartbeat signals  

---

## 2. Why Adamantine Uses Enigmatic

Adamantine integrates Enigmatic for:

### • Wallet‑to‑wallet secure messaging  
### • Shield‑aware signalling (risk flags & confirmations)  
### • DigiAssets meta‑events  
### • DigiDollar mint/burn intents  
### • Multi‑frame governance actions (future)  

Because Enigmatic transactions look like **ordinary DigiByte transactions**, 
they provide *deniability* and privacy.

---

## 3. Components in Adamantine

Enigmatic inside the wallet includes:

- **Encoder** — converts high‑level intents to state vectors  
- **Planner** — selects UTXOs, fees, spread, and cadence  
- **Transaction Builder** — constructs signalling TXs  
- **Decoder** — reads state vectors from the chain  
- **Watcher** — observes multi‑frame conversations  
- **Dialects** — symbol definitions for DD, DigiAssets, Shield, chat  

Everything matches the reference repo structure:

```
enigmatic_dgb/
specs/
docs/
examples/
tests/
```

---

## 4. Wallet Integration Architecture

```
UI → Enigmatic Chat Layer
    → Enigmatic Engine (encode/plan/decode)
        → Wallet Core (key mgmt, UTXOs, fees)
            → DigiByte Node
```

A second path is used for shield communications:

```
Shield Bridge → Enigmatic Engine → TX Builder → Node
```

This allows Adamantine to send **Layer‑0 defensive signals** such as:

- anomaly‑confirmation  
- shield‑sync intents  
- heartbeat beacons  
- DD mint/burn proofs  

---

## 5. Enigmatic Chat (User Feature)

The user‑visible part is a secure, chain‑anchored messaging system:

- each message → 1 or more encoded transactions  
- recipients decode via the same dialect  
- metadata stored locally, not on‑chain  
- optional identity binding to wallet addresses  

Planned safety features:

- spam resistance  
- abuse‑protection heuristics  
- session‑level encryption (wallet‑local)  
- shield‑score integration for risky contacts  

---

## 6. Enigmatic for DigiAssets

Enigmatic can broadcast:

- asset‑mint intents  
- supply‑updates  
- certificate announcements  
- provenance breadcrumbs  

This allows auditors, indexers, and interested wallets to detect asset events 
without scanning the entire chain.

---

## 7. Enigmatic for DigiDollar (DD)

DD uses Enigmatic optionally for:

- `MINT_INTENT`  
- `BURN_INTENT`  
- `SUPPLY_CHANGE`  
- safety messages (halt, confirm, audit)  

This decentralizes DD communication and avoids dependence on external servers.

---

## 8. Shield Integration

Enigmatic is deeply integrated with the DigiByte Quantum Shield:

### Sentinel AI  
Reads Enigmatic patterns for anomaly detection.

### DQSN  
Uses Enigmatic for distributed confirmations.

### ADN v2  
Uses signalling frames to lock or release transaction flows.

### QAC  
Inspects plane consistency for cryptographic manipulation.

### Adaptive Core  
Learns dialect frequency, pattern safety, and long‑term behavioural drift.

---

## 9. Risk & Deniability Model

Enigmatic transactions are designed to be:

- economically plausible  
- policy‑compliant  
- deniable  
- non‑detectable by naive observers  

Wallet‑side mitigations include:

- dialect rotation  
- jitter injection  
- cardinality variation  
- OP_RETURN hints (optional)  
- shield‑assisted risk assessment  

---

## 10. Roadmap

### v0.2  
- DD dialect  
- DigiAssets dialects  
- Chat identity binding  

### v0.3  
- Governance dialect  
- Multi‑wallet conversations  
- Stealth sessions  

### v1.0  
- Full test suite  
- Indexer‑integration  
- Shield‑synchronized dialect switching  

---

Author: **DarekDGB**  
License: MIT
