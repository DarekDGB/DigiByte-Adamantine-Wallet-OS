
# 🛡 Guardian + Risk Engine — Deep Integration Specification (v0.2)
*Location: `core/guardian/docs/integration.md`*  
*Audience: DigiByte Core Developers, Security Architects & Wallet Engineers*  
*Style: Deep Technical, With Scoring Models, Diagrams & System Reasoning*

---

# 1. Purpose of This Document

This document defines **how Guardian Wallet**, the **Risk Engine**, and the **5-Layer Quantum Shield** integrate to protect:

- DigiAssets  
- DigiDollar (DD)  
- Enigmatic Layer-0 messages  
- Standard DigiByte transactions  
- All user signing operations inside Adamantine Wallet  

Together they form a **zero-trust behavioral security framework**.

This is the *core* of Adamantine’s defense architecture.

---

# 2. High-Level System Diagram

```
User Intent
   ↓
Guardian Preflight
   ↓
Risk Engine (scoring + thresholds)
   ↓
Shield Bridge (multi-layer risk map)
   ↓
Sentinel / DQSN / ADN / QWG / Adaptive
   ↓
Guardian Postflight → Verdict
   ↓
Wallet Signing Layer
   ↓
Node Adapter (broadcast)
```

Guardian sits between **every transaction** and the **signing layer**.  
Nothing bypasses it.

---

# 3. Guardian Core Responsibilities

Guardian’s architecture is built around four pillars:

### ✔ 1. **Policy Enforcement**
Rules derived from:
- user configuration  
- engine defaults  
- per-asset rules  
- DD rulesets  
- Enigmatic messaging policies  

### ✔ 2. **Risk Scoring**
Executed by the Risk Engine:
- per-layer scoring  
- weighted aggregation  
- threshold interpretation  

### ✔ 3. **Contextual Behavior Analysis**
Guardian tracks:
- user patterns  
- device  
- location  
- time  
- asset-specific habits  

### ✔ 4. **Decision Authority**
Guardian returns:
- **ALLOW**  
- **WARN**  
- **BLOCK**  
- **LOCKDOWN**  

This decision is final.

---

# 4. Risk Engine — Architecture

Risk Engine is located under:

```
core/risk-engine/
  risk_engine.py
  scoring-rules.md
  guardian-thresholds.md
  inputs.md
```

It performs:

- **Risk normalization**
- **Layer scoring**
- **Weighted aggregation**
- **Threshold evaluation**

---

# 5. Risk Data Sources

Risk Engine consumes inputs from five classes:

### 1. **Transaction Inputs (Local)**
From Guardian:
- amount  
- change behavior  
- address novelty  
- velocity  
- patterns  

### 2. **Node State**
From Node Adapter:
- reorg signals  
- mempool health  
- node sync status  
- peer drift  

### 3. **Shield Layers (Network & Behavior)**

**Sentinel** → mempool anomalies  
**DQSN** → cross-node view consistency  
**ADN** → node reflex & lockdown  
**QWG** → key integrity & PQC posture  
**Adaptive** → long-term behavioral profile

### 4. **Asset Context**
From DigiAssets/DD Engine:
- metadata risk  
- rule violations  
- asset-specific limits  

### 5. **Enigmatic Context**
From L0 messaging engine:
- dialect classification  
- message frequency  
- intent ambiguity  
- topology inconsistencies  

---

# 6. Weighted Aggregation Model

Final risk score formula:

```
score =
  W_sentinel  * sentinel_score  +
  W_dqsn      * dqsn_score      +
  W_adn       * adn_score       +
  W_qwg       * qwg_score       +
  W_adaptive  * adaptive_score  +
  W_local     * local_score
```

Weights are defined in `scoring-rules.md`.

---

# 7. Threshold Definition

Thresholds from `guardian-thresholds.md`:

```
0.00–0.25 → ALLOW
0.25–0.50 → WARN
0.50–0.75 → BLOCK
0.75–1.00 → LOCKDOWN
```

LOCKDOWN is reserved for:
- multi-layer consensus disagreement  
- quantum risk  
- extreme node instability  
- malicious behavior patterns  

---

# 8. Guardian Workflow

## 8.1 Preflight

```
User Intent
   ↓
Guardian validates:
- policy
- inputs
- velocity
- patterns
- asset rules
   ↓
Risk Engine Preflight Score
   ↓
Shield Bridge Preflight Request
```

---

## 8.2 Shield Processing

ASCII diagram:

```
Shield Bridge
   ↓
+------------+------------+------------+------------+------------+
| Sentinel   |   DQSN     |    ADN     |    QWG     |  Adaptive  |
+------------+------------+------------+------------+------------+
   ↓              ↓             ↓            ↓            ↓
  Risk         Risk           Risk         Risk         Risk
  Value        Value          Value        Value        Value
```

Shield aggregates into a single map:

```json
{
  "sentinel": 0.10,
  "dqsn": 0.60,
  "adn": 0.20,
  "qwg": 0.30,
  "adaptive": 0.40
}
```

---

## 8.3 Postflight

Guardian:

- merges Shield scores  
- re-evaluates policy  
- checks behavior profile  
- compares against thresholds  

Returns final verdict.

---

# 9. Guardian Adapter Implementation

Guardian Adapter lives in:

```
core/risk-engine/guardian_adapter.py
modules/*/guardian_bridge.py
```

It transforms:

- Transacton models  
- DigiAssets/ DD intents  
- Enigmatic intents  

into one unified **GuardianContext**:

```json
{
  "flow": "transfer",
  "asset_id": "dgb_asset_xyz",
  "amount": 5000,
  "metadata_size": 82,
  "client": "ios",
  "geo": "uk",
  "velocity": 3,
  "behaviour_hash": "aa39c0…"
}
```

---

# 10. Guardian Lockdown Behavior

Lockdown triggered when:

- **adn_score >= 0.75** or  
- **dqsn_score >= 0.80** or  
- **qwg_score >= 0.85** or  
- **final_score >= 0.75**  

During lockdown:

- all TX blocked  
- signing disabled  
- user warned  
- system enters “restricted mode”  
- Adaptive Core logs event for memory  

---

# 11. Adaptive Core Integration

Adaptive layer provides:

- long-term patterns  
- identity correlation  
- threshold adjustments  
- anomaly memory  

It modifies weights dynamically:

```
If behavior is stable → reduce W_adaptive
If behavior is erratic → increase W_adaptive
```

Adaptive Core is the **immune memory** of Adamantine.

---

# 12. Developer Notes

- Guardian MUST be called before **every** signing action.  
- Guardian does NOT rely on trust — it enforces policy regardless of context.  
- Shield MUST be queried for all DigiAssets, DD, and Enigmatic flows.  

---

# 13. Version

```
Guardian Integration Spec Version: v0.2
Risk Engine Spec Version: v0.2
```

