# 🧩 DigiAssets Engine — Core Technical Specification (v0.2)

*Location: `core/digiassets/docs/overview.md`*  
*Audience: DigiByte Core Developers & Integrators*

---

# 1. Purpose of the DigiAssets Core Engine

The DigiAssets Engine inside **Adamantine Wallet** provides a structured, modular, and security-integrated implementation of DigiByte’s asset layer.  

It does **not** modify DigiByte consensus rules.  
Instead, it provides:

- deterministic asset parsing  
- minting + transfer validation  
- metadata interpretation  
- indexing strategy  
- transaction construction helpers  
- Guardian + Shield integration points  

This document defines the **full internals** of the engine.

---

# 2. Directory Structure

```
core/
  digiassets/
    engine.py
    indexer.py
    indexing_strategy.py
    minting_rules.py
    models.py
    tx_parser.py
    tx_rules.py
    # Documentation:
    docs/
      overview.md   ← (this file)
```

---

# 3. Core Components

## 3.1 `models.py`
Defines strict data structures used across the subsystem:

### Asset Models
- `AssetDefinition`
- `AssetInstance`
- `MintIntent`
- `TransferIntent`
- `BurnIntent`
- `Metadata`
- `RuleSet` (cap, expiration, issuer lock, etc.)

All models are validated on load with rule-level checks.

---

## 3.2 `engine.py`
Main lifecycle handler for DigiAssets operations:

### Responsibilities:
- load + parse asset definitions  
- assemble mint transactions  
- assemble transfer transactions  
- validate ownership + rules  
- attach metadata into OP_RETURN  
- construct pre-signing structure for Guardian  

### Output Format
The engine returns a **normalized transaction object**:

```
{
  "inputs": [...],
  "outputs": [...],
  "metadata": {...},
  "asset_intents": [...],
  "version": "0.2"
}
```

This is the data *before* Guardian reviews and before signing occurs.

---

## 3.3 `indexer.py`
Lightweight, wallet-side DigiAssets indexer.

### Responsibilities:
- scan UTXOs for DigiAsset markers  
- reconstruct asset balances  
- detect burns, migrations, expirations  
- feed indexed state into `wallet_state.py`

Indexing is modular—external node indexing can replace it.

---

## 3.4 `indexing_strategy.py`
Defines the philosophies for parsing DigiAssets on-chain:

Two supported modes:

### Mode A — **Fast Local Scan**
- operate on user wallet UTXOs only  
- real-time updates  
- no complete chain analysis  

### Mode B — **Full Trace Reconstruction**
- rebuild entire asset history  
- authoritative supply calculation  
- slower but fully deterministic  

Developers can plug in custom strategies.

---

## 3.5 `minting_rules.py`
Canonical rule interpreter for minting:

Enforces:

- capped vs uncapped supply  
- issuer-bound rules  
- burn-to-mint rules (optional)  
- DigiDollar-specific minting logic  

Ensures mint intent is compliant before Guardian sees it.

---

## 3.6 `tx_parser.py`
Low-level parser for DigiByte transactions.

Extracts:

- OP_RETURN metadata  
- asset markers  
- output topology  
- supply change signals  

Feeds parsed structures into the DigiAssets engine via uniform objects.

---

## 3.7 `tx_rules.py`
Defines transaction-level rules:

- asset ID consistency  
- multi-output constraints  
- malformed metadata detection  
- disallowed combinations  
- "safe-transfer" defaults  

Directly used before signing and before Guardian security checks.

---

# 4. Asset Lifecycle in the Engine

## Step 1 — Parse or Create Intent
Either:
- user submits a mint/transfer request  
- engine parses an incoming TX  

## Step 2 — Validate Rules
Applies:
- mint rules  
- transfer rules  
- metadata schema validation  

## Step 3 — Construct Pre-Signature Transaction
Engine creates DigiByte transaction model.

## Step 4 — Send to Guardian
Guardian performs:

- policy scoring  
- user-context validation  
- risk thresholds  
- Shield risk-map aggregation  

## Step 5 — Shield Analysis  
Shield Bridge → DQSN → Sentinel → QWG → ADN  
return a unified security packet.

## Step 6 — Guardian Decision
- allow  
- warn  
- block  
- lockdown  

## Step 7 — Final TX Signing (outside core engine)

---

# 5. Metadata Encoding Specification

DigiAssets metadata is encoded via:

```
OP_RETURN <protocol-tag> <json-blob>
```

Engine ensures:

- valid JSON  
- allowed schema fields (per version)  
- deterministic ordering  
- maximum OP_RETURN size compliance  

---

# 6. DigiDollar (DD) Support

DigiDollar minting is supported through:

- `MintIntent`  
- DD-specific minting rules  
- value-backed issuance models  
- Guardian scoring → protects issuance  

This module does **not** implement stablecoin consensus—  
it only supplies issuer tools.

---

# 7. Security Model

The DigiAssets engine is protected through:

### Internal Validation
- strict rule enforcement  
- deterministic metadata parsing  
- zero ambiguity in UTXO ownership  

### Guardian Enforcement
- adaptive policy rules  
- context-aware scoring  

### Shield Enforcement
- anomaly detection  
- reorg-risk  
- topology drift  
- PQC-event hooks  

Together, this forms a **triple-layer safety model**.

---

# 8. Extensibility (v0.3+)

Planned:
- richer metadata schemas  
- collection-type assets  
- encrypted metadata  
- Layer-0 correlation (Enigmatic)  
- asset discovery index improvements  

---

# 9. Summary

This document provides a **full technical overview** of the DigiAssets subsystem inside Adamantine v0.2.  
It defines engine structure, rules, flow, metadata encoding, and Shield/Guardian integration.

A supplementary document for **full schema definitions** will be created under:

```
core/digiassets/docs/schemas.md
```

