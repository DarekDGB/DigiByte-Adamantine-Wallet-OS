# Guardian Policy — Config-Driven Limits & Requirements

**Path:** `core/guardian-wallet/guardian_policy.py`  
**Status:** Draft – config/YAML policy evaluation, evolving.

The **Guardian Policy** layer interprets static configuration (usually YAML)
into simple, explainable decisions for wallet actions:

- `allow`
- `require_auth`
- `require_guardian`
- `block`

It is designed to be:

- **Pure & testable** – no network calls, no storage, no UI.
- **Config-driven** – fed by `GuardianConfig` built from YAML/JSON.
- **Complementary** to the runtime `GuardianEngine` + `GuardianAdapter`.

`GuardianPolicy` is ideal for **spending limits** and **baseline requirements**
that apply to whole wallets or accounts, independent of per-action guardian
approval workflows.

---

## 1. Core Types

### 1.1 `OperationContext`

High-level description of a pending wallet operation:

- `asset` – `"DGB"`, `"DD"`, `"DGA"` (DigiAssets), etc.
- `operation` – `"send"`, `"mint"`, `"redeem"`, `"transfer"`, ...
- `amount` – nominal amount in asset units
- `recent_window_spent` – how much has already been spent in the rolling window

This allows rules like:

> “In 24 hours, don’t let this wallet send more than 10 000 DGB.”

---

### 1.2 `PolicyDecision`

Structured result returned by `GuardianPolicy.evaluate(ctx)`:

- `decision` – one of:
  - `allow`
  - `require_auth`
  - `require_guardian`
  - `block`
- `reasons` – list of machine-friendly reason tags:
  - `["no_matching_rules"]`
  - `["spending_limit:rule_id", "critical_block:rule_id"]`
- `requirements` – list of `Requirement` objects from the config:
  - `device_pin`, `biometric`, `guardian_approval`, `out_of_band_confirmation`
- `rules_triggered` – IDs of the rules that contributed to the decision

Helper:

- `requires_any_guardian()` – returns True if any requirement needs a guardian.

---

## 2. Evaluation Algorithm

`GuardianPolicy` works over a `GuardianConfig` instance.

High-level flow:

1. Normalise:
   - `asset = ctx.asset.upper()`
   - `operation = ctx.operation.lower()`
2. Collect matching rules:
   - `matching = config.rules_for_operation(asset, operation)`
3. If no rules:
   - return `PolicyDecision(decision="allow", reasons=["no_matching_rules"], ...)`
4. For each rule:
   - check **spending limit** (if present)
   - collect **requirements**
   - escalate the decision:
     - `allow < require_auth < require_guardian < block`
   - mark **critical** rules that can block when over limit

Spending limit check:

- If `rule.spending_limit` is set:
  - compute `projected = ctx.recent_window_spent + ctx.amount`
  - if `projected > max_amount` → over limit, escalate

Critical rules:

- When `rule.severity == "critical"` **and** limit is breached:
  - escalate to `block`
  - add `critical_block:<rule_id>` to reasons.

If rules match but none add explicit requirements and no limit is breached,
the policy may return:

- `decision="allow"` with reason `["rules_match_but_no_extra_requirements"]`.

---

## 3. Relationship to GuardianEngine

`GuardianPolicy` and `GuardianEngine` serve different but complementary roles:

- **GuardianPolicy**:
  - driven by `GuardianConfig` built from YAML/JSON
  - focuses on **limits, severity, auth requirements**
  - returns simple decisions like `require_auth` or `require_guardian`

- **GuardianEngine**:
  - operates on `ActionContext`
  - manages **ApprovalRequest** state
  - handles multi-guardian 2-of-N workflows and explicit approvals

In Adamantine, a typical future flow might be:

1. Use `GuardianPolicy` to decide high-level stance:
   - if `block` → stop immediately
   - if `require_guardian` → route into GuardianEngine for detailed approvals
   - if `allow` or `require_auth` → proceed with local auth

This layering keeps:

- configuration logic in `GuardianConfig` + `GuardianPolicy`
- live approval logic in `GuardianEngine` + `GuardianAdapter`.

---

## 4. Example Usage

```python
from core.guardian_wallet.guardian_config import GuardianConfig
from core.guardian_wallet.guardian_policy import GuardianPolicy, OperationContext

cfg = GuardianConfig.from_dict(raw_config)
policy = GuardianPolicy(config=cfg)

ctx = OperationContext(
    asset="DGB",
    operation="send",
    amount=2_500,
    recent_window_spent=5_000,
)

decision = policy.evaluate(ctx)

if decision.decision == "block":
    # show critical warning
elif decision.decision == "require_guardian":
    # route into GuardianEngine-based approval flow
elif decision.decision == "require_auth":
    # enforce device PIN / biometric
else:
    # allow normally
```

---

## 5. Testing

Tests for `GuardianPolicy` (planned / WIP) will verify:

- spending-limit decisions (`allow` vs `require_guardian` vs `block`)
- escalation order correctness
- multiple rules combining into final decision
- requirement lists matching rule definitions

As the policy layer evolves, tests will ensure that changes remain
predictable and explainable to both developers and users.
