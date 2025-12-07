
# 🔐 Enigmatic Layer‑0 Integration — Adamantine Wallet (v0.2)
*Location: `modules/enigmatic-chat/docs/integration.md`*  
*Audience: DigiByte Core Developers, Protocol Engineers & Security Architects*  
*Style: Deep Technical, With Diagrams & System Reasoning*

---

# 1. Purpose of This Document
Enigmatic is DigiByte’s **Layer‑0 messaging framework**, created by JohnnyLaw, which encodes intent, metadata, and communication signals **directly into UTXO, fee, topology, and block‑placement planes** — without altering consensus.

Adamantine Wallet v0.2 integrates Enigmatic as:

- a **secure messaging channel**  
- a **transaction‑intent interpreter**  
- a **risk signal provider**  
- a **DigiAssets metadata correlator**  
- a **Guardian scoring input**  

This document defines the **full integration pipeline**, including message validation, threat detection, scoring, and Guardian + Shield interaction.

---

# 2. High-Level System Diagram

```
User
  ↓
UI (Web / iOS / Android)
  ↓
Adamantine Messenger Interface
  ↓
Enigmatic Encoder / Decoder
  ↓
State-Plane Interpreter
  ↓
Guardian Adapter (Enigmatic)
  ↓
Shield Bridge
  ↓
Sentinel / DQSN / ADN / QWG / Adaptive
  ↓
Guardian Verdict
```

Layer‑0 messaging is treated as a **first‑class citizen** in Adamantine’s security model.

---

# 3. Enigmatic Planes and Adamantine Consumption

Enigmatic messages exist across **five state planes**:

1. **Value Plane**  
2. **Fee Plane**  
3. **Cardinality Plane**  
4. **Topology Plane**  
5. **Block Placement Plane**

Adamantine consumes these planes via the Python reference stack provided by JohnnyLaw.

## 3.1 Plane Ingestion Flow

```
Raw TX
  ↓
Enigmatic Decoder
  ↓
Plane Vector Extraction
  ↓
Dialect Interpreter
  ↓
Intent Classification
  ↓
Guardian Adapter
```

The decoding logic lives in:

```
modules/enigmatic-chat/decoder.py
modules/enigmatic-chat/dialect.py
modules/enigmatic-chat/interpreter.py
```

---

# 4. Message Validation Pipeline

Message validation follows a layered approach:

```
Raw TX
  ↓
Plane Structural Validation
  ↓
Dialect Validation
  ↓
Intent Validation
  ↓
Metadata Correlation (optional)
  ↓
Guardian Security Pipeline
```

## 4.1 Structural Validation
Checks:

- correct number of plane entries  
- valid encoding tags  
- size limits  
- UTXO/topology consistency  

If this fails → **Guardian = block**.

---

# 5. Intent Classification

Enigmatic supports different “dialects” for different use cases:

- **Direct Messaging Dialect**
- **DigiAssets Intent Dialect**
- **DD Operational Dialect**
- **Wallet-Internal Signals (opt-in)**

Adamantine classifies every decoded message into **Intent Types**:

```
MESSAGE
ASSET_OP
MINT_REQUEST
BURN_REQUEST
DD_MINT
DD_REDEEM
SYSTEM_SIGNAL
UNKNOWN
```

Unknown intents automatically raise Guardian’s risk scoring.

---

# 6. Threat Detection & Abuse Controls

Enigmatic messages can be abused if not filtered correctly.

Adamantine implements checks for:

### 6.1 Replay Attacks  
Adaptive Core detects repeated messages across blocks.

### 6.2 Flooding / Spam  
Sentinel layer monitors:
- message frequency  
- fee-plane anomalies  
- topology clustering  

### 6.3 Address Manipulation  
If a dialect requires paired metadata and address states, mismatches trigger warnings.

### 6.4 Malformed or Ambiguous Dialects  
Guarded by dialect grammar:

```
If dialect != expected:
  raise ENIGMATIC_DIALECT_ERROR
```

### 6.5 Metadata–Plane Correlation Attacks  
Metadata mismatch with plane hints → **block**.

---

# 7. Guardian Integration

Enigmatic is wired into Guardian through:

```
modules/enigmatic-chat/guardian_adapter.py
modules/enigmatic-chat/guardian-rules.md
core/risk-engine/guardian_adapter.py
```

Guardian receives an **EnigmaticRiskPacket**:

```json
{
  "layer": "enigmatic",
  "dialect": "string",
  "intent_type": "string",
  "confidence": 0.0,
  "anomaly_score": 0.0,
  "metadata_size": 0,
  "pattern_history": "hash"
}
```

Guardian maps this into:

- **risk score**
- **policy rules**
- **lockdown triggers**

---

# 8. Shield Bridge Integration

Enigmatic risk becomes part of the **Shield’s risk map**.

### 8.1 Shield Input

```json
{
  "enigmatic": {
    "dialect": "string",
    "intent_type": "string",
    "anomaly": 0.0,
    "frequency": 0.0,
    "topology_drift": 0.0
  }
}
```

### 8.2 Layer Contributions

- **Sentinel:** mempool drift, spam signals  
- **DQSN:** network-wide opinion on dialect anomalies  
- **ADN:** node health correlation with message timing  
- **QWG:** key posture compared to message pattern  
- **Adaptive:** long-term behavioral memory  

---

# 9. Enigmatic & DigiAssets / DigiDollar (DD)

Enigmatic is **not mandatory** for DigiAssets or DD, but provides:

### 9.1 Layer‑0 channel for:
- mint notifications  
- intent pre-signals  
- governance-style messaging  
- metadata extensions  

### 9.2 Correlation with DigiAssets

```
DigiAssets → OP_RETURN metadata
Enigmatic → State-plane metadata
```

Adamantine cross-checks both:

- mismatch → **warning/block**  
- correlated → **high-confidence flow**  

### 9.3 DD Communications

Enigmatic can optionally broadcast:

- mint proofs  
- stability messages  
- oracle state summaries  

---

# 10. Full End-to-End Flow

```
User message → Enigmatic Encoder → Raw TX
    ↓                 ↓
  Chain              Block
    ↓                 ↓
Enigmatic Decoder → Plane Extraction
    ↓
Dialect Validation
    ↓
Intent Classification
    ↓
Guardian Preflight
    ↓
Shield Multi-Layer Scan
    ↓
Guardian Verdict
    ↓
UI → Display (allow, warn, block)
```

---

# 11. Attack Surfaces & Mitigations

### 11.1 Misdirected Intent
Mitigation:
- dialect grammar validation  
- metadata cross-check  

### 11.2 Fake Identity Signals  
Mitigation:
- Enigmatic identity mapping stored in Adaptive Core  

### 11.3 Spam Flooding  
Mitigation:
- Sentinel mempool model  
- Guardian frequency thresholds  

### 11.4 Malicious Metadata  
Mitigation:
- strict JSON schema  
- OP_RETURN/plane correlation  

### 11.5 Ambiguous Intent Injection  
Mitigation:
- Guardian = block  
- Adaptive memory stores signature  

---

# 12. Developer Notes

- Enigmatic is **optional** at runtime but **deeply integrated** in Adamantine for security benefits.  
- Adamantine does not modify Johnny’s protocol; it **implements a full interpreter** around it.  
- This document should be used alongside JohnnyLaw’s **Enigmatic Spec** for full understanding.

---

# 13. Version

```
Enigmatic Integration Spec Version: v0.2
Compatible with Adamantine Wallet v0.2
```

