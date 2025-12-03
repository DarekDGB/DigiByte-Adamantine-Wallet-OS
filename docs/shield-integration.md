# DigiByte Quantum Shield Integration — Adamantine Wallet

Status: draft v0.1

This document describes **how the DigiByte Quantum Immune Shield stack
integrates with the Adamantine Wallet**, across all layers and
platforms. It is written for DigiByte core contributors, wallet
engineers, and security auditors who want a clear, implementation‑level
map of the interfaces between:

- the Adamantine Wallet core  
- DigiByte node infrastructure  
- the five shield layers (Sentinel AI v2, DQSN v2, ADN v2,
  Quantum Adaptive Core, Shield Bridge APIs)  
- and external monitoring / orchestration services.

The goal is that a developer can open **this single file** and
understand *exactly* where to plug in shield components, what data
flows between them, and how wallet UX is affected.

---

## 1. Integration Goals

Adamantine’s shield integration is guided by five goals:

1. **Non‑invasive** — no changes to DigiByte consensus or block
   validation rules. Everything runs as an **adjacent security plane**
   around standard DigiByte nodes and wallets.
2. **Composable** — node operators and wallet builders can enable
   shield layers independently (Sentinel only, or Sentinel + ADN, etc.)
   but get the **strongest guarantees** when the full stack is present.
3. **User‑centric** — all shield decisions surface as **clear,
   human‑readable signals** in the wallet: risk scores, warnings,
   cool‑downs, and explicit user approvals.
4. **Chain‑agnostic design, DGB‑first implementation** — the shield is
   designed so other UTXO chains *could* adopt it, but Adamantine
   focuses entirely on **best‑in‑class protection for DigiByte users**.
5. **Evolvable** — as quantum threats, attack patterns, or protocol
   changes appear, the shield can be upgraded **without forcing a hard
   fork** or breaking existing wallets.

---

## 2. High‑Level Data Flow

At a high level, the integration follows this loop:

1. **Adamantine Wallet** constructs a transaction proposal on behalf of
   the user (send, mint DigiDollar, mint DigiAsset, etc.).
2. The wallet sends a **pre‑broadcast request** to the **Shield Bridge
   API**, describing the transaction intent and relevant context.
3. The Shield Bridge forwards this to:
   - **Sentinel AI v2**, which correlates with chain‑wide telemetry and
     anomaly signals.
   - **DQSN v2**, which validates the transaction plan against
     distributed confirmation rules and peer views.
   - **ADN v2**, which simulates node‑level behaviour and lockdown
     conditions.
   - **Quantum Adaptive Core**, which evaluates long‑term patterns,
     immune memory, and quantum‑suspicious indicators.
4. Each layer returns a **structured verdict** and a **risk score** to
   the Shield Bridge.
5. The Shield Bridge aggregates these into a **single unified decision**
   and sends it back to the wallet.
6. The wallet maps this decision to UX:
   - *Allow silently* (green)  
   - *Allow with warning* (amber)  
   - *Require user confirmation / 2FA* (red‑amber)  
   - *Block and cool‑down* (red)
7. If allowed, the wallet broadcasts the transaction via its connected
   DigiByte node(s). Shield layers then continue to monitor **post‑facto
   behaviour** for reorgs, anomalies, and adaptive learning.

---

## 3. Components and Interfaces

### 3.1 Shield Bridge API

The Shield Bridge is the **single integration point** for the wallet.

- **Location**: `core/shield-bridge/` (spec + API docs)
- **Responsibility**:
  - Normalize wallet transaction intents into shield‑agnostic payloads.
  - Call each enabled shield layer via its internal API.
  - Aggregate scores, reasons, and recommended actions.
  - Expose a **stable, versioned API** to wallet clients.

Core request structure:

```jsonc
{
  "wallet_id": "adamantine-ios-uuid",
  "intent_type": "dgb_transfer | dd_mint | digiasset_issue | digiasset_transfer",
  "tx_plan": {
    "inputs": [...],
    "outputs": [...],
    "fee_sats": 1234,
    "change_policy": "single | multi"
  },
  "context": {
    "device_fingerprint": "...",
    "geo_hint": "UK",
    "time_seconds": 1733222000,
    "user_risk_profile": "standard | hardened"
  }
}
```

