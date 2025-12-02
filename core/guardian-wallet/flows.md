# DGB Guardian Wallet Layer — Flows (flows.md)

Status: **draft v0.1 – internal skeleton**

This document describes the **main runtime flows** of the DGB Guardian
Wallet layer inside the DigiByte Adamantine Wallet.

It complements `spec.md` by showing **how** Guardian is called from the
UI and **how** it interacts with Shield Bridge, Risk Engine and TX
Builder for common actions.

The goal is to keep flows:

- deterministic
- auditable
- easy to test with fixtures and replay logs.

---

## 1. Common Flow Pattern

All guarded actions follow the same high-level pattern:

```text
[ UI ] → build ActionRequest
      → Guardian.evaluate(request)
      → Guardian returns GuardianVerdict
      → UI interprets verdict
      → (optional challenge)
      → TX Builder / Module executes or aborts
```

The only difference between actions is:

- which fields are populated in `ActionRequest.extras`
- which modules consume the verdict (TX builder, DD engine, Enigmatic).

---

## 2. Send DGB Flow

### 2.1 Preconditions

- User has selected:
  - `from` account
  - `to` address or contact
  - amount in DGB (sats)
- Wallet has:
  - fresh balance / UTXO view
  - up-to-date ShieldIntegrationState (or at least last-known status)

### 2.2 Steps

```text
1. UI collects input:
   - from_account_id
   - to_address / to_contact
   - amount_sats

2. UI snapshots environment:
   - DeviceSecuritySnapshot
   - NetworkStateSnapshot

3. UI builds ActionRequest:

   kind          = "send-dgb"
   profile_id    = currentProfile.id
   account_id    = from_account_id
   amount_sats   = X
   from_address  = (optional – if chosen)
   to_address    = resolved DGB address
   to_contact_id = (optional – if a contact was used)

4. UI calls:

   verdict = Guardian.evaluate(actionRequest)

5. Guardian:
   a) Reads Risk Profile for this account.
   b) Queries Shield Bridge for:
      - sentinel summary
      - dqsn node health
      - adn node status
      - qac confirmation pattern (if relevant)
      - adaptive core hints
   c) Runs local heuristics:
      - contact trust level / risk flags
      - new vs known address
      - abnormal amount (relative to history)
      - device security posture
   d) Aggregates to RiskLevel.
   e) Maps RiskLevel → GuardianAction via profile.
   f) Returns GuardianVerdict.

6. UI interprets verdict:

   if action = "allow":
       proceed → TX Builder
   if action in {"require-local-confirmation", "require-biometric",
                 "require-passphrase"}:
       run challenge flow, then (if passed) proceed → TX Builder
   if action = "delay-and-retry":
       show message, schedule retry
   if action = "block-and-alert":
       show blocking message, abort

7. TX Builder constructs raw transaction, signs and broadcasts,
   or aborts if Guardian blocked.

8. Guardian logs outcome (including whether user overrode or cancelled)
   to feed Adaptive Core.
```

---

## 3. Mint DD Flow

Minting DD is more sensitive than a normal send because it:

- **locks backing UTXOs** for DD issuance,
- may involve oracle checks,
- may be a target for sophisticated attacks.

### 3.1 Preconditions

- User has chosen:
  - `from` account for backing DGB
  - target DD amount (or DGB to convert)
- Wallet knows:
  - backing UTXOs candidate set
  - current oracle state (if used)

### 3.2 Steps

```text
1. UI collects DD mint inputs:
   - backing_account_id
   - desired_dd_amount or backing_sats
   - chosen settlement address (if applicable)

2. UI snapshots environment:
   - DeviceSecuritySnapshot
   - NetworkStateSnapshot

3. UI builds ActionRequest:

   kind        = "mint-dd"
   profile_id  = currentProfile.id
   account_id  = backing_account_id
   amount_dd   = desired_dd_amount (if known)
   amount_sats = implied or explicit backing value

   extras = {
     "mint_mode": "onchain" | "other",
     "oracle_snapshot": { ... }   // optional summary
   }

4. UI calls Guardian.evaluate(request).

5. Guardian:
   - pulls Risk Profile
   - queries Shield Bridge
   - checks for:
     - high mempool / reorg risk
     - unusual backing pattern
     - suspicious node health
     - recent shield alerts affecting DD
   - aggregates RiskLevel
   - maps to GuardianAction
   - returns GuardianVerdict.

6. UI interprets verdict:
   - If `allow` or `allow-with-challenge` → proceed to DD engine.
   - If `block-and-alert` → show reason (e.g. "Network unstable for mint").

7. DD engine:
   - selects backing UTXOs
   - constructs and submits mint transaction(s)
   - updates DigiDollarState.

8. Guardian logs event for Adaptive Core.
```

