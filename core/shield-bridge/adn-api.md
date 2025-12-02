# Shield Bridge — ADN API (adn-api.md)

Status: **draft v0.1 – internal skeleton**

This document defines how Adamantine communicates with the
**Autonomous Defense Node v2 (ADN v2)** through the Shield Bridge.

ADN is the **node-level reflex & lockdown engine**. It monitors
local node behaviour and can enter **defense modes** when it detects
suspicious patterns.

Adamantine must **observe** ADN state and adjust behaviour, but never
override ADN decisions.

---

## 1. Purpose

- Read ADN’s current **defense mode**.
- Read recent **alerts / incidents**.
- Optionally send **annotations** about user-approved actions
  (for correlation).

---

## 2. Endpoint: /v1/state

```http
GET /v1/state
```

### Example Response

```json
{
  "mode": "normal",                
  "lockdown": {
    "is_active": false,
    "scope": []
  },
  "recent_alerts": [
    {
      "id": "alert-123",
      "kind": "reorg-depth",
      "severity": "medium",
      "summary": "Detected reorg of depth 2",
      "timestamp": "2025-12-02T13:25:00Z"
    }
  ],
  "timestamp": "2025-12-02T13:26:00Z"
}
```

`mode` values (example):

- `"normal"`
- `"heightened"`
- `"lockdown"`

`lockdown.scope` might contain strings like:

- `"no-new-connections"`
- `"no-large-broadcasts"`
- `"no-zero-conf"`

Guardian interprets these as **hard constraints**.

---

## 3. Endpoint: /v1/incidents

Returns a paginated list of recent ADN incidents.

```http
GET /v1/incidents?limit=20&since=2025-12-02T12:00:00Z
```

```json
{
  "incidents": [
    {
      "id": "inc-001",
      "kind": "peer-flooding",
      "severity": "high",
      "summary": "Unusual inbound message rate from multiple peers.",
      "details_url": "https://adn.local/incidents/inc-001",
      "timestamp": "2025-12-02T13:00:00Z"
    }
  ],
  "next_cursor": null
}
```

Adamantine may surface a simplified view in diagnostics but **Guardian
mostly needs the aggregate `mode` and `lockdown` state**.

---

## 4. Endpoint: /v1/annotations (optional)

The wallet may send **annotations** about user-approved actions to help
ADN correlate local behaviour with shield decisions.

```http
POST /v1/annotations
Content-Type: application/json
```

```json
{
  "client": "adamantine-wallet",
  "version": "0.1.0",
  "events": [
    {
      "kind": "tx-approved",
      "txid": "abc123...",
      "risk_level": "medium",
      "guardian_action": "require-biometric",
      "timestamp": "2025-12-02T13:27:00Z"
    }
  ]
}
```

This is optional and must follow privacy constraints.

---

## 5. Degraded Behaviour

When ADN reports `mode = "lockdown"`:

- Guardian should **block** certain actions regardless of local config
  (see `guardian-wallet/configs.md` hard limits).
- UI should display a clear “Defense Mode Active” banner.

When ADN is unreachable, its signals are treated as **missing** and
Risk Engine compensates by leaning more heavily on Sentinel + DQSN.
