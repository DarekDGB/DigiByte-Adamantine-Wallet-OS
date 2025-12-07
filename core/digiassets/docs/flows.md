
# 🔄 DigiAssets Engine — Flow Specifications (v0.2)
*Location: `core/digiassets/docs/flows.md`*  
*Audience: DigiByte developers implementing full DigiAssets support inside Adamantine.*

This document defines the **canonical mint, transfer, and burn flows** used by the DigiAssets Engine in Adamantine v0.2.  
Flows formalize the **ordered sequence of operations** that the engine, Guardian, Node Adapter, and Shield Bridge follow.

---

# 1. What Is a Flow?

A **flow** is a structured, multi‑step process that transforms a high‑level intent  
(e.g., “mint 100 tokens”)  
into:

1. a normalized transaction model  
2. security evaluation (Guardian + Shield)  
3. the final signed transaction ready for broadcast

All flows must be:

- deterministic  
- stateless (except for index lookups)  
- fully inspectable  
- Guardian‑gated  

---

# 2. Mint Flow (MINT)

Minting creates new units of a DigiAsset or DigiDollar.

### ASCII Diagram

```
MintIntent → Engine → Rule Validation → TX Model
            ↓
         Guardian → Shield Bridge → Risk Evaluation
            ↓
          Verdict (allow / warn / block)
            ↓
         Signing → Broadcast (if allowed)
```

---

## 2.1 Mint Flow Steps (Technical)

### **Step 1 — Receive MintIntent**
Engine accepts a structure:

```
{
  asset_id,
  mint_amount,
  destination_address,
  metadata,
  supply_rules
}
```

### **Step 2 — Load AssetDefinition**
Engine retrieves asset definition (local or remote).

### **Step 3 — Validate Mint Rules**
Checks:

- remaining supply  
- cap vs uncapped logic  
- metadata schema  
- burn‑to‑mint dependencies (if any)  

### **Step 4 — Construct Transaction Skeleton**
Engine prepares:

- inputs (UTXOs)  
- outputs (destination + change)  
- OP_RETURN metadata payload  

No signatures yet.

### **Step 5 — Forward to Guardian**
Guardian performs:

- scoring  
- policy check  
- risk aggregation  
- DD‑mint special thresholds  

### **Step 6 — Shield‑Bridge Evaluation**
Shield queries:

- Sentinel (mempool conditions)  
- DQSN (network view)  
- ADN (node health)  
- QWG (key posture)  
- Adaptive memory  

### **Step 7 — Guardian Verdict**
- allow  
- warn  
- block  
- lockdown  

### **Step 8 — Signing**
Only allowed if Guardian returns allow/warn.

### **Step 9 — Broadcast**
Node adapter broadcasts via RPC.

---

# 3. Transfer Flow (TRANSFER)

Used for moving existing DigiAsset balances.

### ASCII Diagram

```
TransferIntent → Engine → Input/Output Validation → TX Model
                ↓
              Guardian → Shield Bridge → Risk Map
                ↓
             Verdict → Signing → Broadcast
```

---

## 3.1 Transfer Flow Steps

### **Step 1 — Receive TransferIntent**
Includes:

```
inputs[], outputs[], change_address, fee_rate, metadata
```

### **Step 2 — Ownership + Balance Check**
Engine verifies:

- user owns all inputs  
- amounts are valid  
- no negative deltas  

### **Step 3 — RuleSet Enforcement**
From AssetDefinition:

- transferable flag  
- max batch limit  
- restricted addresses  
- metadata requirements  

### **Step 4 — Construct Transaction Skeleton**
Engine compiles:

- input/output map  
- metadata payload  
- DigiByte standard fees  

### **Step 5 — Send to Guardian**
Guardian does:

- anomaly scoring  
- context evaluation  
- detection of address/drain abnormalities  
- Shield‑Bridge preflight  

### **Step 6 — Shield Analysis**
Risk map is built from:

- Sentinel → mempool drift  
- DQSN → network disagreement  
- ADN → local node safety  
- QWG → key posture  
- Adaptive → behavior history  

### **Step 7 — Guardian Verdict**
Same as mint flow.

### **Step 8 — Signing + Broadcast**

---

# 4. Burn Flow (BURN)

Used to reduce supply or retire tokens.

### ASCII Diagram

```
BurnIntent → Engine → Burn Validation → TX Model
             ↓
          Guardian → Shield → Verdict → Signing
```

---

## 4.1 Burn Flow Steps

### **Step 1 — Receive BurnIntent**
Structure:

```
asset_id, amount, burn_utxo, reason?
```

### **Step 2 — Ownership Validation**
Engine verifies user owns the burn_utxo.

### **Step 3 — RuleSet Enforcement**
Checks:

- burn allowed  
- reason required?  
- amount valid  

### **Step 4 — Construct Burn TX**
Engine creates:

- input = burn_utxo  
- output = OP_RETURN metadata marking “burn”  

### **Step 5 — Guardian Review**
Guardian ensures:

- no behavior anomalies  
- no attempts to burn unauthorized assets  
- no conflicting asset policies  

### **Step 6 — Shield Evaluation**
Same 5‑layer evaluation.

### **Step 7 — Verdict → Signing → Broadcast**

---

# 5. Common Validation Rules

All flows share:

- **maximum outputs**  
- **maximum inputs**  
- **metadata size**  
- **allowed protocols**  
- **asset ID checks**  
- **signing horizon limits** (Guardian)  

These appear in:

- `tx_rules.py`  
- `guardian_policy.py`  
- `scoring-rules.md`  

---

# 6. Flow Output Schema

Every flow emits a standard structure:

```json
{
  "tx_model": {
    "inputs": [],
    "outputs": [],
    "metadata": {},
    "version": "0.2"
  },
  "context": {
    "flow_type": "MINT | TRANSFER | BURN",
    "asset_id": "string",
    "risk_preflight_id": "uuid"
  }
}
```

Guardian consumes this and returns a verdict.

---

# 7. Integration Points

### **Engine → Guardian**
via:

- `guardian_adapter.py`
- `guardian_api.md`

### **Guardian → Shield Bridge**
via:

- `sentinel-api.md`
- `dqsn-api.md`
- `adn-api.md`
- `qac-api.md`
- `adaptive-core-api.md`

### **Guardian → Node**
via:

- `node-api.md`

---

# 8. Error Handling

Flows can return:

- `RULE_VIOLATION`
- `INVALID_METADATA`
- `INSUFFICIENT_BALANCE`
- `POLICY_BLOCKED`
- `GUARDIAN_CRITICAL`
- `NODE_UNSAFE`

Errors are always structured JSON.

---

# 9. Summary

This document defines the **behavioral flow** for all DigiAssets actions inside Adamantine v0.2.  
It ensures developers can implement or extend asset functionality while maintaining:

- determinism  
- safety  
- Guardian compliance  
- Shield compatibility  

The flows are stable for v0.2 and will expand during v0.3 implementation.

