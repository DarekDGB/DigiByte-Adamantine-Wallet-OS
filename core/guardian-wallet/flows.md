# Guardian Wallet Flows — How Safety Hooks Into Adamantine

**Path:** `core/guardian-wallet/flows.md`  
**Status:** Draft – describes how Guardian integrates with wallet flows.

This document explains **where** and **how** the Guardian Wallet module
is invoked in the Adamantine architecture:

- DGB sends
- DigiAssets operations
- DigiDollar (DD) mint / redeem
- Enigmatic Layer-0 messaging

It focuses on the interplay between:

- `GuardianEngine` + `GuardianAdapter`
- (future) `GuardianPolicy`
- `WalletService`
- Node clients (local or remote)

---

## 1. Components Involved

- **GuardianEngine (`engine.py`)**  
  Evaluates rules and produces:
  - `GuardianVerdict` (`ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`)
  - optional `ApprovalRequest`

- **GuardianAdapter (`guardian_adapter.py`)**  
  High-level bridge with helpers like:
  - `evaluate_send_dgb(...)`
  - `evaluate_mint_dd(...)`
  - `evaluate_redeem_dd(...)`
  - `evaluate_digiasset_op(...)`
  - `evaluate_enigmatic_message(...)`

- **GuardianPolicy (`guardian_policy.py`)**  
  Limit-based, config-driven decisions:
  - `allow`
  - `require_auth`
  - `require_guardian`
  - `block`  
  (future: used as an outer layer before the engine)

- **WalletService (`core/wallet_service.py`)**  
  Orchestrates:
  - GuardianAdapter
  - node manager / node client
  - high-level send/mint flows

---

## 2. DGB Send Flow (High-Level)

**Goal:** user sends DGB from account A → address B.

1. UI collects:
   - source account
   - destination address
   - amount

2. `WalletService.send_dgb(...)` is called with:
   - `wallet_id`
   - `account_id`
   - `to_address`
   - `amount_minor` (DGB units in chosen convention)
   - description

3. `WalletService` calls:

   ```python
   decision = guardian_adapter.evaluate_send_dgb(
       wallet_id=wallet_id,
       account_id=account_id,
       value_dgb=amount_minor,
       description=description,
       meta={"to_address": to_address},
   )
   ```

4. Based on `GuardianDecision`:
   - if `decision.is_blocked()`:
     - return blocked status, do **not** talk to the node
   - if `decision.needs_approval()`:
     - return pending status, prompt for guardian approval in UI
   - if `decision.is_allowed()`:
     - proceed to build/broadcast transaction via node client

5. Node client (local or remote) broadcasts the transaction.

---

## 3. DigiAssets Flows

### 3.1 Asset Creation / Issuance

For creation or issuance, wallet code calls:

- `evaluate_asset_creation(...)`
- `evaluate_asset_issuance(...)`

These are thin wrappers around `evaluate_digiasset_op(...)` with appropriate
metadata (e.g. `asset_id`, `amount`).

Guardian can be configured to:

- allow small test assets freely
- require approvals for large or “official” asset issuances
- block certain high-risk patterns

### 3.2 Asset Transfer

Transfers use:

```python
evaluate_asset_transfer(
    wallet_id=...,
    account_id=...,
    asset_id="...",
    amount=...,
    description="Transfer DigiAsset units",
    meta={...},
)
```

The verdict drives whether:

- the transfer proceeds normally
- additional guardian steps are required
- the operation is blocked

### 3.3 Asset Burn

Burns use:

```python
evaluate_asset_burn(...)
```

This allows policies such as:

- require confirmation / approvals before destroying valuable assets.

---

## 4. DigiDollar (DD) Mint / Redeem

DigiDollar-specific helpers:

- `evaluate_mint_dd(...)`
- `evaluate_redeem_dd(...)`

Flow sketch:

1. UI initiates a **mint** (DGB → DD) or **redeem** (DD → DGB).
2. Wallet code calls the respective helper.
3. Guardian verdict decides:
   - small operations → allowed seamlessly
   - large operations → require guardian approvals
   - suspicious / high-risk scenarios → blocked

When combined with Shield/Risk Engine (future), rules can say:

- if oracle or node risk is high → always require guardian approval
- if risk extreme → block all DD operations until safe.

---

## 5. Enigmatic Layer-0 Messaging

Enigmatic flows can also be guarded via:

```python
evaluate_enigmatic_message(...)
```

Possible policies:

- treat certain Enigmatic dialects (e.g. governance / high-risk intents)
  as protected actions
- require guardian approvals for governance or administration messages
- block messages that exceed particular thresholds or patterns.

This integrates Layer-0 messaging into the same approval framework as
standard wallet actions.

---

## 6. Future: GuardianPolicy Outer Layer

A future version of wallet flows may:

1. Call **GuardianPolicy** first:
   - quickly decide `allow` / `require_auth` / `require_guardian` / `block`
   - based on YAML limits and severity
2. If `require_guardian`, route into **GuardianEngine** via **GuardianAdapter**
   to manage detailed approval state.
3. If `block`, stop before building or signing any transaction.

This layering keeps:

- configuration and limits in `GuardianConfig` + `GuardianPolicy`
- live approval logic in `GuardianEngine` + `GuardianAdapter`.

---

## 7. Notes for Client Implementers

- Android / iOS / Web clients should **not** interpret Guardian rules themselves.  
  They should:
  - call WalletService / GuardianAdapter
  - react to the `GuardianDecision` or high-level flow result
- Approvals UI should be generic:
  - list guardians
  - show required vs current approvals
  - handle approval / rejection statuses
- Logs & analytics can use:
  - rule IDs
  - decision types
  - basic reason tags

This keeps the Guardian logic centralised and auditable.