Core response structure:

```jsonc
{
  "decision": "allow | warn | require_2fa | block",
  "score": 0.0,
  "reasons": [
    "sentinel: mempool pattern normal",
    "dqsn: peer consensus stable",
    "adn: node health good"
  ],
  "cooldown_seconds": 0,
  "layer_breakdown": {
    "sentinel": { "score": 0.03, "notes": ["..."] },
    "dqsn":     { "score": 0.05, "notes": ["..."] },
    "adn":      { "score": 0.02, "notes": ["..."] },
    "adaptive": { "score": 0.10, "notes": ["..."] }
  }
}
```

The **wallet never talks directly** to Sentinel, DQSN, ADN, or the
adaptive core — only to the Shield Bridge API. This keeps the wallet
client simple and lets shield internals evolve independently.

---

### 3.2 Sentinel AI v2 Integration

- **Location**: external project `Sentinel-AI-v2` (Layer 1: monitoring)
- **Interface**: Shield Bridge → Sentinel RPC / HTTP API

Sentinel provides:

- chain‑wide drift metrics  
- mempool anomalies  
- reorg risk scores  
- oracle / price feed deviations

Adamantine uses Sentinel in two ways:

1. **Pre‑broadcast checks** – ensure the chain appears healthy before
   sending large or sensitive transfers (DigiDollar, DigiAssets, cold
   storage sweeps).
2. **Background telemetry** – when the app is open, Sentinel signals can
   inform UX banners such as: *“Network unstable. High reorg risk —
   consider waiting before sending large amounts.”*

If Sentinel is **not available**, the Shield Bridge marks its layer as
`unreachable` but still proceeds with other layers.

---

### 3.3 DQSN v2 Integration

- **Location**: `DGB-Quantum-Shield-Network-v2` (Layer 2: distributed
  confirmation)
- **Interface**: Shield Bridge → DQSN gateway / gRPC / HTTP

DQSN v2 runs an overlay of **shield‑aware nodes** that:

- compare multiple node views for the same height / mempool  
- detect suspicious divergence or conflicting histories  
- provide a **peer‑based confidence score** for a proposed transaction.

Adamantine’s integration:

- For standard small DGB transfers, DQSN is **consulted opportunistically**.
- For high‑value transfers, DigiDollar mint / redeem, or DigiAsset
  issuance, DQSN feedback is treated as **mandatory**. If DQSN reports
  inconsistent views, the wallet blocks or warns.

---

### 3.4 ADN v2 Integration

- **Location**: `DigiByte-ADN-v2` (Layer 3: node‑level defense)
- **Interface**: Shield Bridge → ADN API

ADN v2 simulates how a hardened DigiByte node would:

- accept or reject the transaction  
- respond to certain reorg or eclipse scenarios  
- activate local lockdown or quarantine.

Adamantine uses ADN v2 to:

- sanity‑check that proposed transactions respect **policy** (dust,
  standardness, anti‑spam) before hitting the real node.
- detect whether the local node appears **compromised or mis‑configured**
  based on ADN’s health model.

If ADN flags issues, the Shield Bridge can recommend:

- broadcasting via a **different node set**  
- delaying the transaction  
- or escalating to the user with a clear explanation.

---

### 3.5 Quantum Adaptive Core Integration

- **Location**: `DigiByte-Quantum-Adaptive-Core` (Layer 4: immune
  system)
- **Interface**: Shield Bridge → Adaptive Core REST / gRPC

The adaptive core is the **long‑memory brain** of the shield:

- tracks historical attacks and near‑misses  
- maintains per‑wallet and global risk baselines  
- detects quantum‑style exploitation patterns  
- proposes new defense rules back to ADN / DQSN / Sentinel.

For Adamantine, this means:

- users with normal patterns enjoy **frictionless** experience  
- users under targeted attack get **aggressive protection** (forced
  delays, step‑up authentication, IP / device hardening).

The adaptive core returns an **incremental risk score** that the Shield
Bridge combines with other layers.

---

### 3.6 DigiByte Core Node Integration

