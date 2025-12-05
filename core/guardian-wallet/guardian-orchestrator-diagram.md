# Guardian → Wallet Orchestrator Diagram

**Goal:** visualize how Guardian Wallet components connect to wallet flows
and node backends inside the Adamantine architecture.

---

## 1. High-Level Diagram

```text
                 +------------------------------+
                 |         Mobile / Web         |
                 |    (Android / iOS / Web)     |
                 +---------------+--------------+
                                 |
                                 v
                       +------------------+
                       |  WalletService   |
                       | (core/wallet_    |
                       |      service.py) |
                       +---------+--------+
                                 |
          ------------------------------------------------
          |                                              |
          v                                              v
+--------------------------+                +--------------------------+
|   GuardianAdapter        |                |   Node Manager / Client  |
| (guardian_adapter.py)    |                |    (core/node/...)       |
+------------+-------------+                +-------------+------------+
             |                                               |
             v                                               v
   +---------------------+                         +-------------------+
   |   GuardianEngine    |                         |  DigiByte Node    |
   |     (engine.py)     |                         | (local/remote,    |
   +---------------------+                         |  Digi-Mobile, ...)|
                                                  +-------------------+
```

---

## 2. Data Flow (DGB Send Example)

1. UI → `WalletService.send_dgb(...)`
2. `WalletService` → `GuardianAdapter.evaluate_send_dgb(...)`
3. `GuardianAdapter` → `GuardianEngine.evaluate(ActionContext)`
4. `GuardianEngine` → `GuardianDecision` (ALLOW / REQUIRE_APPROVAL / BLOCK)
5. `WalletService`:
   - if BLOCK → return blocked result
   - if REQUIRE_APPROVAL → return pending result to UI
   - if ALLOW → call Node client to broadcast tx

---

## 3. Where GuardianPolicy Fits (Future)

```text
          +------------------+
          |  GuardianPolicy  |
          | (limits, YAML)   |
          +--------+---------+
                   |
                   v
            PolicyDecision
        (allow / require_auth /
         require_guardian / block)
```

- For simple deployments, only `GuardianEngine + GuardianAdapter` may be used.
- In more advanced setups, `GuardianPolicy` sits **before** the engine:
  - `block` → stop early
  - `require_guardian` → route into GuardianEngine
  - `allow` / `require_auth` → proceed with normal send flow.

---

This diagram is intentionally minimal and text-based so it can be read
directly in GitHub without additional rendering tools.
