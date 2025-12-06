# 🧩 Guardian Wallet — Schemas & Data Models
Status: **draft v0.2 – aligned with Adamantine v0.2**

This document describes **canonical JSON / Pydantic‑style schemas** used
by the Guardian engine. Implementations in other languages should mirror
these shapes as closely as possible.

---

## 1. Common Types

```jsonc
// MoneyAmount
{
  "asset": "dgb | digiasset | digidollar",
  "amount": "string-decimal",       // to avoid FP issues
  "unit": "DGB | sat | token | DD"
}

// RiskLevel
"low" | "medium" | "high" | "critical"

// Verdict
"allow" | "warn" | "block" | "require_second_factor"
```

---

## 2. GuardianRiskSnapshot

Snapshot of all relevant scores at a decision time.

```jsonc
{
  "sentinel": {
    "score": 0.0,
    "signals": [ "mempool_normal", "no_reorgs_detected" ]
  },
  "dqsn": {
    "score": 0.0,
    "signals": [ "network_stable" ]
  },
  "adn": {
    "score": 0.0,
    "signals": [ "node_in_sync", "no_lockdown" ]
  },
  "qwg": {
    "score": 0.0,
    "signals": [ "keys_pqc_ready", "no_export_leaks" ]
  },
  "adaptive_core": {
    "score": 0.0,
    "signals": [ "behaviour_typical" ]
  },
  "aggregated": {
    "guardian_risk_score": 0.0,
    "guardian_risk_level": "low",
    "weights": {
      "sentinel": 0.2,
      "dqsn": 0.2,
      "adn": 0.2,
      "qwg": 0.2,
      "adaptive_core": 0.2
    }
  }
}
```

---

## 3. Policy Model

```jsonc
{
  "wallet_id": "adamantine-main",
  "account_id": "default-dgb",
  "version": 1,
  "limits": {
    "daily_spend": {
      "default": { "asset": "dgb", "amount": "10000", "unit": "DGB" },
      "digiasset": { "asset": "digiasset", "amount": "1000", "unit": "token" }
    },
    "single_tx_max": {
      "default": { "asset": "dgb", "amount": "5000", "unit": "DGB" }
    }
  },
  "requirements": {
    "second_factor_threshold": {
      "guardian_risk_level_at_least": "medium",
      "amount_over": { "asset": "dgb", "amount": "1000", "unit": "DGB" }
    },
    "min_confirmations_inbound": {
      "default": 12,
      "high_risk_sender": 25
    }
  },
  "flags": {
    "lockdown_enabled": true,
    "permit_offline_mode": false
  },
  "sources": {
    "static_config": true,
    "remote_overrides": true,
    "adaptive_core": true
  },
  "last_updated": "RFC3339"
}
```

---

## 4. Event Model (`GuardianEvent`)

```jsonc
{
  "event_id": "uuid-v4",
  "wallet_id": "adamantine-main",
  "account_id": "default-dgb",
  "event_type": "login_attempt | device_change | tx_created | tx_signed | tx_broadcast | policy_override",
  "created_at": "RFC3339",
  "client": "android | ios | web | node-adapter",
  "metadata": {
    "ip_hash": "…",
    "device_id": "…",
    "txid": "optional",
    "additional": { }
  }
}
```

Guardian MAY forward a normalised `GuardianEvent` stream into Sentinel / DQSN /
Adaptive Core via Shield Bridge.

---

## 5. Decision Record (`GuardianDecision`)

Used for audit trails and adaptive learning.

```jsonc
{
  "decision_id": "uuid-v4",
  "wallet_id": "adamantine-main",
  "account_id": "default-dgb",
  "when": "RFC3339",
  "verdict": "allow",
  "guardian_risk_score": 0.07,
  "guardian_risk_level": "low",
  "risk_snapshot": { /* GuardianRiskSnapshot */ },
  "tx_summary": {
    "asset": "dgb",
    "amount": "50",
    "unit": "DGB",
    "destination_count": 1
  },
  "policy_version": 1,
  "source_endpoint": "tx/preflight",
  "extra": { }
}
```

---

## 6. Node Context (`NodeStatusSnapshot`)

Pulled from node adapter (`node-api.md`).

```jsonc
{
  "node_version": "v8.25.0",
  "network": "mainnet",
  "best_height": 2000000,
  "headers_height": 2000000,
  "in_sync": true,
  "mempool_tx": 1234,
  "peer_count": 16,
  "lockdown_mode": "none | soft | hard"
}
```

Guardian uses this as an input into risk scoring.

---

## 7. Extensibility

- All schemas MUST be **backwards compatible**:
  - new fields are optional
  - existing fields are not repurposed silently
- Implementations should provide language‑native structs / classes
  that map 1:1 onto these JSON shapes.
