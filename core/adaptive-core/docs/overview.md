# 🧠 Adaptive Core — Behavior & Learning Engine (v0.2)
*Location: `core/adaptive-core/docs/overview.md`*  
*Audience: DigiByte Core Developers, Security Engineers, Data/ML Engineers*  

Adaptive Core is the **behavioral immune system** of Adamantine.  
Where Guardian enforces explicit rules and the Shield layers monitor technical risk, Adaptive Core learns patterns over time and adjusts **how strongly** the system reacts.

It does *not* change DigiByte consensus or keys.  
It only influences **risk weights, thresholds, and policy hints**.

---

## 1. Design Goals

Adaptive Core is built to:

1. Learn **normal behavior** for a wallet over time  
2. Detect **deviations** from that baseline  
3. Adjust **Risk Engine weights** dynamically  
4. Provide **memory** of past incidents (near misses, blocks, lockdowns)  
5. Remain **transparent and inspectable** (no opaque AI black box)

---

## 2. High-Level Architecture

```text
Transaction / Message / Event
        ↓
   Guardian Context
        ↓
   Adaptive Ingest
        ↓
  Behavior Profile Update
        ↓
  Weight / Threshold Hints
        ↓
   Risk Engine + Guardian
```

Adaptive Core never directly approves or blocks a transaction.  
It only **advises** Guardian and the Risk Engine.

---

## 3. Data Model

Adaptive Core maintains per-wallet, per-account, and per-asset profiles.

### 3.1 BehaviorProfile

```json
{
  "profile_id": "uuid",
  "wallet_id": "string",
  "account_id": "string",
  "created_at": "timestamp",
  "last_seen_at": "timestamp",
  "stats": {
    "tx_count": 0,
    "avg_amount": 0,
    "max_amount": 0,
    "velocity_per_day": 0,
    "asset_diversity": 0
  },
  "flags": {
    "recent_lockdown": false,
    "recent_block": false,
    "under_observation": false
  }
}
```

### 3.2 IncidentRecord

```json
{
  "incident_id": "uuid",
  "wallet_id": "string",
  "type": "WARN | BLOCK | LOCKDOWN",
  "risk_score": 0.0,
  "layers": {
    "sentinel": 0.0,
    "dqsn": 0.0,
    "adn": 0.0,
    "qwg": 0.0,
    "adaptive": 0.0
  },
  "timestamp": "timestamp"
}
```

These structures are persisted (local or remote, depending on implementation).

---

## 4. Feature Extraction

For each GuardianContext, Adaptive Core computes a **feature vector**:

- normalized amount  
- destination novelty (new vs known address)  
- time-of-day bucket  
- device fingerprint hash  
- client type (web / ios / android)  
- asset type (DGB / DigiAsset / DD)  
- Enigmatic presence (yes/no, dialect type)  
- policy overrides (manual user approval, 2FA, etc.)

Feature extraction logic lives in:

`core/adaptive-core/features.py`

---

## 5. Learning Model

Adaptive Core v0.2 uses a **simple statistical / rules-based model** (no heavy ML):

- Exponential moving averages  
- Bounds / thresholds learned from history  
- “Stability index” based on variation over time  

### 5.1 Stability Index

Value in `[0, 1]`:

- `0.0–0.3` → unstable  
- `0.3–0.7` → normal  
- `0.7–1.0` → very stable  

---

## 6. Influence on Risk Engine

Adaptive Core **does not** change scores directly.  
Instead, it outputs **weight hints**:

```json
{
  "weights_hint": {
    "W_adaptive": 0.15,
    "W_local": 0.25,
    "W_sentinel": 0.20,
    "W_dqsn": 0.20,
    "W_adn": 0.10,
    "W_qwg": 0.10
  },
  "threshold_hint": {
    "warn_delta": -0.02,
    "block_delta": -0.01
  }
}
```

The Risk Engine merges these hints with static defaults from `scoring-rules.md`.

### 6.1 Intuition

- If behavior has been stable for a long time → slightly **lower** sensitivity to small changes.  
- If behavior becomes erratic → **raise** sensitivity, increase W_adaptive.

---

## 7. Incident Handling & Memory

When Guardian returns `WARN`, `BLOCK`, or `LOCKDOWN`, Adaptive Core:

1. Stores an `IncidentRecord`  
2. Associates it with the current `BehaviorProfile`  
3. Adjusts stability index downward  
4. Temporarily increases W_adaptive and/or tightens thresholds  

Over time (if events are clean), the stability index **recovers**.

---

## 8. Integration Points

### 8.1 Guardian → Adaptive

Guardian sends every normalized context to:

`core/adaptive-core/ingest.py`

Including:

- final risk score  
- verdict  
- underlying layer contributions (sentinel, dqsn, etc.)  

### 8.2 Adaptive → Risk Engine

At the start of each scoring run, Risk Engine calls:

`adaptive_core.get_weight_hints(profile_id, context)`

If Adaptive is disabled or unavailable, defaults are used.

---

## 9. Privacy & Security Considerations

- Adaptive data is **local to the wallet environment** unless explicitly synced.  
- No user-identifying personal data is required; only behavioral statistics.  
- Profiles are keyed by wallet/account IDs, not names/emails.  
- Implementations must consider GDPR/local privacy laws when syncing behavior profiles.

---

## 10. Configuration

Config file (example):

```yaml
adaptive_core:
  enabled: true
  storage_backend: "local"   # or "remote"
  decay_days: 30
  min_events_for_profile: 10
  max_incident_history: 1000
```

---

## 11. Failure Modes

If Adaptive Core fails or is unavailable:

- Guardian and Risk Engine **continue to operate** using static weights.  
- A warning is logged, but no transaction is blocked solely due to Adaptive failure.  
- Incident logging falls back to a minimal event log.

---

## 12. Version

```
Adaptive Core Spec Version: v0.2
Compatible with Adamantine v0.2 and Guardian Integration v0.2
```

---

## 13. Summary

Adaptive Core turns Adamantine from a static “rule engine” into a **living security organism**:

- learns normal behavior  
- remembers past incidents  
- subtly tunes reaction strength  
- never overrides Guardian, only advises  

This document serves as the blueprint for any implementation of Adaptive Core within the Adamantine ecosystem.
