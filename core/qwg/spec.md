# PQC Wallet Guard (QWG) — Specification

Status: draft v0.1

QWG is the cryptographic validation layer that protects all outgoing
operations inside the Adamantine Wallet using **post-quantum containers**
(PQC Containers).  
It ensures that every signature, message, asset, and identity update is
wrapped in PQ-safe metadata.

---

## 1. Goals

- Provide quantum-resistant signing containers  
- Enforce deterministic wallet-side validation  
- Integrate with Guardian approvals  
- Serve as a pre-flight firewall for the risk-engine  
- Produce structured logs for the Adaptive Core  

---

## 2. Architecture

```
┌──────────────────────┐
│   Wallet Operation    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   QWG Validation     │
│  - PQC Container     │
│  - Event Hooks       │
│  - Policy Binding    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Risk Engine        │
└──────────────────────┘
```

---

## 3. PQC Containers

Each TX or identity change is wrapped in:

```yaml
container:
  version: 1
  pq_sig: <bytes>        # Dilithium/Falcon placeholder
  metadata:
    entropy_fingerprint: <hash>
    key_epoch: <uint>
    wallet_id: <uuid>
```

---

## 4. Validation Steps

1. Verify PQ signature  
2. Verify entropy-fingerprint  
3. Rebuild expected container locally  
4. Compare hashes  
5. Pass to risk-engine  

If any mismatch → BLOCK.

---

## 5. Integration Points

- Send flow  
- DigiAsset mint/transfer  
- Identity updates  
- Guardian approvals  
- Enigmatic messaging  

---

## 6. Outputs

QWG produces:

- structural validation result  
- PQC container hash  
- entropy score  
- anomaly markers  
- recommended action (PASS/WARN/BLOCK)  

---
