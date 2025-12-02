# Shield Bridge — Sentinel API (sentinel-api.md)

Status: **draft v0.1 – internal skeleton**

This document defines how the Adamantine Wallet talks to the **Sentinel AI v2**
monitoring layer through the Shield Bridge.

Sentinel provides a **read-only, external telemetry view** of the DigiByte
network and mempool. Adamantine never controls Sentinel; it only **queries
summaries and feeds events**.

---

## 1. Purpose

Guardian / Risk Engine need a compact view of:

- chain stability
- mempool health
- fee environment
- visible reorg patterns
- anomaly scores

Sentinel already computes this. The Sentinel API defines a **thin JSON
interface** to consume it from the wallet.

---

## 2. Transport & Auth (Conceptual)

Exact transport is implementation-dependent, but recommended defaults:

- Protocol: HTTPS (or WSS for streaming)
- Format: JSON
- Auth: 
  - optional API key for public instances, or
  - local-only (localhost / LAN) without auth for self-hosted nodes.

Adamantine should support **multiple Sentinel endpoints** via
`config/shield-endpoints.yml`.

---

## 3. Endpoint: /v1/summary

Returns a compact snapshot of current network + mempool health.

```http
GET /v1/summary
```

### 3.1 Response (example)

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
    "top_signals": [
      "normal_activity"
    ]
  },
  "timestamp": "2025-12-02T13:11:00Z"
}
```

Guardian / Risk Engine primarily care about:

- `network.reorg_risk`
- `mempool.fee_environment`
- `anomaly.level`

---

## 4. Endpoint: /v1/tx-context

Returns Sentinel’s view of **a specific TX** (or a proposed TX template).

```http
POST /v1/tx-context
Content-Type: application/json
```

### Request

```json
{
  "chain": "DGB-mainnet",
  "raw_tx_hex": "0200000001...",
  "hint_amount_sats": 150000000,
  "hint_destination_addresses": ["Dabcd...", "Dxyz..."]
}
```

- `raw_tx_hex` MAY be omitted for privacy; in that case, only hints are used.

### Response (example)

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

Guardian can combine this with local contact info and shield data from
other layers to derive a final verdict.

---

## 5. Endpoint: /v1/events

Adamantine MAY (optionally) push anonymised events to Sentinel to enrich
global anomaly detection, e.g.:

```http
POST /v1/events
Content-Type: application/json
```

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

This is entirely optional and must follow the privacy rules defined in
`modules/analytics-telemetry/privacy-model.md`.

---

## 6. Degraded Behaviour

When `/v1/summary` or `/v1/tx-context` are unreachable:

- Shield Bridge marks Sentinel status as `"offline"` or `"degraded"`.
- Risk Engine treats Sentinel data as **missing** and degrades safely:
  - assume at least `"unknown"` risk, never blindly `"low"`.
  - adjust Guardian policies according to `risk-engine/scoring-rules.md`.

The wallet must remain functional but more conservative in decisions.
