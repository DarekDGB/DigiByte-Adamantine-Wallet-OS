# 🛡 Guardian Wallet Flows

**Module:** `core/guardian-wallet/`  
**Scope:** How and *when* Guardian is invoked by Adamantine Wallet flows.

This document explains how wallet actions (send, DigiAssets, DigiDollar, Enigmatic)
call into the Guardian engine, and what the possible outcomes are from a user
experience point of view.

---

## 1. Components in the Flow

Guardian is not called directly from UI screens. Instead, the flow is:

1. **Wallet Core / Feature Engine**
   - DGB send logic
   - DigiAssets engine
   - DigiDollar (DD) engine
   - Enigmatic messaging layer

2. **GuardianAdapter (`guardian_adapter.py`)**
   - Maps a high-level operation (send, mint, redeem, asset op, Enigmatic flow)
     into a `ActionContext` + `RuleAction` for the engine.
   - Returns a `GuardianDecision` object.

3. **GuardianEngine (`engine.py`)**
   - Applies rules from configuration.
   - Outputs `GuardianVerdict` and optional `ApprovalRequest`.

4. **Guardian UI Payloads (`guardian_ui_payloads.py`)**
   - Convert verdict + approval request + config maps into a simple,
     serialisable `GuardianUIPayload` for Android / iOS / Web.

5. **Client UI (Android / iOS / Web)**
   - Renders the payload:
     - ALLOW → proceed with action.
     - REQUIRE_APPROVAL → show guardians, required approvals, progress.
     - BLOCK → show a clear message and stop the action.

---

## 2. DGB Send Flow

### 2.1 Trigger

User taps **Send** and fills in:

- amount
- destination address
- optional memo

Wallet core builds a candidate transaction and a value representation for
Guardian rules (e.g. DGB units or minor units).

### 2.2 Call Guardian

```python
from core.guardian_wallet.guardian_adapter import GuardianAdapter
from core.guardian_wallet.guardian_ui_payloads import build_ui_payload

adapter = GuardianAdapter(engine)  # engine from GuardianConfig
decision = adapter.evaluate_send_dgb(
    wallet_id="w1",
    account_id="a1",
    value_dgb=amount_dgb,
    description="User initiated DGB send",
    meta={"destination": dest_address},
)

ui_payload = build_ui_payload(
    verdict=decision.verdict,
    approval_request=decision.approval_request,
    rules=guardian_rules,
    guardians=guardian_registry,
    meta={"flow": "send_dgb"},
)
```

### 2.3 Outcomes

- **ALLOW**
  - UI shows standard confirmation (PIN/biometrics) and broadcasts TX.
- **REQUIRE_APPROVAL**
  - UI shows:
    - which guardians are needed,
    - how many approvals are required,
    - current status (pending / approved / rejected).
  - Wallet waits for enough approvals before signing & broadcasting.
- **BLOCK**
  - UI shows a clear message why the action is blocked (e.g. policy, limit).
  - No signing, no broadcast.

---

## 3. DigiAssets Flow

### 3.1 Operations

DigiAssets use the same Guardian infrastructure but with dedicated
RuleAction values when available:

- **Mint** – create new asset units.
- **Transfer** – send asset units to another address.
- **Burn** – destroy asset units.

### 3.2 Call Guardian

```python
decision = adapter.evaluate_digiasset_op(
    wallet_id="w1",
    account_id="assets_account",
    value_units=total_units,       # e.g. smallest asset units
    op_kind="mint",                # "mint" | "transfer" | "burn"
    description="Mint new DigiAsset",
    meta={"asset_symbol": symbol},
)

ui_payload = build_ui_payload(
    verdict=decision.verdict,
    approval_request=decision.approval_request,
    rules=guardian_rules,
    guardians=guardian_registry,
    meta={"flow": "digiasset_" + op_kind, "asset_symbol": symbol},
)
```

Outcome handling is identical to DGB sends:
ALLOW → proceed, REQUIRE_APPROVAL → wait for guardians, BLOCK → stop.

---

## 4. DigiDollar (DD) Mint / Redeem

### 4.1 Overview

The DigiDollar engine (`modules/dd_minting/`) already performs:

- oracle pricing,
- risk / guardian integration,
- Tx planning.

Guardian sits in front of **mint** and **redeem** actions as an extra
policy layer.

### 4.2 Mint Flow (DGB → DD)

1. User requests a quote.
2. Wallet shows how much DD would be minted.
3. When user confirms, wallet calls Guardian via the adapter:

```python
decision = adapter.evaluate_mint_dd(
    wallet_id="w1",
    account_id="a1",
    dgb_value_in=quote.dgb_side.dgb,
    description="Mint DigiDollar (DD)",
    meta={"flow": "dd_mint"},
)
```

4. `build_ui_payload(...)` converts the result to UI form.

- If **ALLOW** → DD engine builds a Tx plan, wallet signs + broadcasts.
- If **REQUIRE_APPROVAL** → guardians must approve the mint.
- If **BLOCK** → no mint; UI shows why.

### 4.3 Redeem Flow (DD → DGB)

Identical pattern, but using `evaluate_redeem_dd(...)` and a `flow` meta of
`"dd_redeem"`.

---

## 5. Enigmatic Messaging

Certain Enigmatic Layer-0 operations may also be guarded, especially
if they:
- move value,
- represent governance actions,
- or perform sensitive signalling on-chain.

### 5.1 Call Guardian

```python
decision = adapter.evaluate_enigmatic_message(
    wallet_id="w1",
    account_id="msg_account",
    value_dgb=estimated_cost_dgb,
    description="Enigmatic Layer-0 message",
    meta={"flow": "enigmatic_message"},
)

ui_payload = build_ui_payload(
    verdict=decision.verdict,
    approval_request=decision.approval_request,
    rules=guardian_rules,
    guardians=guardian_registry,
    meta={"flow": "enigmatic_message"},
)
```

Wallet then follows the standard ALLOW / REQUIRE_APPROVAL / BLOCK pattern.

---

## 6. Guardian Approvals Lifecycle

### 6.1 When REQUIRE_APPROVAL is returned

- The wallet stores the `ApprovalRequest` (id, rule, guardians, status).
- UI displays an approval screen, including:
  - summary of the action,
  - list of guardians,
  - current approval status.

### 6.2 Guardians Respond

As guardians approve or reject (via whatever channel is implemented), the
wallet calls:

```python
engine.apply_decision(
    approval_request,
    guardian_id="g1",
    status=ApprovalStatus.APPROVED,  # or REJECTED
    reason="optional note",
)
```

The `ApprovalRequest` object updates its internal tallies and status.

### 6.3 Action Completion

- If the final status becomes **APPROVED** → wallet proceeds with signing
  and broadcasting.
- If **REJECTED** → wallet permanently blocks the action and updates UI.
- If still **PENDING** → wallet keeps waiting or times out, depending on
  UX policy.

---

## 7. Notes & Future Extensions

- Guardian flows can be extended with **risk scores** from Sentinel / DQSN /
  ADN / Adaptive Core by embedding them into `meta` or additional context.
- Per-contact trust levels and dynamic travel / jurisdiction modes can
  be plugged into the same adapter and UI payloads without changing
  calling code.
- For light clients, approvals can be synced over Enigmatic or other
  off-chain messaging channels.

Guardian flows are intentionally **modular** so Adamantine can evolve from
simple threshold rules into a rich, shield-driven policy engine without
breaking existing wallet logic.
