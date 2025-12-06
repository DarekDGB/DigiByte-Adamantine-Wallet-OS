# Shield Bridge — ADN API (adn-api.md)

Status: **draft v0.2 – internal skeleton**

This document defines how the Adamantine Wallet talks to the  
**Autonomous Defense Node v2 (ADN v2)** through the Shield Bridge.

ADN v2 is the **node‑side reflex / lockdown engine** of the DigiByte
Quantum Shield stack. It runs *next to* a DigiByte node, watching:

- chain and mempool flow in real time,
- shield signals from Sentinel / DQSN / Adaptive Core,
- local Guardian / wallet actions (optional).

From Adamantine’s perspective, ADN exposes a small set of **control
and status endpoints**:

- query current defense posture,
- submit a transaction + context for pre‑flight evaluation,
- request temporary lockdown / unlock,
- fetch recent incidents for UX / diagnostics.

ADN **does not replace** consensus or node rules – it only controls how
*our* node behaves (e.g. pausing broadcasts, tightening local policies).

---

## 1. Transport & Auth (Conceptual)

Implementation details may vary, but recommended defaults:

- Protocol: HTTP(S) over localhost or LAN.
- Format: JSON.
- Auth:
  - for local‑only deployments, loopback without auth is acceptable,
  - for remote ADN instances, use mutual‑TLS or signed tokens.

Adamantine discovers ADN endpoints via `config/shield-endpoints.yml`
(Shield Bridge will unify this for Sentinel, DQSN, QAC, Adaptive Core).

---

## 2. Endpoint: /v1/status

High‑level snapshot of ADN’s current mode and recent activity.

```http
GET /v1/status
```

### Example Response

```json
{
  "adn_version": "2.0.0-alpha1",
  "node_id": "local-node-01",
  "mode": "normal",                   
  "lockdown": {
    "active": false,
    "reason": null,
    "since": null
  },
  "incident_counters": {
    "blocks_flagged": 0,
    "txs_blocked": 3,
    "txs_delayed": 1,
    "policy_escalations": 4
  },
  "last_incident_at": "2025-12-02T13:30:00Z",
  "shield_inputs": {
    "sentinel": "online",
    "dqsn": "healthy",
    "adaptive_core": "online"
  },
  "timestamp": "2025-12-02T13:31:00Z"
}
```

Key fields for Guardian / Wallet UX:

- `mode` – `"normal" | "heightened" | "investigating" | "lockdown"`
- `lockdown.active` – if true, wallet should visually warn user
- `incident_counters` – may be surfaced in diagnostics / logs

---

## 3. Endpoint: /v1/evaluate-tx

Ask ADN to evaluate a **proposed DigiByte transaction** *before*
Adamantine commits to broadcast.

This is the core pre‑flight hook for wallet sends.

```http
POST /v1/evaluate-tx
Content-Type: application/json
```

### Request

```json
{
  "wallet_id": "w1",
  "account_id": "a1",
  "tx_context": {
    "intent": "send-dgb",
    "amount_sats": 250000000,
    "to_address": "dgb1xyz...",
    "fee_sats_per_byte": 4,
    "user_entropy": "hashed-or-omitted",
    "local_risk_hints": {
      "guardian_verdict": "allow",
      "sentinel_level": "low",
      "dqsn_status": "healthy"
    }
  },
  "raw_tx_hex": "0200000001..."
}
```

Notes:

- `raw_tx_hex` MAY be omitted in early prototypes – ADN can work
  purely on metadata + hints.
- `user_entropy` / `context` values must follow the privacy model and
  never leak direct PII.

### Response (example)

```json
{
  "decision": {
    "verdict": "allow",                 
    "confidence": 0.93,
    "recommended_action": "broadcast",  
    "reasons": [
      "no_conflicting_incidents",
      "network_health_normal"
    ]
  },
  "overrides": {
    "min_confirmations": 1,
    "max_amount_sats": null,
    "require_guardian_approval": false
  },
  "lockdown_hint": null,
  "incident_id": null,
  "timestamp": "2025-12-02T13:32:00Z"
}
```

Possible `decision.verdict` values (provisional):

- `"allow"` – safe to proceed.
- `"delay"` – advise user / wallet to retry later (e.g. suspicious mempool).
- `"block"` – do not broadcast from this node.
- `"escalate"` – require additional Guardian / user checks.

WalletService maps this into GuardianDecision / SendStatus and user‑facing
UX (warnings, extra confirmations, etc.).

---

## 4. Endpoint: /v1/lockdown

Request a **local node lockdown** or query current lockdown reason.

This is primarily driven by ADN + Adaptive Core, but the wallet MAY
trigger or release softer modes in response to user actions (e.g.
lost device, suspected compromise).

```http
POST /v1/lockdown
Content-Type: application/json
```

### Request

```json
{
  "action": "enter",                  
  "scope": "tx-broadcasts",
  "reason": "user-suspects-compromise",
  "requested_by": "adamantine-wallet",
  "requested_until": "2025-12-02T18:00:00Z"
}
```

Allowed `action` values:

- `"enter"` – request entering lockdown / heightened mode.
- `"extend"` – extend an existing lockdown window.
- `"exit"` – request returning to normal mode (ADN MAY refuse if higher
  priority sources still demand lockdown).

### Example Response

```json
{
  "accepted": true,
  "effective_mode": "lockdown",
  "lockdown": {
    "active": true,
    "scope": ["tx-broadcasts"],
    "reason": "user-suspects-compromise",
    "since": "2025-12-02T13:35:00Z",
    "until": "2025-12-02T18:00:00Z"
  }
}
```

Wallet should reflect this clearly in the UI (e.g. “Broadcasts paused by
local defense node”) and refuse to override it silently.

A read‑only variant may also be implemented:

```http
GET /v1/lockdown
```

to fetch the current lockdown details without changing anything.

---

## 5. Endpoint: /v1/incidents

Fetch recent **security incidents / notable events** recorded by ADN.

```http
GET /v1/incidents?limit=20
```

### Example Response

```json
{
  "incidents": [
    {
      "id": "inc-20251202-001",
      "kind": "tx-blocked",
      "severity": "high",
      "timestamp": "2025-12-02T12:50:00Z",
      "summary": "Outgoing tx blocked due to fork suspicion",
      "details_hash": "abc123"
    },
    {
      "id": "inc-20251202-002",
      "kind": "mode-escalation",
      "severity": "medium",
      "timestamp": "2025-12-02T13:05:00Z",
      "summary": "Mode raised to heightened during mempool anomaly",
      "details_hash": "def456"
    }
  ]
}
```

Adamantine may surface this in an “advanced diagnostics” panel and use
it for support / export logs (without exposing sensitive details).

---

## 6. Degraded Behaviour

When ADN endpoint(s) are unreachable:

- Shield Bridge marks ADN status as `"offline"`.
- Wallet must **not** assume everything is safe:
  - treat missing ADN as loss of one defense layer,
  - rely more heavily on Guardian + Sentinel + DQSN + Adaptive Core.

Recommended behaviour:

- For small, routine operations → allow but warn in diagnostics that
  ADN is offline.
- For high‑value or high‑risk operations → Guardian policies may
  require extra approvals or refuse entirely, depending on the
  configured profile.

ADN failures must never break basic wallet functionality, but they
**must** be visible in logs / advanced UI so operators can investigate.
