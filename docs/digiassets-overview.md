# 🧩 DigiAssets Overview — Adamantine Wallet (v0.2)
*High-level architecture summary for the DigiAssets Engine inside Adamantine.*

---

## 1. What Are DigiAssets?

**DigiAssets** are non-fungible and fungible digital tokens that run on top of the DigiByte blockchain.  
They use DigiByte’s **UTXO model**, **transaction rules**, and **block structure** to encode:

- asset issuance  
- transfers  
- metadata  
- supply rules  
- ownership  

DigiAssets require **no consensus changes** and work entirely through standard DigiByte transactions and metadata encoding.

Adamantine Wallet includes a **next-generation DigiAssets Engine** designed to be:

- modular  
- secure  
- Guardian-aware  
- Shield-aware  
- fully user-friendly  
- compatible with existing DigiAssets standards  

---

## 2. Adamantine’s DigiAssets Engine — High-Level Components

The DigiAssets subsystem in Adamantine v0.2 is structured into several modules:

### **2.1 Engine**
Handles:

- encoding/decoding DigiAsset transactions  
- interpreting metadata  
- enforcing supply rules  
- validating ownership  
- multi-output + batching logic  

This engine does *not* broadcast transactions directly — it only prepares structured data which is then passed to the **Guardian Wallet workflow** for security checks.

---

### **2.2 Models**
Defines the core data structures:

- `AssetDefinition`  
- `AssetInstance`  
- `TransferIntent`  
- `MintIntent`  
- `BurnIntent`  

All models are type-strict, versioned, and validated before usage.

---

### **2.3 Presets**
Contains pre-configured templates for common operations:

- single-asset simple transfer  
- multi-output transfer  
- mint with cap  
- mint without cap  
- burn flows  
- DigiDollar (DD) mint presets  

These presets simplify creation of assets for users and third-party developers.

---

### **2.4 Flows**
Defines multi-step asset operations such as:

- minting  
- distributing  
- transferring  
- batching  
- metadata updates  

A “flow” is a scripted sequence that feeds into **Guardian** before any signing occurs.

---

## 3. Integration with the Guardian Wallet

Before a DigiAsset transaction is signed:

1. **Engine** forms the TX + metadata  
2. **Guardian** evaluates:  
   - policy rules  
   - scoring  
   - risk thresholds  
   - user context  
3. **Shield Bridge** receives a normalized risk packet  
4. **DQSN + Sentinel + QWG + ADN** provide aggregated signals  
5. Guardian approves, warns, blocks, or enters lockdown  

This ensures **every DigiAsset operation is protected by the full Quantum Shield**.

---

## 4. Integration with Shield-Bridge

When a DigiAsset transaction is prepared:

- metadata  
- fee structure  
- output structure  
- asset IDs  
- OP_RETURN metadata plane  

are passed as structured fields through Shield Bridge for:

- anomaly detection  
- malformed metadata checking  
- cross-node validation  
- topology analysis  

This ensures DigiAssets cannot be abused through malformed or manipulated messages.

---

## 5. DigiDollar (DD) Minting Integration

The DigiAssets Engine powers DigiByte’s **DigiDollar (DD)** minting via:

- `MintIntent`  
- DD-specific presets  
- Guardian scoring checks  
- issuance validation  

This is a lightweight modular system:

- no new consensus rules  
- no new opcodes  
- fully DigiByte-compatible  

Adamantine simply provides a **secure minting interface**.

---

## 6. Planned Additions (v0.3 and later)

In future versions, the DigiAssets subsystem will support:

- richer metadata schemas  
- asset collection views  
- Layer-0 messaging correlation (Enigmatic)  
- multi-asset dashboards  
- QR-based transfer interaction  
- enhanced indexing cache  

These are documented but not implemented in v0.2.

---

## 7. Summary

DigiAssets in Adamantine v0.2 have:

- a complete architecture  
- modular engine  
- strict validation  
- Guardian + Quantum Shield integration  
- minting and transfer workflows  
- full future extensibility  

This document summarizes the subsystem at a high level.  
A **full technical specification** will be placed under:

```
core/digiassets/docs/overview.md
```

