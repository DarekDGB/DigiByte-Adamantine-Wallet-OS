# DGB Guardian Wallet Layer — Specification (spec.md)

Status: **draft v0.1 – internal skeleton**

This document specifies the **DGB Guardian Wallet layer** inside the
DigiByte Adamantine Wallet.

Guardian Wallet is a **policy + decision layer** that:

- sits between the *UI* and any *transaction broadcasting*,
- consumes **risk signals** from the Quantum Shield stack and local checks,
- enforces **actions** (allow, challenge, lock, block) based on policy,
- remains **implementation-agnostic** (usable on web / iOS / Android).

Guardian Wallet does **not**:

- modify DigiByte consensus,
- replace node validation,
- touch raw cryptography or signatures directly.

It is a **reflex layer** for user protection.

---

## 1. Core Responsibilities

Guardian Wallet is responsible for:

1. **Evaluating outgoing actions**
   - Sending DGB
   - Minting / redeeming DD
   - Creating Enigmatic payment requests
2. **Applying policy** based on:
   - user’s chosen risk profile,
   - real-time shield signals (Sentinel, DQSN, ADN, QAC, Adaptive Core),
   - local heuristics (amount, history, address reputation, contact flags).
3. **Producing a verdict**:
   - `allow`
   - `allow-with-challenge` (biometric / passphrase / local confirm)
   - `delay-and-retry` (e.g. degraded network)
   - `block-and-alert`
4. **Recording decisions** for Adaptive Core learning.

Guardian Wallet is essentially a **policy engine** and a **verdict API**.

---

## 2. High-Level Architecture

```text
[ UI Layer ]  →  [ Guardian Wallet Layer ]  →  [ TX Builder / Broadcaster ]
                     ↑            ↑
                     |            |
                [ Shield Bridge ] |
                     ↑            |
             [ Sentinel / DQSN / ADN / QAC / Adaptive Core ]
```

- UI NEVER calls the network directly for sensitive actions.
- UI constructs an **ActionRequest** and asks Guardian for a verdict.
- Guardian queries Shield Bridge + local checks → returns **GuardianVerdict**.
- If verdict is `allow` → TX Builder signs & broadcasts.
- If verdict is `allow-with-challenge` → UI must pass a challenge flow first.
- If verdict is `block-and-alert` → UI shows reason and aborts.

---

## 3. Core Types (Conceptual)

### 3.1 GuardianMode

```ts
type GuardianMode = "off" | "observe" | "enforce"
```

- `off`      – no blocking, only logging (for debugging / dev).
- `observe`  – logs and surfaces warnings, but does not block.
- `enforce`  – actively blocks / challenges according to policy.

### 3.2 RiskLevel

```ts
type RiskLevel = "unknown" | "low" | "medium" | "high" | "critical"
```

### 3.3 GuardianAction

```ts
type GuardianAction =
  | "allow"
  | "require-local-confirmation"
  | "require-biometric"
  | "require-passphrase"
  | "delay-and-retry"
  | "block-and-alert"
```

### 3.4 ActionKind

```ts
type ActionKind =
  | "send-dgb"
  | "mint-dd"
  | "redeem-dd"
  | "enigmatic-payment-request"
  | "settings-change"
  | "unknown"
```

---

## 4. Action Request Model

The UI constructs an **ActionRequest** and passes it to Guardian.

```ts
ActionRequest {
  id: string                       // UUID for logging / audit
  timestamp: timestamp

  kind: ActionKind
  profile_id: string
  account_id: string

  // monetary context (if any)
  amount_sats?: number             // DGB in satoshis
  amount_dd?: number               // DD units

  from_address?: string
  to_address?: string
  to_contact_id?: string           // optional link to Contact

  // environment context
  device_security_state: DeviceSecuritySnapshot
  network_state: NetworkStateSnapshot

  // optional extras per kind
  extras?: Record<string, any>
}
```

`DeviceSecuritySnapshot` and `NetworkStateSnapshot` will be defined in the
risk-engine docs, but Guardian treats them as immutable input.

---

## 5. Guardian Verdict Model

