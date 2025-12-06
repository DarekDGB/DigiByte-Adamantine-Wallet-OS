# 🌐 Node Adapter — API Contract
Status: **draft v0.2 – aligned with Adamantine v0.2**

The **node adapter** is the thin layer between Guardian and a DigiByte node
(or compatible full node implementation).

It has two main jobs:

1. Provide a **clean, typed interface** to the node’s RPC / gRPC surface.
2. Export **NodeStatusSnapshot** and other context objects for Guardian scoring.

---

## 1. Design Notes

- reference implementation lives under `core/guardian_wallet/node/`
- talks to DigiByte via JSON‑RPC
- exposes a Python API used by Guardian engine
- may later grow its own local HTTP API for other processes

---

## 2. Core Python Interface

```python
class NodeAdapter:
    def get_status(self) -> NodeStatusSnapshot: ...
    def estimate_fee(self, target_blocks: int) -> int: ...
    def broadcast_raw_tx(self, tx_hex: str) -> str: ...
    def get_raw_mempool_summary(self) -> dict: ...
    def get_block_header(self, height: int) -> dict: ...
    def get_best_height(self) -> int: ...
    def test_lockdown_hook(self) -> bool: ...
```

`NodeStatusSnapshot` matches the schema in `guardian-schemas.md`.

---

## 3. Lockdown Hook

Guardian needs a way to enforce node‑level reflex actions provided by ADN v2.

Minimal interface:

```python
class NodeLockdownController:
    def enter_soft_lockdown(self, reason: str) -> None: ...
    def enter_hard_lockdown(self, reason: str) -> None: ...
    def clear_lockdown(self, actor: str, note: str = "") -> None: ...
    def get_lockdown_state(self) -> dict: ...
```

- soft lockdown → restricts new outbound TX, keeps node online for observation
- hard lockdown → severs peer connections, stops new blocks / tx relay

---

## 4. Configuration

Node adapter reads its settings from `guardian-config.yml` (`node_adapter` block).

Example:

```yaml
node_adapter:
  rpc_host: 127.0.0.1
  rpc_port: 14022
  rpc_user: digibyte
  rpc_pass: change_me
  timeout_seconds: 10
```

---

## 5. Error Semantics

- Network / RPC failures raise a **typed exception** which Guardian converts
  into a safe error response.
- Node adapter never crashes the whole process due to remote errors.
- In extreme cases Guardian may:
  - switch to **degraded mode** (e.g. block high‑value actions)
  - or trigger local lockdown if node appears compromised.

---

## 6. Future Extensions

- alternative backends (light clients, remote nodes)
- richer metrics streaming for Sentinel AI v2
- support for side‑chains / layer‑2 once defined in DigiByte ecosystem
