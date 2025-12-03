# Adamantine Wallet — Risk Model (v0.1)

## 1. Purpose

This document defines the end‑to‑end risk model for the DigiByte Adamantine Wallet, covering:
- on‑chain risks  
- off‑chain risks  
- wallet‑layer risks  
- protocol‑layer risks  
- DigiByte Quantum Shield Network (DQSN) interactions  
- DigiAssets & DigiDollar compliance requirements  
- Enigmatic Layer‑0 signalling risks  
- user‑side and operational risks  

It guides testing, audits, and future improvements.

---

## 2. Threat Surfaces

### 2.1 On‑Chain Threats
| Threat | Description | Mitigation |
|-------|-------------|------------|
| Reorgs | Small reorganizations affecting confirmation ordering | Sentinel AI v2 monitoring + Adaptive Core |
| Malleability vectors | Transaction form mutations | Strict tx-builder rules |
| Fee-manipulation patterns | Spam or timing manipulation | Shield risk engine scoring |

---

## 3. Wallet‑Layer Threats

### 3.1 Key Material Exposure
- Private key leaks  
- Backup mismanagement  
- Malware harvesting  

**Mitigation:**  
- Secure enclave / KeyStore storage  
- Optional hardware‑wallet mode  
- Encrypted mnemonic backup  
- PQC‑ready upgrade path

### 3.2 Transaction Construction Threats
- Wrong fee-selection  
- Wrong UTXO-selection  
- Replay-pattern detectability  

**Mitigation:**  
- Deterministic builder  
- Adaptive heuristics  
- Shield-engine policy scoring  

---

## 4. DigiAssets Threats

### 4.1 Asset Script Formation
Risks: malformed scripts, loss of asset state, ambiguous interpretation.

Mitigation:
- Strict DigiAssets v3 parser  
- Offline simulation before broadcast  
- Enigmatic signalling to check asset state transitions  

### 4.2 Indexer Dependency
If indexers disagree, wallet state diverges.

Mitigation:
- Multi-indexer quorum (3‑source confirmation)  
- Automatic fallback logic  
- Alerts to Sentinel UI  

---

## 5. DigiDollar Threats

### 5.1 Mint/Burn Logic
Risks:
- Over‑mint  
- Under‑collateralized mint  
- Frozen workflows  

Mitigation:
- On‑chain proofs  
- PQ-safe verification  
- Shield rule-engine scoring  

### 5.2 Stable pegging
External price oracle deviation.

Mitigation:
- Multi‑feed aggregation  
- Drift detection (Sentinel AI v2)  

---

## 6. Enigmatic Layer‑0 Signalling Risks

### 6.1 Detectability Surface
Risk: adversaries fingerprint signalling patterns.

Mitigation:
- Dialect rotation  
- Fee jitter bands  
- Cardinality variation  
- Optional OP_RETURN deniability  

### 6.2 Planner Misalignment
Planner insufficient UTXOs → failed frames.

Mitigation:
- Pre-flight planner simulation  
- Dry-run enforcement  
- Adaptive suggestion engine  

---

## 7. DQSN (Shield) Interaction Risks

### 7.1 Adaptive Core Mistuning
False positives or false negatives.

Mitigation:
- Training windows  
- Multi-signal scoring  
- Reversion safety  

### 7.2 Layer-crossing feedback loops
If Sentinel, Core, and ADN overreact.

Mitigation:
- Rate-limiters  
- Trust-weight smoothing  
- Human override mode  

---

## 8. User-Side Risks

- Lost seed phrase  
- Phishing  
- Insecure devices  
- Outdated OS  
- Bad extensions / malware  

Mitigation:
- Training tips  
- Local device scans  
- Security checklist  
- Push warnings  

---

## 9. Overall Risk Heatmap  
(Pending release v0.2)

High | Medium | Low  
---- | ------ | ----  
DigiAssets script errors | Oracle drift | UI risks  
Enigmatic detectability | Fee front-running | Reorgs under 2 blocks  

---

## 10. Audit Requirements
- Quarterly internal audit  
- Annual external audit  
- PQC migration readiness review  
- Multi-indexer correctness audits  

---

## 11. Status
Draft v0.1 — Architecture‑aligned placeholder for full modeling in v0.2.
