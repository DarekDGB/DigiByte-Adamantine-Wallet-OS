# ⚙️ Guardian Wallet — Configuration
Status: **draft v0.2 – aligned with Adamantine v0.2**

Guardian configuration is loaded from:

1. `guardian-config.yml` (or `.toml` / `.json` in future)
2. Environment variables
3. Optional remote overrides from Shield Network / operator console

This document describes the **reference YAML layout**.

---

## 1. File Location & Basics

Default search order:

1. `${ADAMANTINE_DATA_DIR}/guardian/guardian-config.yml`
2. `${XDG_CONFIG_HOME}/adamantine/guardian-config.yml`
3. `./guardian-config.yml` (development only)

Environment override:

- `GUARDIAN_CONFIG_PATH=/path/to/custom.yml`

---

## 2. Minimal Example

```yaml
wallet_id: adamantine-main

network: mainnet           # mainnet | testnet | regtest

node_adapter:
  rpc_host: 127.0.0.1
  rpc_port: 14022
  rpc_user: digibyte
  rpc_pass: change_me
  timeout_seconds: 10

limits:
  daily_spend_dgb: 10000
  single_tx_max_dgb: 5000

risk_weights:
  sentinel: 0.2
  dqsn: 0.2
  adn: 0.2
  qwg: 0.2
  adaptive_core: 0.2

lockdown:
  enabled: true
  auto_lockdown_on_critical: true
  require_manual_clear: true

logging:
  level: info          # debug | info | warning | error
  path: guardian.log

ui:
  require_second_factor_over_dgb: 1000
  show_risk_banner_over_level: medium
```

---

## 3. Limits Block

```yaml
limits:
  daily_spend_dgb: 10000
  single_tx_max_dgb: 5000
  inbound_high_value_confirmations: 25
  offline_mode_max_dgb: 50
```

- These values are fed into the **policy model**.
- Shield Network and Adaptive Core may **tighten** them but never loosen
  beyond configured hard minimums (see below).

```yaml
hard_minimums:
  daily_spend_dgb: 1000
  single_tx_max_dgb: 500
```

---

## 4. Risk Weights

Weights applied when aggregating scores from each layer.

```yaml
risk_weights:
  sentinel: 0.25
  dqsn: 0.25
  adn: 0.2
  qwg: 0.15
  adaptive_core: 0.15
```

Values should sum to **1.0**.  
Guardian will normalise if they are slightly off.

---

## 5. Lockdown Behaviour

```yaml
lockdown:
  enabled: true
  auto_lockdown_on_critical: true
  require_manual_clear: true
  notify_channels:
    - log
    - ui_banner
    - optional_webhook
  webhook_url: "https://example.com/guardian/alerts"
```

When lockdown is active:

- all new outbound transactions are blocked
- high‑risk inbound funds are quarantined
- UI shows a persistent warning

---

## 6. Integration with Shield Network

```yaml
shield_bridge:
  enabled: true
  endpoint: "http://127.0.0.1:9050"
  auth_token: "local-secret-token"
  send_events: true
  accept_overrides: true
  max_remote_policy_tightening:
    factor: 0.5   # can cut limits by up to 50%
```

- if `accept_overrides=false`, Guardian will still send telemetry but will
  not accept remote policy changes.

---

## 7. Environment Variables

- `GUARDIAN_CONFIG_PATH`
- `GUARDIAN_RPC_BIND` (override default bind for Guardian API itself)
- `GUARDIAN_LOG_LEVEL`
- `GUARDIAN_SHIELD_BRIDGE_TOKEN`

Environment variables always override file config for the same key.

---

## 8. Validation & Reload

- On startup, Guardian validates:
  - YAML syntax
  - required keys
  - risk weight normalisation
- Hot‑reload path (optional implementation):
  - `SIGHUP` on Unix
  - or `POST /admin/reload-config` (not part of public API surface)

Any reload is written into audit log as a `GuardianEvent` with type
`config_reload`.
