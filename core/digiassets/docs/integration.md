# 🔗 DigiAssets Integration — Guardian, Shield & Node (v0.2)
*Location: `core/digiassets/docs/integration.md`*  
*Audience: DigiByte Core Developers & Wallet Integrators*

This document explains **how the DigiAssets Engine is wired into**:

- the **Guardian Wallet** (policy + decision engine)
- the **Shield Bridge** (Sentinel, DQSN, ADN, QWG, Adaptive Core)
- the **Node Adapter** (RPC / node health)
- the **Adamantine Wallet UI** (clients/android, clients/ios, clients/web)

It should be read after:

- `core/digiassets/docs/overview.md`
- `core/digiassets/docs/schemas.md`
- `core/digiassets/docs/flows.md`

---

## 1. High-Level Integration Diagram

```text
User → UI (web/ios/android)
       ↓
  DigiAssets Engine  ←→  Indexer
       ↓
   Guardian Adapter (DigiAssets)
       ↓
     Guardian
       ↓
   Shield Bridge
       ↓
Sentinel / DQSN / ADN / QWG / Adaptive
       ↓
    Guardian Verdict
       ↓
   Node Adapter (broadcast)
```

---

## 2. Engine → Guardian Integration

The integration entry point for DigiAssets into Guardian is:

- `modules/digiassets/guardian_bridge.py`
- `modules/digiassets/guardian-rules.md`
- `core/risk-engine/guardian_adapter.py`

### 2.1 Normalised Request Object

For any DigiAssets flow (`MINT`, `TRANSFER`, `BURN`), the engine emits a **Guardian-ready request**:

```json
{
  "wallet_id": "adamantine-main",
  "account_id": "default-digiassets",
  "asset_id": "string",
  "flow_type": "MINT | TRANSFER | BURN",
  "tx_model": {
    "inputs": [],
    "outputs": [],
    "metadata": {},
    "fee_sats": 0
  },
  "context": {
    "client": "web | ios | android",
    "geo_hint": "…",
    "behaviour_profile_id": "…"
  }
}
```

This maps directly into:

- `POST /v0/tx/preflight` (see `guardian-api.md`)
- with DigiAssets-specific annotations in `details`.

---

### 2.2 Guardian Policy Consumption

The following Guardian policy aspects are applied to DigiAssets:

- per-asset **limits** (max transfer per day, max mint per day)
- per-asset **2FA requirements**
- **lockdown behaviour** if assets are flagged as compromised
- **DigiDollar (DD)**-specific policy overrides (e.g. stricter thresholds)

Guardian rules for DigiAssets are documented in:

- `modules/digiassets/guardian-rules.md`
- `core/risk-engine/guardian-thresholds.md`

---

## 3. Guardian → Shield Bridge Integration

Once the DigiAssets request reaches Guardian, it is transformed into a **Shield-Bridge risk packet**.

### 3.1 Shield Input Envelope

```json
{
  "layer": "digiassets",
  "asset_id": "string",
  "flow_type": "MINT | TRANSFER | BURN",
  "tx_shape": {
    "input_count": 0,
    "output_count": 0,
    "has_op_return": true
  },
  "metadata_summary": {
    "size_bytes": 0,
    "schema": "digiasset-metadata-v1"
  },
  "risk_context": {
    "wallet_id": "adamantine-main",
    "account_id": "default-digiassets"
  }
}
```

Shield Bridge then dispatches this to:

- Sentinel → mempool + anomaly checks
- DQSN → cross-node opinion on recent blocks / UTXO graph
- ADN → node health & lockdown state
- QWG → key posture related to the DigiAssets account
- Adaptive Core → behavior history for this wallet and asset

The responses are aggregated into a structure consumed by Guardian as `GuardianRiskSnapshot`.

---

## 4. Engine → Node Adapter Integration

Engine **never** talks directly to the node.

All node interactions are done through:

- `core/node/node_client.py`
- `core/node/node_manager.py`
- `core/node/rpc_client.py`
- documented in `core/node/node-api.md`

### 4.1 Required Node Capabilities

For DigiAssets, the node must support:

- standard DigiByte JSON-RPC (getrawtransaction, sendrawtransaction, etc.)
- mempool inspection (for Sentinel / risk engine)
- block/UTXO data for indexer reconstruction

### 4.2 Broadcast Path

If Guardian returns a positive verdict:

1. DigiAssets Engine finalises the transaction (ready-to-sign model).
2. Signing is performed in the wallet key-management layer.
3. Node Adapter broadcasts via `sendrawtransaction`.

---

## 5. Engine ↔ Indexer Integration

The DigiAssets Engine uses:

- `core/digiassets/indexer.py`
- `core/digiassets/indexing_strategy.py`

to:

- reconstruct balances  
- support **TransferIntent** creation  
- display wallet asset portfolios in the UI  

Indexer output conforms to `IndexerRecord` schema in `schemas.md`.

The Indexer can be:

- local to the node (wallet mode), or  
- remote (shared index service).

---

## 6. UI Integration (Web / iOS / Android)

The UI layers (under `clients/`) interact with DigiAssets through:

- a **wallet service** layer (`core/wallet-service/`) that exposes:
  - list of assets
  - balances
  - mint/transfer/burn flows
  - Guardian status (warnings, blocks, lockdown)

### 6.1 Typical UX Flow (Transfer)

1. User selects an asset + destination + amount.
2. UI forms a `TransferIntent` or equivalent high-level payload.
3. Wallet service calls DigiAssets Engine.
4. DigiAssets Engine returns a pre-signing model + Guardian preflight result summary.
5. UI shows:
   - risk banner
   - prompts for 2FA if needed
6. If user confirms, signing + broadcast proceed.

---

## 7. Tests & Validation

DigiAssets integration is validated by:

- `tests/test_digiassets_engine.py`
- `tests/test_digiassets_indexer.py`
- `tests/test_guardian_adapter_digiassets.py`
- `tests/digiassets-tests.md`

These tests illustrate:

- correct interaction between the engine and Guardian
- proper handling of rule violations
- metadata validation
- flows correctness

---

## 8. Extensibility Notes

Future integration points:

- mapping DigiAssets into **Enigmatic Layer-0** for richer messaging
- correlation between DigiAssets and **DigiDollar (DD)** for basket assets
- asset-based risk profiles in Guardian (e.g. “high-risk” vs “stable” assets)
- advanced indexer backends (SQL, key-value, remote index microservice)

---

## 9. Summary

DigiAssets in Adamantine v0.2 are not an isolated engine.  
They are deeply integrated with:

- Guardian (policy + scoring)
- Shield Bridge (network-wide risk)
- Node Adapter (safe broadcast)
- Indexer (state reconstruction)
- UI (secure, user-friendly workflows)

This document serves as the **integration map** for developers who want to:

- extend DigiAssets logic, or  
- plug in alternative backends, or  
- build advanced asset features on top of Adamantine.
