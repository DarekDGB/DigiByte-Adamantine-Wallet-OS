# DGB Guardian Wallet Layer — Configs (configs.md)

Status: **draft v0.1 – internal skeleton**

This document defines the **configuration surface** of the DGB Guardian
Wallet layer inside the DigiByte Adamantine Wallet.

It describes:

- what can be tuned by the **user**,
- what can be tuned by the **app / dev team**,
- how these configs are represented (YAML / JSON),
- how they map into the Guardian runtime.

Guardian configs are intentionally:

- explicit
- readable
- versioned
- safe-by-default.

---

## 1. Config Layers

There are three conceptual layers of configuration:

1. **Built‑in defaults**
   - shipped with the app
   - used when there is no override
   - conservative, safe.

2. **Profile & Account‑level user settings**
   - chosen by the user in the UI (“Safe Default”, “Paranoid”, etc.)
   - cannot break safety invariants (e.g. cannot fully disable blocking
     in certain edge conditions).

3. **Remote hints from Adaptive Core / Shield**
   - dynamic suggestions based on network conditions or active threats.
   - may temporarily tighten policies but should not silently weaken them.

Guardian merges these layers into an **effective runtime config**.

---

## 2. Risk Profile Config (risk-profiles.yml)

Primary mapping is defined in:

```text
config/risk-profiles.yml
```

Example structure (illustrative):

```yaml
version: 1

profiles:
  - id: "safe-default"
    label: "Safe Default"
    description: "Balanced protection with minimal friction."

    guardian_mode: "enforce"

    # Mapping from risk level → action for outgoing DGB sends
    send_dgb_policy:
      unknown:   "require-local-confirmation"
      low:       "allow"
      medium:    "require-local-confirmation"
      high:      "require-biometric"
      critical:  "block-and-alert"

    # Mapping for DD operations
    mint_dd_policy:
      unknown:   "require-biometric"
      low:       "require-local-confirmation"
      medium:    "require-biometric"
      high:      "require-passphrase"
      critical:  "block-and-alert"

    redeem_dd_policy:
      unknown:   "require-local-confirmation"
      low:       "allow"
      medium:    "require-biometric"
      high:      "require-passphrase"
      critical:  "block-and-alert"

    # Mapping for sensitive settings changes
    settings_policy:
      unknown:   "require-passphrase"
      low:       "require-biometric"
      medium:    "require-passphrase"
      high:      "block-and-alert"
      critical:  "block-and-alert"

  - id: "paranoid"
    label: "Paranoid"
    description: "Maximum safety, more friction."

    guardian_mode: "enforce"

    send_dgb_policy:
      unknown:   "require-passphrase"
      low:       "require-local-confirmation"
      medium:    "require-biometric"
      high:      "require-passphrase"
      critical:  "block-and-alert"

    mint_dd_policy:
      unknown:   "block-and-alert"
      low:       "require-passphrase"
      medium:    "require-passphrase"
      high:      "block-and-alert"
      critical:  "block-and-alert"

    redeem_dd_policy:
      unknown:   "require-passphrase"
      low:       "require-local-confirmation"
      medium:    "require-biometric"
      high:      "require-passphrase"
      critical:  "block-and-alert"

    settings_policy:
      unknown:   "block-and-alert"
      low:       "require-passphrase"
      medium:    "require-passphrase"
      high:      "block-and-alert"
      critical:  "block-and-alert"

  - id: "observe-only"
    label: "Observe Only"
    description: "No blocking, only warnings."

    guardian_mode: "observe"

    send_dgb_policy:
      unknown:   "allow"
      low:       "allow"
      medium:    "allow"
      high:      "allow"
      critical:  "allow"

    mint_dd_policy:
      unknown:   "allow"
      low:       "allow"
      medium:    "allow"
      high:      "allow"
      critical:  "allow"

    redeem_dd_policy:
      unknown:   "allow"
      low:       "allow"
      medium:    "allow"
      high:      "allow"
      critical:  "allow"

    settings_policy:
      unknown:   "allow"
      low:       "allow"
      medium:    "allow"
      high:      "allow"
      critical:  "allow"
```

The Guardian runtime:

- loads this file on startup,
- validates its schema and version,
- exposes the list of profiles to the Settings UI,
- caches the mapping tables for fast lookup.

---

## 3. Account-Level Guardian Settings

At the **account** level, the user can choose:

- which risk profile to use,
- a small set of overrides like “always require biometric for sends
  above X DGB”.

Conceptual structure (linked to `wallet-state.md`):

```ts
AccountGuardianConfig {
  risk_profile_id: string          // matches config/risk-profiles.yml

  // Optional per-account overrides
  min_biometric_for_sats?: number  // amounts above this require biometric
  min_passphrase_for_sats?: number // amounts above this require passphrase

  // Flags
  allow_offline_sends: boolean     // if false, block when shield offline
  allow_experimental_feeds: boolean
}
```

These values are stored per account and merged with the selected profile
to form the effective policy.

---

## 4. Global Guardian Settings (Per Profile)

Per **Profile**, the user may choose:

- the default risk profile for new accounts,
- whether Guardian is allowed to **escalate** automatically when
  shield reports sustained high risk.

```ts
ProfileGuardianConfig {
  default_risk_profile_id: string

  // If true, Guardian may temporarily tighten policy automatically
  // during high-risk periods (as advised by Adaptive Core).
  allow_adaptive_escalation: boolean

  // If false, user must manually opt in to escalations via prompt.
  require_manual_confirm_for_escalation: boolean
}
```

These values integrate with `Profile.security_level` as described in
`wallet-state.md`.

---

## 5. Built-In Hard Limits (Non-Configurable)

Some rules must **never** be bypassable via config:

- When shield detects a **critical, chain-wide emergency** (e.g.
  confirmed consensus split, catastrophic reorg), Guardian MUST enter
  **"global lock"** for affected actions regardless of local config.

- When device security state is clearly compromised (rooted/jailbroken
  + known exploit), Guardian MAY refuse to approve:
  - DD mints / redeems
  - large DGB sends
  - risk profile downgrades.

These hard limits are defined in code, not in YAML, and documented
here to make the behaviour clear and predictable.

---

## 6. Config Versioning

All Guardian-related config files must be versioned:

```yaml
version: 1
```

On startup, the runtime:

- checks version numbers,
- applies any necessary migrations,
- logs mismatches or unknown versions.

If a config file is missing or invalid:

- Guardian falls back to **built‑in safe defaults**,
- UI shows a warning in developer / diagnostics screens.

---

## 7. Developer / Diagnostics View

For developers and advanced users, Adamantine may expose a
**Diagnostics → Guardian** screen that shows:

- current risk profile,
- merged policy table (per action),
- last N verdicts with risk levels and actions,
- shield connectivity status.

This view is **read-only** and helps:

- test risk configs,
- debug unexpected behaviour,
- demonstrate Guardian decisions to auditors / users.

---

## 8. Future Extensions

Possible future config features:

- time-based policies (e.g. stricter at night or during certain windows),
- geo-based hints (without storing raw location),
- per-contact policy overrides (e.g. "always require biometric for this contact").

Any such additions must preserve:

- transparency,
- user control,
- and Guardian’s core safety guarantees.
