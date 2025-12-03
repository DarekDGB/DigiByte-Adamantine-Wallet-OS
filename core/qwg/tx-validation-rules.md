# PQC Wallet Guard — Transaction Validation Rules

Status: draft v0.1

This document defines the deterministic rule set applied by QWG during
transaction creation, signing, and submission.

These rules are executed **before** touching the network or Guardian layer.

---

## 1. Transaction Structure Rules

- TX must contain at least 1 input  
- All inputs must reference confirmed UTXOs  
- Change address must belong to local wallet  
- Fee must meet DigiByte relay minimum  
- No future locktime beyond allowed threshold  

---

## 2. PQC Requirements

Every TX must include:

```yaml
pqc_container:
  pq_sig: required
  key_epoch: required
  entropy_fingerprint: required
```

Missing ANY → BLOCK.

---

## 3. Risk-Engine Bound Rules

Risk policies may enforce:

- max amount per TX  
- whitelist-only recipients  
- shielded approval required  
- multi-sig guardian path  

If policies fail → BLOCK.

---

## 4. DigiAsset-Specific Rules

When asset metadata is attached:

- asset ID must be valid  
- amount must respect supply constraints  
- issuer rules must match configuration  
- burn request must include guardian-approval  

---

## 5. Output Sanitization

The final TX must pass:

- deterministic re-serialization check  
- byte-for-byte match against wallet expectations  
- container hash consistency check  

---

## 6. Failure Modes

If ANY validation step fails:

```
decision: BLOCK
reason: <validation failure>
```

Wallet UI MUST show red warning with risk explanation.

---
