# Shield Bridge — QAC API (qac-api.md)

Status: **draft v0.1 – internal skeleton**

This document defines how Adamantine queries the
**Quantum Adaptive Confirmation (QAC)** layer via the Shield Bridge.

QAC analyses confirmation patterns across multiple nodes / regions to
detect **unusual confirmation behaviour** that might signal advanced
attacks or partial forks.

---

## 1. Purpose

Guardian & Risk Engine need a **smarter notion of confirmation** than
“number of blocks” only.

QAC tells us:

- how “healthy” confirmations are for a given TX,
- whether some regions / nodes disagree,
- whether confirmation timing looks abnormal.

---

## 2. Endpoint: /v1/tx-confirmation

```http
GET /v1/tx-confirmation?txid={txid}
```

### Example Response

```json
{
  "txid": "abc123...",
  "seen_by_nodes": 18,
  "first_seen_at": "2025-12-02T13:00:00Z",
  "confirmations": 3,

  "confidence": {
    "level": "high",         
    "score": 0.96,
    "reasons": [
      "broad_node_agreement",
      "normal_confirmation_timing"
    ]
  },

  "disagreement": {
    "has_disagreement": false,
    "disagreement_score": 0.0
  },

  "timing": {
    "expected_confirmation_time_s": 600,
    "actual_first_confirmation_time_s": 580,
    "timing_anomaly_score": 0.05
  },

  "timestamp": "2025-12-02T13:35:00Z"
}
```

Key fields for Guardian:

- `confidence.level`  – `"low" | "medium" | "high"`
- `disagreement.has_disagreement`
- `timing.timing_anomaly_score`

QAC can also be used for **inbound** TXs (incoming payments) to decide
when to show them as “safe” in UI.

---

## 3. Endpoint: /v1/batch-tx-confirmation (optional)

For performance, the wallet may query multiple TXs at once:

```http
POST /v1/batch-tx-confirmation
Content-Type: application/json
```

```json
{
  "txids": ["abc123...", "def456...", "ghi789..."]
}
```

```json
{
  "results": [
    { "txid": "abc123...", "confidence": { "level": "high" } },
    { "txid": "def456...", "confidence": { "level": "medium" } },
    { "txid": "ghi789...", "confidence": { "level": "low" } }
  ]
}
```

---

## 4. Degraded Behaviour

When QAC is unavailable:

- Wallet falls back to standard confirmation logic (block count only).
- Guardian may:
  - delay treating large incoming payments as fully safe,
  - treat some outbound flows as slightly higher risk.

Exact scoring rules are in `risk-engine/scoring-rules.md`.