---

## 4. Redeem DD Flow

Redeeming DD unlocks backing UTXOs and may be abused to drain reserves
if compromised. Guardian must treat anomalous redeems as high risk.

Flow is analogous to Mint DD:

```text
1. User selects a DD position or amount to redeem.
2. UI builds ActionRequest with kind = "redeem-dd".
3. Guardian evaluates as above.
4. Verdict decides whether DD engine proceeds.
5. TX Builder + DD engine construct redeem TXs.
6. Guardian logs for Adaptive Core.
```

Additional heuristics:

- large redeem after a long idle period → higher risk
- redeem to a new unseen address → higher risk
- multiple rapid redeems from same device → suspicious.

These heuristics belong to the Risk Engine but are orchestrated here.

---

## 5. Enigmatic Payment Request Flow

Enigmatic itself handles messaging, but Guardian protects actions that
**move value** or **trigger sensitive operations** based on messages.

Example: A contact sends a payment request via Enigmatic.

```text
1. Enigmatic module receives a signed payment request message.
2. Module parses, verifies signature and constructs a proposed action:

   kind        = "send-dgb" (or "mint-dd", etc.)
   from_account_id = ...
   to_contact_id   = ...
   amount_sats     = ...

3. Instead of executing directly, module passes this to Guardian
   as an ActionRequest (same as manual send, just with origin = "enigmatic").

4. Guardian evaluates using:
   - contact trust level
   - past history with this contact
   - shield signals
   - device security
   - amount and novelty of address.

5. UI shows:
   - the request details
   - Guardian’s warnings or approvals.

6. User can accept / reject, but execution still flows through Guardian
   as in the standard send case.
```

This ensures Enigmatic cannot bypass Guardian policy.

---

## 6. Settings Change Flow

Certain settings changes are sensitive:

- switching to a custom node
- disabling Guardian
- lowering risk profile
- enabling experimental shield feeds

For such actions:

```text
1. UI constructs ActionRequest with kind = "settings-change".
2. Includes details in `extras` (e.g. "disable_guardian": true).
3. Guardian evaluates:
   - may require biometric / passphrase
   - may block entirely if policy forbids.
4. If verdict allows, settings module applies the change.
```

This prevents malware / remote control from silently weakening the wallet.

---

## 7. Degraded / Offline Mode

When Shield endpoints are partially or fully unreachable:

- Shield Bridge reports `status = "degraded"` or `"offline"`.
- Risk Engine marks certain signals as stale or unavailable.
- Guardian MUST degrade **safely**:

Examples:

```text
- If shield is offline but device is healthy and contact is trusted:
    allow small sends with local heuristics, block large ones.

- If shield is degraded and network appears unstable:
    tighten policy for all sends (e.g. treat as at least "medium" risk).
```

These degradation strategies will be defined in more detail in
`core/risk-engine/scoring-rules.md`, but flows here must assume that
**some data is sometimes missing** and still behave safely.

---

## 8. Logging & Telemetry Hooks

For every evaluated action Guardian SHOULD:

- create a **decision log entry** with:
  - action kind
  - risk level
  - guardian action
  - shield status summary
  - anonymised context hashes
- expose this to:
  - Adaptive Core (for learning)
  - local analytics (if enabled and privacy-approved).

Logs MUST:

- avoid storing raw addresses where possible
- avoid storing exact amounts unless user opts in
- be protected by the same encryption model as other sensitive metadata.

---

## 9. Testability

These flows are designed to be:

- reproducible via JSON fixtures (ActionRequest → GuardianVerdict),
- testable without network access (using mocked Shield Bridge),
- extensible as new modules (e.g. additional asset types) appear.

Dedicated test vectors will be documented in `tests/risk-engine-tests.md`.
