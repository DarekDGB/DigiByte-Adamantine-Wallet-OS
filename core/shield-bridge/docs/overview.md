
# 🌉 Shield Bridge — Master Specification (v0.2)
*Location: `core/shield-bridge/docs/overview.md`*  
*Audience: DigiByte Core Developers, Node Operators, Security Architects*  

Shield Bridge is the **coordination layer** that connects Adamantine’s wallet, Guardian, and Risk Engine to the **5-layer DigiByte Quantum Shield Network**:

- Sentinel AI v2  
- DQSN v2 (DigiByte Quantum Shield Network)  
- ADN v2 (Autonomous Defense Node)  
- QWG (Quantum Wallet Guard)  
- Adaptive Core  

It is responsible for transporting **normalized risk packets**, aggregating responses, and exposing a **stable API** to the rest of Adamantine.

---

## 1. Design Principles

Shield Bridge is designed to be:

1. **Stateless** — it does not persist business state itself; it only routes and aggregates.
2. **Pluggable** — individual layers (Sentinel, DQSN, ADN, QWG, Adaptive) can be turned on/off.
3. **Deterministic** — same inputs must result in same aggregated risk output.
4. **Transport-Agnostic** — can run in-process, over IPC, HTTP, gRPC, or any other mechanism.
5. **Observable** — all requests + responses are traceable for debugging and audits.

---

## 2. Repository Layout

In Adamantine:

```text
core/shield-bridge/
  accounts.py
  node_manager.py
  transactions.py
  tx_builders.py
  wallet_service.py        # high-level entrypoints
  # Docs:
  docs/
    overview.md            ← (this file)
    dqsn-api.md            # DQSN interface
    sentinel-api.md        # Sentinel interface (future)
    adn-api.md             # ADN interface (future)
    qwg-api.md             # Quantum Wallet Guard interface (future)
    adaptive-api.md        # Adaptive Core hints interface (future)
```

> Note: file names may differ slightly in implementation; this spec defines the intended structure.

---

## 3. Core Concepts

### 3.1 Risk Packet

The fundamental unit of communication is the **RiskPacket**:

```json
{
  "packet_id": "uuid",
  "wallet_id": "string",
  "account_id": "string",
  "flow_type": "TRANSFER | MINT | BURN | MESSAGE | NODE_OP",
  "amount_sats": 0,
  "asset_id": "string | null",
  "metadata_size": 0,
  "client": "web | ios | android | service",
  "context": {
    "geo_hint": "string | null",
    "device_fingerprint": "string | null"
  },
  "layer_payloads": {
    "digiassets": {},
    "dd": {},
    "enigmatic": {},
    "node": {}
  }
}
```

Shield Bridge sends this RiskPacket (or projections of it) to each layer.

---

### 3.2 Layer Result

Each layer returns a **LayerResult**:

```json
{
  "layer": "sentinel | dqsn | adn | qwg | adaptive",
  "risk_score": 0.0,
  "signals": {
    "flags": [],
    "metrics": {}
  }
}
```

---

### 3.3 Aggregated Result

Shield Bridge aggregates all LayerResult objects into a **RiskMap**:

```json
{
  "packet_id": "uuid",
  "results": [
    { "layer": "sentinel", "risk_score": 0.10 },
    { "layer": "dqsn", "risk_score": 0.45 },
    { "layer": "adn", "risk_score": 0.20 },
    { "layer": "qwg", "risk_score": 0.05 },
    { "layer": "adaptive", "risk_score": 0.30 }
  ]
}
```

This RiskMap is consumed by Guardian + Risk Engine.

---

## 4. Request Flow

### 4.1 Sequence Diagram (Simplified)

```text
Guardian → Shield Bridge → Sentinel
                          → DQSN
                          → ADN
                          → QWG
                          → Adaptive
           ← RiskMap  ←←←←←←←←←←←
```

Steps:

1. Guardian constructs a RiskPacket.
2. Shield Bridge fans out to configured layers.
3. Each layer returns a LayerResult.
4. Shield Bridge aggregates into a RiskMap.
5. RiskMap returned to Guardian / Risk Engine.

