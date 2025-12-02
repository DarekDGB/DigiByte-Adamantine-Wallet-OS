# Shield Bridge — DQSN API (dqsn-api.md)

Status: **draft v0.1 – internal skeleton**

This document defines how Adamantine talks to the **DigiByte Quantum
Shield Network (DQSN)** via the Shield Bridge.

DQSN is the **node / network health & diversity layer**. It provides
Adamantine with a view of:

- which nodes are healthy,
- which peers are suspicious,
- whether the wallet is seeing a consistent view of the chain.

---

## 1. Purpose

Guardian & Risk Engine need to know:

- is the current node safe enough to trust?
- do we see agreement across multiple independent nodes?
- are there signs of eclipse / partition attacks?

DQSN exposes this as a set of **summaries and recommendations**.

---

## 2. Endpoint: /v1/node-summary

```http
GET /v1/node-summary
```

### Example Response

```json
{
  "local_node": {
    "address": "127.0.0.1:12024",
    "reachable": true,
    "protocol_version": 80021,
    "subversion": "/DigiByte:8.22.0/",
    "latency_ms": 45,
    "height": 17500000,
    "is_synced": true,
    "ban_score": 0
  },
  "cluster_view": {
    "consensus_height": 17500000,
    "height_disagreement": "low",       
    "avg_latency_ms": 120,
    "node_count": 7,
    "fork_suspicion": "none"            
  },
  "recommendation": {
    "status": "healthy",                 
    "notes": [
      "local_node_within_cluster_height",
      "no_major_fork_detected"
    ]
  },
  "timestamp": "2025-12-02T13:20:00Z"
}
```

Key fields for Guardian:

- `recommendation.status` – `"healthy" | "warning" | "unsafe"`
- `cluster_view.fork_suspicion`
- `height_disagreement`

---

## 3. Endpoint: /v1/node-list

Optional endpoint to get a **diverse set of candidate nodes**.

```http
GET /v1/node-list
```

```json
{
  "nodes": [
    {
      "address": "node1.dgb.example:12024",
      "latency_ms": 90,
      "score": 0.95,
      "tags": ["geo-eu", "community"]
    },
    {
      "address": "node2.dgb.example:12024",
      "latency_ms": 150,
      "score": 0.92,
      "tags": ["geo-us", "community"]
    }
  ]
}
```

Adamantine may use this to:

- auto-select healthy nodes,
- offer suggestions to the user in node settings,
- cross-check views from multiple nodes.

---

## 4. Endpoint: /v1/health-check

Lightweight probe used by the wallet for periodic health checks.

```http
GET /v1/health-check
```

```json
{
  "status": "ok",
  "uptime_seconds": 7200,
  "last_cluster_refresh": "2025-12-02T13:18:00Z"
}
```

If this times out, Shield Bridge marks DQSN as `"offline"` and Risk
Engine adjusts scoring accordingly.

---

## 5. Degraded Behaviour

When DQSN is `"offline"` or `"unsafe"`:

- Guardian should be more cautious about:
  - large sends,
  - DD operations,
  - interpreting height / confirmation counts.
- The wallet UI may:
  - warn the user about node health,
  - suggest switching to other nodes,
  - show a “Network Health: Degraded” banner.

Exact risk scoring details live in `risk-engine/scoring-rules.md`.
