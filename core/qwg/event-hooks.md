# PQC Wallet Guard (QWG) — Event Hooks

Status: draft v0.1

This document defines the event-hook model used by **PQC Wallet Guard** to
listen to state transitions inside the Adamantine Wallet.

Event hooks allow QWG to intercept operations, perform PQC checks, apply
risk policies, and return PASS / WARN / BLOCK decisions before a TX or
identity update is executed.

---

## 1. Event Types

### 1.1 Transaction Events
- `on_tx_created`
- `on_tx_signed`
- `on_tx_submitted`
- `on_tx_confirmed`

### 1.2 Identity / Key Events
- `on_identity_generated`
- `on_key_rotation_requested`
- `on_key_rotation_completed`

### 1.3 Guardian Events
- `on_guardian_added`
- `on_guardian_removed`
- `on_guardian_approval_required`

### 1.4 DigiAsset Events
- `on_asset_issued`
- `on_asset_transferred`
- `on_asset_burn_requested`

---

## 2. Hook Response Structure

Each hook returns:

```yaml
decision: PASS | WARN | BLOCK
reason: <string>
policy_ref: <policy-id>
metadata:
  risk_score: <0-100>
  checks: [ ... ]
```

---

## 3. Execution Order

1. Local integrity checks  
2. PQC-container signature verification  
3. Policy evaluation (risk-engine)  
4. Guardian rules (if required)  
5. Final decision returned to wallet UX  

---

## 4. Error Handling

Hooks must fail **closed**, not open:

- If PQC validation cannot complete → BLOCK  
- If risk-engine scores > threshold → WARN or BLOCK  
- If guardian approval missing → BLOCK  

---

## 5. Logging

All hooks emit:

- event type  
- timestamp  
- decision  
- signature container hash  
- risk-score snapshot  

These logs feed the Adaptive Core for future learning.

---

## 6. Future Extensions

- External hook plugins  
- Miner-side validation hooks  
- Advanced anomaly fingerprints  

---