---

## 5. DQSN Integration (Example Layer)

DQSN v2 is the **network health & safety layer**.  
The DQSN interface is fully documented in `dqsn-api.md`.

From Shield Bridge’s perspective:

- Inputs: TX shape, confirmation expectations, reorg risk, multi-node views.
- Outputs: score representing **network disagreement / reorg likelihood**.

Example DQSN request excerpt:

```json
{
  "context": {
    "height": 1234567,
    "expected_confirmations": 2
  },
  "tx_shape": {
    "inputs": 2,
    "outputs": 3,
    "has_op_return": true
  }
}
```

---

## 6. Sentinel Integration

Sentinel monitors:

- mempool anomalies  
- fee-plane behavior  
- transaction clustering  

Shield Bridge sends:

- TX fee rate  
- mempool snapshot hints  
- broadcast timing  

Sentinel returns:

- short-term mempool risk score  
- spam likelihood  
- sudden topology shifts  

---

## 7. ADN Integration

ADN (Autonomous Defense Node) provides:

- node-local reflexes  
- chain reorg awareness  
- lockdown state  

Shield Bridge queries ADN for:

- current node health (sync, peers, bans)  
- reorg history  
- quarantine mode  

If ADN enters **lockdown**, Shield Bridge marks:

```json
{ "layer": "adn", "risk_score": 1.0 }
```

This usually pushes Guardian to `LOCKDOWN`.

---

## 8. QWG Integration

QWG (Quantum Wallet Guard) focuses on:

- key posture  
- PQC migration state  
- suspicious signing patterns  

Shield Bridge sends:

- key id  
- signing history hints  
- whether the transaction uses legacy or PQC containers  

QWG returns:

- risk score for key compromise or quantum exposure  
- migration recommendations  

---

## 9. Adaptive Core Integration

Adaptive Core gives **behavioral context**:

- stability index  
- recent incident history  
- profile-level risk hints  

Shield Bridge can either:

- request Adaptive directly, or  
- receive Adaptive-derived weights via Risk Engine.

In v0.2, Adaptive is usually accessed by Risk Engine, but this doc leaves room for Shield → Adaptive direct calls.

---

## 10. Error Handling

If a layer is unavailable:

- Shield marks that layer as `status: "unreachable"`  
- Risk Engine may reduce the weight of that layer for this packet  
- Guardian is informed via “degraded mode” flag  

Example:

```json
{
  "layer": "sentinel",
  "status": "unreachable",
  "risk_score": 0.0
}
```

No transaction is automatically blocked solely due to one layer being offline—policy decides.

---

## 11. Configuration

Example YAML:

```yaml
shield_bridge:
  enabled_layers:
    sentinel: true
    dqsn: true
    adn: true
    qwg: true
    adaptive: true
  timeouts_ms:
    per_layer: 800
    overall: 2500
  retries:
    enabled: true
    max_attempts: 2
```

---

## 12. Extensibility

New layers may be added in future (e.g., **oracle-layer**, **governance-layer**).  
Requirements:

1. Implement a Layer Adapter (request/response normalization).
2. Register adapter in Shield Bridge configuration.
3. Provide documentation similar to `dqsn-api.md`.

---

## 13. Security & Privacy

- Shield Bridge transports **risk metadata only**, not private keys.
- IPs / geolocation hints must be handled per local privacy regulations.
- Debug logging should redact sensitive context fields.

---

## 14. Version

```
Shield Bridge Master Spec Version: v0.2
Compatible with Adamantine v0.2
```

---

## 15. Summary

Shield Bridge is the **nervous system bus** of Adamantine:

- connects Guardian/Risk Engine with Sentinel, DQSN, ADN, QWG, Adaptive  
- normalizes risk signals  
- aggregates them into a RiskMap  
- provides an extensible and observable interface  

This document serves as the blueprint for all Shield Bridge implementations within the DigiByte Adamantine ecosystem.
