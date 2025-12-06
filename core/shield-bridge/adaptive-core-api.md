# Shield Bridge — Adaptive Core API (adaptive-core-api.md)

Status: **draft v0.1 – internal skeleton**

This document defines how Adamantine interacts with the
**Quantum Adaptive Core (QACore)** through the Shield Bridge.

Adaptive Core is the **immune system / learning brain** of the shield:

- consumes anonymised events and metrics,
- learns patterns of attacks / anomalies,
- feeds back **policy hints** and **risk overlays**.

Adamantine must treat Adaptive Core as:

- advisory for **policy suggestions**,
- authoritative for some **emergency escalations**.

---

## 1. Purpose

- Send **decision + telemetry events** from Guardian / wallet.
- Receive **policy hints** and **escalation directives**.
- Query **learned risk overlays** for certain contexts.

---

## 2. Endpoint: /v1/events (ingest)

Adamantine → Adaptive Core

```http
POST /v1/events
Content-Type: application/json
```

```json
{
  "client": "adamantine-wallet",
  "version": "0.1.0",
  "profile_fingerprint": "hashed-or-omitted",
  "device_class": "mobile-ios",
  "events": [
    {
      "kind": "guardian-verdict",
      "timestamp": "2025-12-02T13:40:00Z",
      "risk_level": "high",
      "guardian_action": "block-and-alert",
      "action_kind": "send-dgb",
      "context_hash": "abc123"
    },
    {
      "kind": "shield-status",
      "timestamp": "2025-12-02T13:40:05Z",
      "sentinel_status": "online",
      "dqsn_status": "healthy",
      "adn_mode": "heightened"
    }
  ]
}
```

All identifiers must be:

- minimised,
- hashed where possible,
- compliant with privacy model.

---

## 3. Endpoint: /v1/policy-hints

Adaptive Core → Adamantine

```http
GET /v1/policy-hints?profile_security_level=paranoid
```

### Example Response

```json
{
  "global_risk_level": "medium",
  "valid_for_seconds": 3600,
  "escalations": [
    {
      "id": "esc-001",
      "scope": "send-dgb",
      "min_amount_sats": 1000000000,
      "recommended_action": "require-passphrase"
    },
    {
      "id": "esc-002",
      "scope": "mint-dd",
      "recommended_action": "block-and-alert"
    }
  ],
  "notes": [
    "Elevated risk detected in last hour. Suggest tightening for large sends.",
    "DD mint operations show abnormal patterns; consider temporary halt."
  ]
}
```

Guardian merges this with **local config** and user preferences to compute the effective runtime policy.

---

## 4. Endpoint: /v1/context-risk (optional)

Query contextual risk for a given high-level action without sending full details.

```http
POST /v1/context-risk
Content-Type: application/json
```

```json
{
  "action_kind": "send-dgb",
  "approx_amount_bucket": "1-10-dgb",
  "address_reputation_bucket": "unknown",
  "shield_status": {
    "sentinel": "online",
    "dqsn": "healthy",
    "adn": "normal"
  }
}
```

```json
{
  "risk_overlay_level": "medium",
  "risk_overlay_score": 0.6,
  "notes": [
    "Recent pattern of phishing-like sends to unknown addresses."
  ]
}
```

Guardian can treat this as an additional input into Risk Engine.

---

## 5. Degraded Behaviour

When Adaptive Core is unreachable:

- Guardian falls back to static config + real-time shield signals only.
- No adaptive escalations are applied.

When Adaptive Core explicitly signals **emergency**:

- Guardian may override some user preferences temporarily,
- enter enforced lock / stricter mode as defined in configs.

All such decisions must be:

- logged locally,
- visible in diagnostics,
- time-bounded.
