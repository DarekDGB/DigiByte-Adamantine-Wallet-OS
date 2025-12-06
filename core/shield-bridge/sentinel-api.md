# 🛡️ Shield Bridge — Sentinel API  
### *Adamantine Wallet → Sentinel AI v2 Telemetry Interface*  
**Status:** v0.2 – Internal Architecture Specification  
**Author:** @Darek_DGB — MIT Licensed  

---

Sentinel AI v2 is the **Layer-1 telemetry intelligence** of the DigiByte
Quantum Shield Network.  
It provides **external, read-only, real-time analytics** about:

- chain stability  
- mempool conditions  
- reorg signals  
- anomaly detection  
- fee environment trends  

The Adamantine Wallet **never controls Sentinel** — it only *queries*
Sentinel through the Shield Bridge.

This document defines the wallet-facing **Sentinel API contract** used by:

- Guardian Wallet  
- Risk Engine  
- QWG (Quantum Wallet Guard)  
- Adaptive Core scoring  

---

# 1. Purpose of This API

Adamantine requires a compact, trusted summary of the DigiByte environment to
support the following behaviours:

### ✔ Guardian preflight checks  
### ✔ Risk engine scoring  
### ✔ Fee recommendations  
### ✔ Transaction-context risk analysis  
### ✔ Anomaly correlation across layers

Sentinel AI already computes these metrics.  
The Shield Bridge exposes them in a **thin JSON interface**, optimised for:

- low overhead  
- mobile performance  
- multi-Sentinel redundancy  
- offline-safe degradation  

---

# 2. Transport & Authentication (Conceptual Layer)

Implementation may vary per platform, but recommended defaults:

| Component | Recommendation |
|----------|----------------|
| Protocol | HTTPS (REST) or WSS (streaming) |
| Format   | JSON (UTF-8) |
| Auth     | optional API key (public nodes), or local-only for self-hosted |

Adamantine supports **multiple Sentinel endpoints** configured in:

```
config/shield-endpoints.yml
```

Example:

```yaml
sentinel:
  endpoints:
    - https://sentinel1.dgbsystems.com
    - https://sentinel.local
  timeout_ms: 1700
  fallback_strategy: "round-robin"
```

---

# 3. Endpoint — `/v1/summary`  
### *Global Network & Mempool Snapshot*

```
GET /v1/summary
```

### 3.1 Response Example

```json
{
  "network": {
    "chain": "DGB-mainnet",
    "height": 17500000,
    "best_block_hash": "abc123...",
    "reorg_risk": "low",
    "reorg_score": 0.02,
    "last_reorg_depth": 1,
    "last_reorg_at": "2025-12-02T13:10:00Z"
  },
  "mempool": {
    "tx_count": 1234,
    "estimated_blocks_to_clear": 2,
    "fee_environment": "normal",
    "min_fee_sats_per_byte": 1,
    "median_fee_sats_per_byte": 3,
    "high_fee_sats_per_byte": 10
  },
  "anomaly": {
    "score": 0.08,
    "level": "low",
    "top_signals": ["normal_activity"]
  },
  "timestamp": "2025-12-02T13:11:00Z"
}
```

### 3.2 Consumers Inside Adamantine

| Component | Uses |
|----------|------|
| **Risk Engine** | anomaly.level, reorg risk, mempool environment |
| **Guardian Wallet** | preflight policy gates |
| **QWG** | recalibrate local heuristics |
| **Adaptive Core** | combine with internal scoring vectors |

**Minimum fields required by wallet logic:**

- `network.reorg_risk`
- `mempool.fee_environment`
- `anomaly.level`

---

# 4. Endpoint — `/v1/tx-context`  
### *Evaluate a Proposed or Finalised Transaction*

```
POST /v1/tx-context
Content-Type: application/json
```

### Request Body

```json
{
  "chain": "DGB-mainnet",
  "raw_tx_hex": "0200000001...",
  "hint_amount_sats": 150000000,
  "hint_destination_addresses": ["Dabcd...", "Dxyz..."]
}
```

Notes:

- `raw_tx_hex` **may be omitted** to protect privacy.
- If omitted, Sentinel uses heuristics & hints only.

### Response Example

```json
{
  "tx_risk": {
    "level": "low",
    "score": 0.1,
    "reasons": [
      "fee_within_normal_range",
      "no_known_bad_addresses"
    ]
  },
  "fee_assessment": {
    "sats_per_byte": 4,
    "classification": "normal"
  },
  "address_flags": [
    {
      "address": "Dabcd...",
      "label": "exchange",
      "risk_hint": "medium"
    }
  ],
  "timestamp": "2025-12-02T13:12:00Z"
}
```

### Consumers

- Guardian uses `tx_risk.level` + internal rules → allow / require approval / block  
- Risk Engine uses deeper scoring → anomaly reinforcement  
- QWG uses fee + address patterns for malicious behaviour detection  

---

# 5. Endpoint — `/v1/events` (Optional)  
### *Send anonymised local events to Sentinel AI v2*

This endpoint lets Adamantine contribute **privacy-preserving signals** to the
global anomaly model.

```
POST /v1/events
Content-Type: application/json
```

### Example

```json
{
  "client": "adamantine-wallet",
  "version": "0.1.0",
  "device_fingerprint": "hashed-or-omitted",
  "events": [
    {
      "kind": "guardian-verdict",
      "timestamp": "2025-12-02T13:13:00Z",
      "risk_level": "high",
      "action": "block-and-alert",
      "context_hash": "abc123"
    }
  ]
}
```

### Privacy Requirements

Must comply with:

```
modules/analytics-telemetry/privacy-model.md
```

No personal identifiers.  
No raw addresses without hashing.  
Device fingerprints must be **hashed or omitted**.

---

# 6. Degraded Behaviour (Offline Mode)

If `/v1/summary` or `/v1/tx-context` fails:

- Shield Bridge marks Sentinel as:  

  - `"offline"`  
  - `"unreachable"`  
  - `"degraded"`  

- Risk Engine applies **conservative fallback rules**, e.g.:

### Fallback Logic

| Missing Data | Safe Behaviour |
|--------------|----------------|
| reorg signals | assume `"unknown"` risk |
| mempool environment | assume `"volatile"` |
| tx risk context | assume `"needs_review"` |
| anomaly scores | assume `"medium"` |

Wallet remains fully functional **but never over-confident**.

Guardian rules MUST degrade safely according to:

```
core/risk-engine/scoring-rules.md
```

---

# 7. Future Extensions (Reserved)

| Future Feature | Purpose |
|----------------|---------|
| `/v1/live-stream` | WebSocket real-time feed |
| `/v1/metrics/*` | richer scoring vectors |
| `/v1/signal-packets` | compressed event batches for Adaptive Core |
| `/v1/topology` | network-wide behavioural topology maps |

These are reserved and will be defined in the next architecture phase.

---

# 8. License

```
MIT License — by @Darek_DGB
```

---

# 9. Changelog

| Version | Changes |
|---------|---------|
| v0.2 | Full rewrite, unified with QAC, ADN, DQSN, Adaptive Core API docs |
| v0.1 | Initial placeholder skeleton |

---

**End of Specification – Sentinel API v0.2**  
**Shield Bridge — DigiByte Adamantine Wallet**  
