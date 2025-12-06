# 🛡 Guardian Wallet — API Contract
Status: **draft v0.2 – aligned with Adamantine v0.2 architecture**

Guardian is the **policy + decision engine** inside the DigiByte Adamantine Wallet.
It sits between:

- the **UI / client apps** (android / ios / web)
- the **local node adapter** (core/guardian_wallet/node/)
- the **Shield Bridge** into the DigiByte Quantum Shield Network (DQSN, ADN, QWG, Adaptive Core)

Guardian does **not** sign, broadcast, or mine blocks by itself.  
It *decides whether something is allowed to happen* and returns a verdict + metadata.

---

## 1. High‑Level Responsibilities

Guardian API is used for:

1. **Policy‑Aware Transaction Flow**
   - pre‑flight checks before signing
   - post‑flight checks before broadcasting
   - optional “dual‑control” approvals for high‑risk actions

2. **Risk‑Informed Decisions**
   - pulls scores from:
     - Sentinel AI v2 (telemetry)
     - DQSN v2 (network‑wide confirmation)
     - ADN v2 (node‑level reflex / lockdown)
     - QWG (quantum‑aware key posture)
     - Adaptive Core (long‑term immune memory / models)
   - aggregates into a single **guardian_risk_score** and **verdict**

3. **Wallet‑Level Protections**
   - daily / weekly withdrawal limits
   - per‑asset policies (DGB, DigiAssets, DigiDollar)
   - device trust & behavioural fingerprints
   - “guardian challenge” for sensitive actions (PIN / biometric / second device)

All calls are **local** (Unix domain socket / 127.0.0.1 HTTP) in Adamantine reference implementation.

---

## 2. Base Transport & Formats

- Transport: HTTP/1.1 or local IPC (implementation detail)
- Encoding: JSON (binary / gRPC can be added later)
- Auth: local token (for UI) + internal service tokens (for node adapter / bridge)
- Versioning: `X-Guardian-Version: 0.2` header

All responses follow:

```jsonc
{
  "ok": true,
  "verdict": "allow | warn | block | require_second_factor",
  "guardian_risk_score": 0.0,
  "guardian_risk_level": "low | medium | high | critical",
  "reason": "short human readable text",
  "details": { "… engine‑specific payloads …" },
  "correlation_id": "uuid-v4",
  "timestamp": "RFC3339"
}
```

---

## 3. Core Endpoints

### 3.1 `POST /v0/tx/preflight`

Ask Guardian whether a **proposed transaction** should be allowed to proceed to signing.

**Request**

```jsonc
{
  "wallet_id": "adamantine-main",
  "account_id": "default-dgb",
  "client": "android | ios | web | cli",
  "tx_template": {
    "inputs": [ "…" ],
    "outputs": [ "…" ],
    "fee_sats": 1200,
    "network": "mainnet | testnet | regtest"
  },
  "context": {
    "purpose": "payment | digiasset_transfer | digidollar_mint | admin",
    "user_ip_hash": "…",
    "device_id": "…",
    "geo_hint": "…",
    "ui_locale": "en-GB"
  }
}
```

**Behaviour**

- runs **Guardian scoring pipeline**
- consumes signals from Shield Bridge (if available)
- returns verdict + risk score
- MAY suggest **policy modifications** (e.g. reduce amount, increase confirmations)

---

### 3.2 `POST /v0/tx/postflight`

Called **after signing but before broadcast**.

Purpose:
- re‑validate the exact signed TX (id, size, scripts, fees)
- check real‑time changes: mempool state, reorg risk, network alerts
- allow **last‑second lockdown** if something changed since pre‑flight

Request minimally includes:

```jsonc
{
  "wallet_id": "adamantine-main",
  "account_id": "default-dgb",
  "signed_tx_hex": "…",
  "txid": "…",
  "preflight_correlation_id": "uuid-v4"
}
```

Response shape is the standard Guardian envelope.  
If verdict = `block`, the wallet **must not broadcast**.

---

### 3.3 `POST /v0/policy/simulate`

Dry‑run “what would Guardian say if…?”

- used by UI to explain to user why something would be blocked
- used by operators to **tune rules**

Request:

```jsonc
{
  "wallet_id": "adamantine-main",
  "account_id": "default-dgb",
  "scenario": {
    "amount_dgb": 123.45,
    "destination": "D…",
    "frequency_hint": "one_off | recurring",
    "asset_type": "dgb | digiasset | digidollar"
  }
}
```

---

### 3.4 `GET /v0/policy/state`

Returns **current effective policy** for a wallet / account after merging:

- static config (`guardian-config.yml`)
- remote overrides from Shield Network
- adaptive “learned” constraints from Adaptive Core

Response (abridged):

```jsonc
{
  "wallet_id": "adamantine-main",
  "account_id": "default-dgb",
  "limits": {
    "daily_spend_dgb": 10_000,
    "single_tx_max_dgb": 5_000
  },
  "requirements": {
    "second_factor_for_high_risk": true,
    "min_confirmations_for_large_inbound": 25
  },
  "sources": {
    "static": true,
    "dqsn": true,
    "adaptive_core": true
  }
}
```

---

### 3.5 `POST /v0/event/notify`

Fire‑and‑forget event ingest from UI / node adapter:

- login attempts
- device fingerprint changes
- abnormal behaviour (e.g. 100 failed PIN entries)
- new key imports / exports

These events are forwarded into:

- local risk history
- Sentinel / DQSN feeds (through Shield Bridge)
- Adaptive Core long‑term models

---

## 4. Error Handling

Guardian never leaks sensitive internals in errors.

```jsonc
{
  "ok": false,
  "error_code": "GUARDIAN_CONFIG_MISSING | BACKEND_UNAVAILABLE | INVALID_REQUEST | RATE_LIMITED",
  "reason": "short message safe to show to user",
  "correlation_id": "uuid-v4"
}
```

Wallet UIs **must** treat any `ok=false` as equivalent to `verdict = "block"`
unless explicitly whitelisted in UX (e.g. “backend offline, operate in
degraded offline‑only mode”).

---

## 5. Extensibility Notes

- v0.2 focuses on **single‑node, local Guardian** deployments.
- Future versions may add:
  - multi‑tenant Guardian instances for custodians
  - gRPC streaming for high‑frequency event feeds
  - dedicated admin / operator API surface
- All new endpoints should preserve the **standard envelope** and
  keep verdict / score semantics consistent.
