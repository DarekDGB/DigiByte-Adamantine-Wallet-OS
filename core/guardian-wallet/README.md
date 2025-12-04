# 🛡 Guardian Wallet — Policy & Safety Engine

**Path:** `core/guardian-wallet/`  
**Status:** Draft implementation – experimental, not production‑ready.  

The *Guardian Wallet* module is the **local safety brain** of the Adamantine Wallet.  
It turns shield + risk signals and user preferences into **concrete decisions** for every sensitive action:

- ALLOW (silent pass-through)
- REQUIRE_APPROVAL (one or more guardians must approve)
- BLOCK (hard stop – action is not allowed)

This module does **not** talk directly to the blockchain.  
Instead, it sits between:

- the **wallet core** (sending transactions, minting DD, managing DigiAssets), and  
- the **risk / shield layers** (Risk Engine, Sentinel, DQSN, ADN, Adaptive Core).  

It is responsible for translating *human policies* into *machine‑enforceable rules* that can be audited and reasoned about.

---

## 1. Responsibilities

Guardian Wallet is designed to:

1. **Express policies** in a simple, declarative format (thresholds, scopes, actions).
2. **Evaluate actions** (send, mint, redeem, etc.) against those policies.
3. **Decide UX paths** – allow silently, ask for more confirmation, or block.
4. **Coordinate approvals** from trusted guardians (people, devices, or services).
5. **Log decisions** in a way the Risk Engine and analytics can consume later.

---

## 2. Directory Layout

```text
core/guardian-wallet/
  ├── configs.md          # Human-readable config formats and examples
  ├── engine.py           # GuardianEngine core logic
  ├── flows.md            # Where/when Guardian is invoked in wallet flows
  ├── guardian_config.py  # Load & validate GuardianConfig from dict/YAML
  ├── guardian_policy.py  # High level facade: "should we allow this action?"
  ├── models.py           # Dataclasses & enums for rules, guardians, approvals
  └── spec.md             # Design spec & background
```

### 2.1 `models.py`

Defines the core data types used everywhere else:

- **Guardian** – a person, device, or service that can approve actions.
  - `id`, `label`, `role`, `contact`, `status`
- **GuardianRule** – a single policy rule such as:
  - *“For wallet X, SEND over 10 000 DGB requires 2 approvals from guardians G1 + G2.”*
- **RuleScope** – where the rule applies:
  - `GLOBAL`, `WALLET`, or `ACCOUNT`
- **RuleAction** – what type of action is being guarded:
  - `SEND`, `MINT_DD`, `REDEEM_DD`, `MINT_ASSET`, etc.
- **GuardianVerdict** – `ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`
- **ApprovalRequest** – tracks a concrete request for guardian approval:
  - which rule fired, which guardians must respond, current status & tallies.

These models are shared by the engine, policy facade, tests, and (later) by UI adapters.

### 2.2 `guardian_config.py`

Provides **loading and validation** for static configuration, usually sourced from YAML:

- Which guardians exist for this wallet?
- Which rules are active?
- Default thresholds and per‑action overrides.

```python
from core.guardian_wallet.guardian_config import GuardianConfig

cfg = GuardianConfig.from_dict(raw_config)
engine = cfg.build_engine()  # returns GuardianEngine
```

This keeps all parsing / defaults / validation in one place, so the engine can stay focused on pure decision logic.

### 2.3 `engine.py`

Implements the **GuardianEngine** – the heart of the module.

Key pieces:

- `ActionContext` – everything the engine needs to know about an action:
  - action type, wallet/account ids, value, metadata/description, extra context.
- `GuardianEngine.evaluate(context)`
  - returns `(GuardianVerdict, ApprovalRequest | None)`
- `GuardianEngine.apply_decision(request, guardian_id, status, reason=None)`
  - updates an existing approval request when a guardian responds.

The engine currently supports a simple but powerful model:

- **No matching rules → ALLOW.**
- **Threshold rule with `threshold_value`**:
  - if value < threshold → `ALLOW`
  - if value ≥ threshold → `REQUIRE_APPROVAL` with `min_approvals` guardians
- **Block rule** (no threshold, `min_approvals == 0`) → `BLOCK`

This behaviour is covered by tests in `tests/test_guardian_engine.py`.

### 2.4 `guardian_policy.py`

A thin **facade** that wallet flows can call instead of talking to the engine directly.

It will eventually:

- combine static rules (from `GuardianConfig`)
- dynamic inputs (Risk Engine scores, shield signals, device posture)
- user‑level profiles (conservative / balanced / aggressive)

into a single decision function such as:

```python
decision = guardian_policy.evaluate_action(context, risk_summary)
```

Right now it wraps the engine and prepares the module for future richer policies.

### 2.5 `configs.md`, `flows.md`, `spec.md`

- **`configs.md`** – documentation and examples for YAML / JSON configs.
- **`flows.md`** – describes where Guardian is called in:
  - DGB sends
  - DigiAssets creation / transfer
  - DigiDollar mint / redeem
  - Enigmatic messaging flows
- **`spec.md`** – deeper design notes:
  - threat model
  - non‑goals
  - how Guardian interacts with Sentinel, Risk Engine, and Shield Bridge.

---

## 3. How Wallet Flows Use Guardian

Typical send flow:

1. Wallet builds a candidate transaction and value estimate.
2. Wallet constructs an `ActionContext` for the attempted operation.
3. Guardian is invoked:

   ```python
   verdict, req = engine.evaluate(context)
   ```

4. Wallet reacts:
   - `ALLOW` → proceed with standard biometric / PIN + broadcast.
   - `REQUIRE_APPROVAL` → create UX for guardian approvals
     - show which guardians are needed
     - track approvals / rejections
   - `BLOCK` → show clear message, do not broadcast.

5. When guardians respond, wallet calls `apply_decision` and proceeds only if the final status is approved.

---

## 4. Relationship to Shield & Risk Engine

Guardian Wallet is **local** and **user‑configured**.  
It does not make assumptions about global network risk on its own.

Instead, it is designed to plug into:

- **Risk Engine** – which aggregates Sentinel / DQSN / ADN / Adaptive Core signals.
- **Shield Bridge** – which exposes those signals to the wallet core.

Future work will allow rules such as:

- *“If risk score > 0.8, always require guardian approval, even for small sends.”*
- *“If node health is degraded or suspicious, block all DD mint/redeem.”*

These policies will live alongside value thresholds in the same rule system.

---

## 5. Testing

Unit tests live under:

- `tests/test_guardian_engine.py`

They currently verify:

- No rules → `ALLOW`
- Threshold rules below / above the limit
- Block rules without thresholds
- Multi‑guardian approval (2‑of‑N)
- Rejections overriding approvals

CI runs these tests on each push to ensure guardian behaviour remains stable as the wallet evolves.

---

## 6. Roadmap

Planned extensions include:

- Per‑contact trust levels (friends, exchanges, unknown recipients).
- Time‑based rules (night mode, travel mode, jurisdiction adaptation).
- Integration with device‑posture checks (rooted / jailbroken detection).
- Exportable policy snapshots for audits and incident analysis.
- UI surface for power users to manage guardians and rules directly.

---

*Guardian Wallet is the “safety layer with a face.”  
It turns the deep intelligence of the DigiByte Quantum Shield into decisions that normal users can understand, trust, and verify.*
