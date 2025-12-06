# Shield Bridge — QAC API (qac-api.md)

Status: **draft v0.2 – internal skeleton**

This document defines how the Adamantine Wallet talks to the
**Quantum Assurance Controller (QAC)** through the Shield Bridge.

QAC is the **post‑quantum migration brain** of the shield:

- tracks DigiByte's PQC migration roadmap and local support,
- aggregates capability signals from PQC containers and nodes,
- recommends **safe default algorithms** and **fallback paths**,
- raises **early‑warning alerts** for emerging quantum‑class threats.

Adamantine must treat QAC as:

- *advisory* for everyday algorithm choices, and
- *authoritative* for hard **"do not use this algorithm"** bans once
  confirmed by core security processes.

---

## 1. Purpose

The QAC API lets Adamantine:

1. Discover **what PQC algorithms and key types** are considered safe
   *right now* for different purposes (wallet keys, guardians, DD, etc.).
2. Understand the current **migration phase**:
   - classical‑only,
   - hybrid (classical + PQC),
   - PQC‑preferred, etc.
3. Receive **urgent advisories / bans** when:
   - an algorithm is downgraded,
   - a parameter set is deprecated,
   - or emergency rotation is recommended.

---

## 2. Common Concepts

- **Key domain**  
  High‑level purpose of a key or credential:
  - `user_wallet`,
  - `guardian_channel`,
  - `node_auth`,
  - `dd_contract`,
  - etc.

- **Algo family**  
  e.g. `ecdsa`, `ed25519`, `ml-kem`, `ml-dsa`, `hash-based`.

- **Posture**  
  QAC's qualitative view:
  - `experimental`,
  - `recommended`,
  - `legacy_only`,
  - `banned`.

---

## 3. Endpoint: /v1/readiness

High‑level view of global PQC readiness.

```http
GET /v1/readiness
```

### Example Response

```json
{
  "network_phase": "hybrid-preferred",
  "valid_for_seconds": 600,

  "key_domains": [
    {
      "domain": "user_wallet",
      "preferred_algorithms": ["ecdsa-secp256k1", "ml-dsa-65"],
      "fallback_algorithms": ["ecdsa-secp256k1"],
      "posture": "recommended"
    },
    {
      "domain": "guardian_channel",
      "preferred_algorithms": ["ml-kem-768", "ml-dsa-65"],
      "fallback_algorithms": ["rsa-3072"],
      "posture": "recommended"
    },
    {
      "domain": "node_auth",
      "preferred_algorithms": ["ml-kem-1024"],
      "fallback_algorithms": [],
      "posture": "experimental"
    }
  ],

  "notes": [
    "Hybrid signatures for user wallets are recommended.",
    "Guardian channels should prefer PQC KEM + PQC signatures."
  ]
}
```

Adamantine uses this to:

- choose defaults when creating new keys,
- annotate UI with migration status,
- warn when a user selects weaker options.

---

## 4. Endpoint: /v1/algorithms

Detailed catalogue of supported algorithms and QAC posture.

```http
GET /v1/algorithms
```

### Example Response

```json
{
  "algorithms": [
    {
      "id": "ecdsa-secp256k1",
      "family": "ecdsa",
      "category": "classical",
      "posture": "legacy_only",
      "min_key_bits": 256,
      "notes": ["Allowed only in hybrid or for backwards compatibility."]
    },
    {
      "id": "ml-dsa-65",
      "family": "ml-dsa",
      "category": "pqc-signature",
      "posture": "recommended",
      "min_key_bits": 256,
      "notes": ["Preferred PQC signature once available on-chain."]
    },
    {
      "id": "ml-kem-768",
      "family": "ml-kem",
      "category": "pqc-kem",
      "posture": "recommended",
      "min_key_bits": 192,
      "notes": ["Suitable for guardian secure channels."]
    }
  ],
  "timestamp": "2025-12-02T13:50:00Z"
}
```

The wallet can cache this and use it for:

- local validation rules,
- advanced settings pages,
- developer diagnostics.

---

## 5. Endpoint: /v1/advisories

Stream‑like endpoint for **security advisories and emergency notices**.

```http
GET /v1/advisories?since=2025-12-01T00:00:00Z
```

### Example Response

```json
{
  "advisories": [
    {
      "id": "adv-2025-001",
      "severity": "high",
      "affected_algorithms": ["ecdsa-secp256k1"],
      "summary": "Practical quantum speedup evidence for discrete-log.",
      "recommended_actions": [
        "stop-creating-new-ecdsa-keys",
        "prefer-hybrid-or-pqc",
        "plan-rotation-within-180-days"
      ]
    },
    {
      "id": "adv-2025-002",
      "severity": "critical",
      "affected_algorithms": ["toy-pqc-xyz"],
      "summary": "Catastrophic break in experimental PQC scheme.",
      "recommended_actions": [
        "ban-algorithm",
        "rotate-all-keys-within-7-days"
      ]
    }
  ],
  "has_more": false
}
```

Guardian / Risk Engine consume this to:

- flip posture flags from `recommended` → `legacy_only` or `banned`,
- trigger UI banners and rotation flows,
- inform Adaptive Core of changed assumptions.

---

## 6. Endpoint: /v1/local-posture (optional)

Gives a scoped view of **this specific wallet's** PQC posture, after
combining QAC recommendations with local capabilities.

```http
POST /v1/local-posture
Content-Type: application/json
```

```json
{
  "client": "adamantine-wallet",
  "version": "0.1.0",
  "capabilities": {
    "has_pqc_containers": true,
    "hardware_secure_element": false,
    "supports_hybrid_signatures": true
  }
}
```

```json
{
  "effective_phase": "hybrid-preferred",
  "recommended_key_domains": [
    {
      "domain": "user_wallet",
      "mode": "hybrid",
      "algorithms": ["ecdsa-secp256k1", "ml-dsa-65"]
    },
    {
      "domain": "guardian_channel",
      "mode": "pqc-only",
      "algorithms": ["ml-kem-768", "ml-dsa-65"]
    }
  ],
  "ui_flags": {
    "show_rotation_banner": true,
    "show_pqc_beta_warning": false
  }
}
```

The wallet may use this to configure:

- which wizards to show,
- whether to expose PQC options as **beta**,
- when to prompt for key rotation.

---

## 7. Degraded Behaviour

When QAC is unreachable:

- PQC‑related choices fall back to:
  - **local static defaults** in `pqc-containers/` config, and
  - DigiByte core / community advisories shipped with the app.
- The wallet **must not** silently downgrade to obviously weak choices.

When QAC explicitly marks an algorithm as `banned`:

- Adamantine must:
  - stop offering it for new keys,
  - warn loudly when existing keys use it,
  - route rotation / migration tasks to the user as soon as reasonable.

All QAC‑driven changes must be:

- logged in diagnostics,
- visible in the Security / Advanced section of the wallet,
- designed so they can be audited later by power users and developers.
