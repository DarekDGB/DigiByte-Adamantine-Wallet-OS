# 💎 DigiDollar (DD) — Core Technical Specification (v0.2)
*Location: `modules/dd_minting/docs/overview.md`*  
*Audience: DigiByte Core Developers, Wallet Architects, and Integrators*

DigiDollar (DD) is a **DigiAssets‑based stable issuance model** protected by Guardian and the full 5‑Layer Quantum Shield.  
This document defines the **technical architecture**, **rules**, and **flows** for DD minting, redemption, validation, and Shield integration.

---

# 1. Purpose of DigiDollar (DD)

DD is not a new blockchain or consensus mechanism.  
It is a **token issuance standard** implemented as a DigiAsset with:

- policy‑enforced minting  
- predictable supply rules  
- Guardian‑checked issuance  
- Shield risk evaluation  
- stable value conventions (off‑chain oracle optional)

Adamantine Wallet provides:

- **DD Mint Engine**
- **DD Redemption Engine**
- **Guardian ruleset for DD**
- **Shield risk profiles for minting**

---

# 2. Directory Structure

```
modules/
  dd-minting/
    mint-flow.md
    redeem-flow.md
    guardian-bridge.md
    oracle-and-risks.md
    spec.md
    ui-wireframes.md
  dd_minting/
    engine.py
    models.py
    __init__.py
```

---

# 3. Core Concepts

## 3.1 DD AssetDefinition

A DigiDollar asset is defined using the standard DigiAssets schema, but with DD‑specific flags:

```json
{
  "dd_enabled": true,
  "mint_rules": {
    "requires_guardian_approval": true,
    "requires_risk_evaluation": true,
    "max_per_tx": 1000000
  },
  "redeem_rules": {
    "allowed": true
  }
}
```

Guardian enforces these rules strictly and will block mint attempts that violate policy.

---

# 4. DD Models

## 4.1 `DDMintIntent`

```json
{
  "version": "1.0",
  "asset_id": "string",
  "amount": "integer",
  "destination": "string",
  "backing_reference": "string | null",
  "metadata": {}
}
```

## 4.2 `DDRedeemIntent`

```json
{
  "version": "1.0",
  "asset_id": "string",
  "amount": "integer",
  "recipient": "string",
  "metadata": {}
}
```

---

# 5. Minting Lifecycle

### ASCII Diagram

```
DDMintIntent → DD Engine → Rules → DigiAssets Engine
                 ↓
              Guardian → Shield Bridge → Risk Map
                 ↓
             Verdict → Signing → Broadcast
```

---

## 5.1 Detailed Steps

### **Step 1 — Receive DDMintIntent**

Input includes:

- amount  
- asset_id  
- backing_reference (proof of value, optional)  
- metadata  

### **Step 2 — Validate Rules**

Engine checks:

- supply caps  
- DD-specific thresholds  
- mint frequency limits  
- metadata completeness  

### **Step 3 — Build DigiAssets MintIntent**

DD engine wraps its intent into standard DigiAssets minting.

### **Step 4 — Guardian Review**

Guardian considers:

- amount thresholds  
- DD-specific mint risk multipliers  
- user behavior  
- geolocation / device context  
- Shield risk map  

### **Step 5 — Shield Analysis**

- Sentinel → economic spam detection  
- DQSN → supply consensus agreement  
- ADN → node safety  
- QWG → key posture  
- Adaptive → minting behavior history  

### **Step 6 — Verdict**

- allow  
- warn (rare)  
- block  
- critical lockdown (very rare)

---

# 6. Redemption Lifecycle

### ASCII Diagram

```
DDRedeemIntent → DD Engine → Rules → DigiAssets BurnIntent
                    ↓
                 Guardian → Shield → Verdict
                    ↓
               Signing → Burn TX → Broadcast
```

### Steps

1. Validate redeem rules  
2. Convert to BurnIntent  
3. Guardian checks for fraud or drain attempts  
4. Shield validates network conditions  
5. Transaction is signed and broadcast  

---

# 7. Guardian Ruleset for DigiDollar

Documented in:

- `guardian_bridge.md`
- `guardian-rules.md`

Guardian applies:

- stricter thresholds for DD than normal assets  
- mandatory 2FA for large mints  
- daily mint caps  
- velocity checks  
- unusual-pattern detection (Adaptive layer)  

If Guardian detects instability, the DD minting subsystem is temporarily **locked down**.

---

# 8. Shield Risk Profiles for DD

DD has unique risk signals:

- large issuance attempts  
- repetitive mint bursts  
- oracle deviation (if backing reference used)  
- network mempool spam correlation  

Shield produces a DD‑specific risk packet including:

```json
{
  "risk_dd": {
    "amount_factor": 0.8,
    "oracle_factor": 0.2,
    "mint_velocity_factor": 0.7
  }
}
```

Aggregated with:

- Sentinel  
- DQSN  
- ADN  
- QWG  
- Adaptive memory  

---

# 9. Node Interaction

DD does not add new RPC calls.

Broadcast path:

1. DD Engine → DigiAssets Engine  
2. Guardian → approval  
3. Node Adapter → `sendrawtransaction`

Indexer picks up DD transactions like any DigiAsset.

---

# 10. UI Integration

UI supports:

- DD balance view  
- mint interface  
- redeem interface  
- Guardian warnings (color-coded)  
- risk explanation panels  

All flows match the logic in:

`modules/dd-minting/ui-wireframes.md`

---

# 11. Tests

Related tests:

- `tests/test_dd_minting_engine.py`
- `tests/dd-minting-tests.md`

They ensure:

- safe mint construction  
- safe redeem construction  
- rule enforcement  
- Guardian integration behavior  

---

# 12. Version Notes

This specification defines:

```
DD Engine version: 0.2
Mint flow version: 0.2
Redeem flow version: 0.2
```

DD 0.3 will introduce optional oracle-binding templates and expanded Guardian controls.

---

# 13. Summary

DigiDollar (DD) in Adamantine v0.2 provides:

- a secure mint/redeem mechanism  
- full Guardian + Shield protection  
- deterministic DigiAssets-based rules  
- compatibility with the existing DigiByte ecosystem  

This spec allows developers to extend, audit, or replace DD components safely.

