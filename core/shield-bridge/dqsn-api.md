# Shield Bridge — DQSN API (dqsn-api.md)

Status: **draft v0.2 – aligned with ShieldBridgeClient**

This document defines how the Adamantine Wallet talks to the  
**DigiByte Quantum Shield Network (DQSN)** via the **Shield Bridge**.

DQSN is the **Layer 2 – node / network health & diversity layer** of the
DigiByte Quantum Shield Network. It provides Adamantine with a view of:

- which nodes are healthy,
- which peers are suspicious,
- whether the wallet is seeing a consistent view of the chain.

Adamantine never calls DQSN directly. All calls flow through:

- `core/shield_bridge_client.py`  → HTTP / gRPC to DQSN gateway
- `core/node_manager.py`          → local node selection / failover

---

## 1. Purpose

Guardian & Risk Engine need to know:

- is the current node safe enough to trust?
- do we see agreement across multiple independent nodes?
- are there signs of eclipse / partition attacks?
- should we suggest a different node or fail closed for large actions?

DQSN exposes this as a set of **summaries and recommendations** that the
Shield Bridge presents as a **thin JSON API**.

---

## 2. Transport & Auth (conceptual)

Implementation details can vary by deployment, but recommended defaults:

- Protocol: HTTPS or gRPC over TLS
- Format: JSON
- Auth:
  - optional API key for public DQSN services, or
  - no auth on localhost / LAN for self-hosted setups.

Adamantine MAY support **multiple DQSN backends** via
`config/shield-endpoints.yml` (e.g. primary + backup).

---

## 3. Endpoint: /v1/node-summary

High‑level snapshot of current node and cluster health.

```http
GET /v1/node-summary
```

### 3.1 Example Response

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
  "network_health": {
    "status": "healthy",
    "eclipse_risk": "low",
    "partition_risk": "low",
    "notes": [
      "local_node_within_cluster_height",
      "no_major_fork_detected"
    ]
  },
  "recommendation": {
    "status": "healthy",
    "preferred_action": "continue",
    "suggested_node": null
  },
  "timestamp": "2025-12-02T13:20:00Z"
}
```

Key fields for Guardian / Risk Engine:

- `network_health.status` – `"healthy" | "warning" | "unsafe"`
- `cluster_view.fork_suspicion`
- `cluster_view.height_disagreement`
- `network_health.eclipse_risk` / `partition_risk`

The Shield Bridge may cache this for a short window
(e.g. 5–30 seconds) to avoid hammering DQSN.

---

## 4. Endpoint: /v1/node-list

Optional endpoint to get a **diverse set of candidate nodes** for
NodeManager and advanced users.

```http
GET /v1/node-list
```

### 4.1 Example Response

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
  ],
  "recommendation": {
    "preferred": "node1.dgb.example:12024",
    "fallback": ["node2.dgb.example:12024"]
  }
}
```

Adamantine / NodeManager may use this to:

- auto-select healthy nodes,
- suggest nodes in the “advanced settings” UI,
- cross-check views from multiple nodes.

---

## 5. Endpoint: /v1/health-check

Lightweight probe used by the wallet for periodic health checks and
startup diagnostics.

```http
GET /v1/health-check
```

### 5.1 Example Response

```json
{
  "status": "ok",
  "uptime_seconds": 7200,
  "last_cluster_refresh": "2025-12-02T13:18:00Z"
}
```

If this endpoint times out or returns a non‑OK status, the Shield Bridge
marks DQSN as `"offline"` and Risk Engine adjusts scoring accordingly.

---

## 6. Error Model (minimal)

DQSN SHOULD return structured errors where possible:

```json
{
  "error": {
    "code": "BACKEND_UNAVAILABLE",
    "message": "DQSN cluster temporarily unreachable",
    "retry_after_seconds": 30
  }
}
```

The Shield Bridge maps these into its own internal error types and
exposes only **safe, non‑leaky** messages to the wallet UI.

---

## 7. Degraded Behaviour

When DQSN is `"offline"` or reports `"unsafe"` network health:

- Guardian should be more cautious about:
  - large DGB sends,
  - DigiDollar operations,
  - interpreting height / confirmation counts.
- NodeManager may:
  - attempt to switch to a better node from `/v1/node-list`,
  - temporarily reduce background operations that depend on consensus.

The wallet UI MAY:

- warn the user about node health,
- suggest switching to other nodes,
- show a “Network Health: Degraded” banner.

Exact risk scoring details live in `risk-engine/scoring-rules.md`, and
DQSN is treated as one **input signal** into the overall score, not a
single point of failure.