Adamantine never bypasses DigiByte Core. Instead:

- shield layers **observe and influence** which nodes are trusted and
  when transactions are broadcast.
- the wallet can maintain a **node roster**, tagged with Sentinel / ADN
  health signals (e.g., `healthy`, `degraded`, `quarantined`).

In future, Adamantine may support **multi‑node broadcasting** for
additional safety, coordinated by DQSN v2.

---

## 4. Wallet UX Integration

Shield decisions must feel **natural** inside the wallet.

### 4.1 Risk Banners

- **Green** – “Protected by DigiByte Quantum Shield. Network healthy.”  
- **Amber** – “Caution: network turbulence detected. Small transfers
  recommended.”  
- **Red** – “High risk conditions. Critical operations temporarily
  blocked by shield.”

### 4.2 Transaction Review Screen

Before final send, Adamantine shows a **Shield Summary**:

- overall decision (Allow / Warn / Block)  
- short explanation (“Mempool normal · Nodes agree · Historical pattern
  safe”)  
- advanced view toggle for experts (layer breakdown & scores).

### 4.3 Activity Log

A dedicated **Security Activity** screen records:

- shield warnings & blocks  
- cool‑down timers  
- when adaptive core updated policies for the wallet.

This log is crucial for **auditing** and user trust.

---

## 5. Platform‑Specific Wiring

### 5.1 Mobile (iOS / Android)

- each mobile client talks to the Shield Bridge via a **single HTTPS
  endpoint**.
- network failures degrade gracefully:
  - if shield unreachable → fall back to **local-only checks** and show
    “Shield offline” banner.

### 5.2 Web Client

- uses the same Shield Bridge endpoint, but must be especially careful
  with **CORS**, session management, and phishing protections.
- all shield responses are treated as **advisory + strong hints**;
  web‑level security (content integrity, CSP) remains critical.

### 5.3 Future Desktop / Hardware Wallets

- will reuse the same Shield Bridge contract.  
- in air‑gapped flows, shield decisions can be fetched on an **online
  companion device** and encoded into QR / file for the offline signer.

---

## 6. Configuration and Policies

Adamantine exposes shield‑related settings in an **“Advanced Security”**
panel (for power users and node operators only):

- enable / disable individual shield layers (where supported)  
- choose risk profile:
  - *Standard* – balanced UX vs security.  
  - *Hardened* – more prompts, delays, 2FA.  
- export anonymized shield logs for auditing or support.

Default for all normal users: **full shield ON**, *Standard* profile.

---

## 7. Failure Modes and Graceful Degradation

When parts of the shield are unavailable:

- **Sentinel down** – show “Network telemetry unavailable”; continue
  with local checks, DQSN, ADN, adaptive core.
- **DQSN unreachable** – block only *critical* flows (large transfers,
  DigiDollar, DigiAssets) or require explicit override.
- **ADN offline** – warn that local node health cannot be simulated;
  recommend trusted remote nodes.
- **Adaptive core offline** – disable adaptive risk boosts, revert to
  static scoring.

The guiding rule:
> *If in doubt, protect the user but never silently trap funds.*

---

## 8. Roadmap Hooks

This integration spec is designed to accommodate future features:

- **DigiAsset‑native shield rules** (per‑asset risk profiles).  
- **Multi‑sig & social recovery flows** with shield oversight.  
- **On‑device models** for limited offline protection.  
- **Community‑shared threat feeds** feeding into Sentinel and adaptive
  core.

As these land, this file will be revised with new message types and UX
patterns.

---

## 9. Summary

Adamantine Wallet is not just “another DigiByte wallet.”  
Through deep integration with the **DigiByte Quantum Shield** stack it
behaves like a **living, learning immune system** around user funds.

This document anchors that integration:

- one bridge API,  
- four shield layers,  
- clear data flows,  
- and wallet UX that always keeps the user in control.

Further implementation details for each component live in:

- `core/shield-bridge/*.md`  
- `modules/dd-minting/*.md`  
- `modules/digiassets/*.md`  
- `docs/risk-model.md`  
- `docs/roadmap.md`  
- and the individual shield project repositories.