```ts
GuardianVerdict {
  request_id: string               // matches ActionRequest.id
  decided_at: timestamp

  // overall classification
  risk_level: RiskLevel
  action: GuardianAction

  // explanation for UI / logs
  title: string                    // short user-facing explanation
  description?: string             // longer text if needed

  // optional remediation hints
  retry_after_ms?: number
  suggested_alt_node?: string

  // internal correlation / shield linkage
  shield_trace_id?: string
  notes_for_adaptive_core?: string
}
```

UI logic:

- If `action = "allow"` → proceed.
- If `action ∈ {"require-*"} ` → run challenge, then re-confirm.
- If `action = "delay-and-retry"` → show countdown / retry.
- If `action = "block-and-alert"` → abort and show reason.

---

## 6. Policy Configuration

Policy is configured per **Risk Profile**.

Simplified example:

```yaml
# config/risk-profiles.yml
profiles:
  - id: "safe-default"
    label: "Safe Default"
    guardian_mode: "enforce"
    send_policy:
      low:       "allow"
      medium:    "require-local-confirmation"
      high:      "require-biometric"
      critical:  "block-and-alert"

  - id: "paranoid"
    label: "Paranoid"
    guardian_mode: "enforce"
    send_policy:
      low:       "require-local-confirmation"
      medium:    "require-biometric"
      high:      "require-passphrase"
      critical:  "block-and-alert"

  - id: "observe-only"
    label: "Observe Only"
    guardian_mode: "observe"
    send_policy:
      low:       "allow"
      medium:    "allow"
      high:      "allow"
      critical:  "allow"
```

The mapping from **RiskLevel → GuardianAction** can be tuned per profile
and per action kind in future versions.

---

## 7. Risk Inputs (High Level)

Guardian does **not** compute all risk alone. It orchestrates:

1. **Shield Bridge Signals**
   - Sentinel: mempool anomalies, reorg risk, fee weirdness.
   - DQSN: node health, fork suspicion, latency.
   - ADN: local node behaviour anomalies.
   - QAC: confirmation irregularities across the network.
   - Adaptive Core: learned patterns, attack fingerprints.

2. **Local Heuristics**
   - Contact trust level & risk flags.
   - New / unseen address vs known contact.
   - Sudden large amount relative to account history.
   - Device security state (jailbroken / rooted / outdated OS).
   - Time since last guardian config sync.

3. **User Overrides (in configs.md)**
   - User can choose stricter profiles.
   - User may opt into “experimental” shield data.

These inputs are combined by the **Risk Engine** into a single `RiskLevel`.
Guardian then applies policy mapping to that level.

---

## 8. Life of a Transaction (Send DGB Example)

Conceptual flow (detailed flows live in `flows.md`):

1. User fills send form in UI.
2. UI builds `ActionRequest` with `kind = "send-dgb"`.
3. UI calls `Guardian.evaluate(actionRequest)`.
4. Guardian:
   - pulls current Risk Profile for this account,
   - queries Shield Bridge for fresh signals,
   - runs local heuristics,
   - aggregates into a `RiskLevel`,
   - picks `GuardianAction` based on profile mapping,
   - returns `GuardianVerdict`.
5. UI:
   - If verdict says `allow` → proceed to signing/broadcast.
   - If verdict says `require-*` → run challenge, then allow.
   - If verdict says `block-and-alert` → stop and show message.
6. Guardian records verdict + context for Adaptive Core.

Same pattern applies for DD and Enigmatic payment actions, with their
own extra fields.

---

## 9. Integration With Adaptive Core

Guardian MUST:

- log anonymised decision events (risk level, action, context hashes),
- receive **policy updates / hints** from Adaptive Core over time,
- support future dynamic policy adjustments (e.g. “tighten high-risk
  policy for the next 24h”).

The exact wire format is defined in `core/shield-bridge/adaptive-core-api.md`.

---

## 10. Implementation Notes (Non-Normative)

- Guardian logic SHOULD be implemented in a **pure, deterministic** core
  library that can run identically on web / iOS / Android.
- All platform-specific code (UI, OS APIs) must remain outside of this
  layer and only interact via well-defined functions / data structures.
- Where possible, Guardian should be **side-effect free** and treat the
  wallet state as an input, returning a verdict + updated annotations
  rather than mutating global state directly.

Future versions of this spec will:

- attach formal JSON schemas for ActionRequest and GuardianVerdict,
- define a test vector library for common scenarios,
- specify how Guardian degrades gracefully when shield endpoints are
  unreachable (e.g. offline mode).

