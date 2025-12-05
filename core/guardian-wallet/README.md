# 🛡 Guardian Wallet — Policy, Approvals & Safety Engine

**Path:** `core/guardian-wallet/`  
**Status:** Draft implementation – experimental, evolving rapidly.  

The *Guardian Wallet* module is the **local protection layer** inside the Adamantine Wallet.  
It converts thresholds, rules, guardian approvals, and (later) Shield-based risk signals into clear, enforceable decisions:

- **ALLOW** – normal action, proceed  
- **REQUIRE_APPROVAL** – one or more guardians must approve  
- **BLOCK** – stop immediately  

Guardian Wallet **does not** broadcast transactions, talk to DigiByte Core, or perform networking.  
It acts as the **decision brain** between:

- the **wallet flows** (DGB sends, DD mint/redeem, DigiAssets), and  
- the **Shield layers** (Risk Engine, Sentinel, DQSN, ADN, Adaptive Core).

It translates human-understandable policies into **machine-enforced safety**.

---

## 1. Responsibilities

Guardian Wallet is designed to:

1. **Define rules** (thresholds, action types, required guardians).
2. **Evaluate actions** through the GuardianEngine.
3. **Support approvals** (multi-guardian 2-of-N, rejections, overrides).
4. **Apply stricter limits** through GuardianPolicy (config/YAML).
5. **Provide structured decisions** to the wallet UX and orchestrator.
6. **Prepare for deep integration** with Shield & Risk Engine.

Two complementary paths exist:

### **A. GuardianEngine (runtime, granular approvals)**  
- action-by-action evaluation  
- handles multi-guardian approval workflows  
- used by wallet flows (send, DigiAssets, DigiDollar)

### **B. GuardianPolicy (static config / YAML limit checks)**  
- interprets GuardianConfig  
- works for value limits, auth requirements  
- future home for risk-dependent policies

---

## 2. Directory Layout

```
core/guardian-wallet/
  ├── configs.md             # Human-readable config formats and examples
  ├── engine.py              # Main GuardianEngine runtime logic
  ├── flows.md               # How/when Guardian is invoked in wallet flows
  ├── guardian_adapter.py    # High-level adapter for wallet flows (SEND/DD/Assets)
  ├── guardian_config.py     # Load & validate GuardianConfig from dict/YAML
  ├── guardian_policy.py     # Limit-checking / requirement-based policies
  ├── models.py              # Core dataclasses & enums for rules/guardians
  └── spec.md                # Deep design notes and architecture
```

---

## 3. Component Overview

### 3.1 `models.py`
Shared data types:

- **Guardian** – person/device/service that can approve actions  
- **GuardianRule** – thresholds, approvals, scopes  
- **RuleAction** – SEND, MINT_DD, REDEEM_DD, MINT_ASSET, etc.  
- **GuardianVerdict** – `ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`  
- **ApprovalRequest** – stateful multi-guardian approval object  

These models power both `engine.py` and `guardian_policy.py`.

---

### 3.2 `guardian_config.py`
Parses YAML → structured config → builds engine-ready rule sets.

```python
cfg = GuardianConfig.from_dict(raw)
engine = cfg.build_engine()
```

Keeps parsing, validation, defaults, and schema consistency in one place.

---

### 3.3 `engine.py`
**The core approval engine.**

Responsible for:

- matching rules  
- evaluating thresholds  
- producing a verdict  
- generating ApprovalRequest objects  
- applying guardian decisions (`apply_decision`)  

Rules behave as:

| Rule Structure | Behaviour |
|----------------|-----------|
| No rule match | `ALLOW` |
| Threshold rule (`value >= threshold`) | `REQUIRE_APPROVAL` |
| Block rule (`min_approvals == 0`, no threshold) | `BLOCK` |

All tested in:  
`tests/test_guardian_engine.py`

---

### 3.4 `guardian_adapter.py`
A *high-level bridge* between wallet flows and GuardianEngine.

Provides clean helpers:

- evaluate_send_dgb  
- evaluate_mint_dd  
- evaluate_redeem_dd  
- evaluate_digiasset_op  
- evaluate_enigmatic_message  

Wallets never touch rules directly—only this adapter.

---

### 3.5 `guardian_policy.py`
A **parallel evaluation path** for YAML/static policies.

Used for:

- spending limits  
- basic auth requirements  
- early risk-aware policies in future versions  

Produces a structured `PolicyDecision`:

```
allow / require_auth / require_guardian / block
```

Both systems coexist:

- **GuardianEngine:** live approval workflow  
- **GuardianPolicy:** config-driven constraints  

---

## 4. How Wallet Flows Use Guardian

### Example: user sends DGB

1. Build `ActionContext`  
2. Engine evaluates:

```
verdict, req = engine.evaluate(ctx)
```

3. Wallet reacts:
   - `ALLOW` → proceed  
   - `REQUIRE_APPROVAL` → guardian UI  
   - `BLOCK` → stop  

4. When guardians respond:

```
engine.apply_decision(request, guardian_id="g1", status="APPROVED")
```

---

## 5. Guardian + Shield + Risk Engine (future)

Guardian Wallet will integrate with:

- Sentinel AI v2  
- DQSN  
- ADN  
- Adaptive Core  

to escalate rules automatically.

---

## 6. Testing

Tests verify:

- threshold behaviour  
- block rules  
- multi-guardian flows  
- rejections overriding approvals  
- YAML config policy decisions  

---

## 7. Roadmap

- Device posture detection  
- Travel/jurisdiction modes  
- Rolling time-window spending limits  
- Guardian groups  
- Risk-adaptive escalation  
- Exportable audit logs  

---

**Guardian Wallet is the safety heart of Adamantine —  
the layer that turns shield intelligence into user-trustable decisions.**
