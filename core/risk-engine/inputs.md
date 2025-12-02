# Risk Engine — Inputs (inputs.md)

Status: **draft v0.1 – internal skeleton**

This document defines the **shape of the data** fed into the Risk Engine
for a single action evaluation.

Guardian provides an **ActionRequest**, Shield Bridge provides shield
snapshots, and local modules provide device / app state.

Risk Engine merges these into a single `RiskAssessment`.

---

## 1. RiskInput Aggregate

```ts
RiskInput {
  action: ActionRequest
  shield: ShieldStatusSnapshot
  local: LocalContextSnapshot
  adaptive_overlay?: AdaptiveOverlaySnapshot
}
```

Types like `ActionRequest` and `GuardianVerdict` are defined in
`guardian-wallet/spec.md`; this file focuses on shield + local shapes.

---

## 2. ShieldStatusSnapshot

```ts
ShieldStatusSnapshot {
  sentinel?: SentinelSnapshot
  dqsn?: DqsnSnapshot
  adn?: AdnSnapshot
  qac?: QacSnapshot
}
````

Fields are deliberately compact to avoid bloating logs and memory.

### 2.1 SentinelSnapshot

```ts
SentinelSnapshot {
  anomaly_level: "unknown" | "low" | "medium" | "high"
  reorg_risk: "unknown" | "low" | "medium" | "high"

  fee_environment: "unknown" | "low" | "normal" | "high" | "extreme"
  min_fee_sats_per_byte?: number
  median_fee_sats_per_byte?: number
  high_fee_sats_per_byte?: number

  last_update_at: timestamp
  is_stale: boolean
}
```

### 2.2 DqsnSnapshot

```ts
DqsnSnapshot {
  node_status: "unknown" | "healthy" | "warning" | "unsafe"
  fork_suspicion: "none" | "low" | "medium" | "high"
  height_disagreement: "low" | "medium" | "high"

  cluster_node_count?: number
  avg_latency_ms?: number

  last_update_at: timestamp
  is_stale: boolean
}
```

### 2.3 AdnSnapshot

```ts
AdnSnapshot {
  mode: "unknown" | "normal" | "heightened" | "lockdown"

  lockdown_active: boolean
  lockdown_scope: string[]            // e.g. ["no-large-broadcasts"]

  last_update_at: timestamp
  is_stale: boolean
}
```

### 2.4 QacSnapshot

```ts
QacSnapshot {
  // For outgoing TXs, this may be empty or based on past behaviour.
  last_relevant_confidence_level?:
    "unknown" | "low" | "medium" | "high"

  last_timing_anomaly_score?: number   // 0.0 – 1.0
  last_disagreement_score?: number     // 0.0 – 1.0

  last_update_at?: timestamp
  is_stale: boolean
}
```

For **incoming** transactions, separate QAC queries can be logged and
shown in the UI; this snapshot focuses on what's relevant for outgoing
risk scoring.

---

## 3. LocalContextSnapshot

```ts
LocalContextSnapshot {
  device: DeviceSecuritySnapshot
  app: AppStateSnapshot
  counterparty?: CounterpartySnapshot
  history?: HistorySnapshot
}
```

### 3.1 DeviceSecuritySnapshot

```ts
DeviceSecuritySnapshot {
  os_family: "ios" | "android" | "web" | "desktop" | "unknown"
  os_version: string

  is_rooted_or_jailbroken: boolean
  has_known_exploit: boolean

  has_secure_enclave: boolean
  biometrics_configured: boolean

  last_security_check_at?: timestamp
}
```

### 3.2 AppStateSnapshot

```ts
AppStateSnapshot {
  app_version: string
  build_channel: "release" | "beta" | "dev"

  integrity_ok: boolean              // passed self-checks / signatures
  debug_mode_enabled: boolean

  last_config_sync_at?: timestamp
}
```

### 3.3 CounterpartySnapshot

```ts
CounterpartySnapshot {
  contact_id?: string
  contact_trust_level?: "unknown" | "low" | "normal" | "high" | "blocked"

  is_known_scam?: boolean
  is_exchange?: boolean
  is_internal_wallet?: boolean

  // Simple usage stats
  total_interactions?: number
  last_interaction_at?: timestamp
}
```

### 3.4 HistorySnapshot

```ts
HistorySnapshot {
  recent_actions_count: number          // in last N hours
  recent_large_sends_count: number
  recent_dd_operations_count: number

  // Optional baseline for abnormality checks
  typical_max_send_sats?: number
  typical_frequency_per_day?: number
}
```

---

## 4. AdaptiveOverlaySnapshot

```ts
AdaptiveOverlaySnapshot {
  global_risk_level?: "low" | "medium" | "high"
  risk_overlay_score?: number

  escalations?: AdaptiveEscalation[]
}

AdaptiveEscalation {
  id: string
  scope: string                 // e.g. "send-dgb", "mint-dd"
  min_amount_sats?: number
  recommended_action?: string   // advisory; Guardian enforces
}
```

Risk Engine does not blindly follow Adaptive overlays; instead it treats
them as **additional hints** that lift the baseline risk score.

---

## 5. Privacy Considerations

- RiskInput should be kept **in-memory only** for live evaluations.
- If logged for diagnostics, fields MUST be:
  - minimised,
  - hashed where possible,
  - stripped of direct identifiers (raw addresses, exact amounts).
- Persistent logs, if enabled, must follow the privacy model and be
  opt-in, never default-on for normal users.
