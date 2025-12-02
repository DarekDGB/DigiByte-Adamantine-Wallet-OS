# DigiByte Adamantine Wallet — Contact Model

Status: **draft v0.1 – internal skeleton**

This document defines the **contact and identity model** used by the
DigiByte Adamantine Wallet. It is shared by:

- the core wallet (address book)
- the Enigmatic messaging module
- the DD (DigiDollar) module for trusted counterparties
- Guardian / QWG for trust scoring and risk hints

The goal is to:

- keep a **single source of truth** for “who is this person / entity?”
- support both **human contacts** and **service endpoints**
- allow privacy-preserving use where needed.

> NOTE: This is a conceptual model. Concrete storage (SQLite, etc.)
> can adapt it as needed.

---

## 1. Core Contact Object

```ts
Contact {
  id: string                     // local UUID
  profile_id: string             // owner profile (Profile.id)

  kind: "person" | "business" | "service" | "self-alias"

  display_name: string           // "JohnnyLawDGB", "Cold Vault", etc.
  nickname?: string              // local short label

  // Optional visual hints
  avatar_url?: string
  color_hint?: string            // e.g. "#0055ff" for UI

  // Relationship metadata
  is_favorite: boolean
  tags: string[]                 // ["dgb-core", "family", "exchange"]
  created_at: timestamp
  last_interaction_at?: timestamp

  // Trust & risk perception (local, subjective)
  trust_level: "unknown" | "low" | "normal" | "high" | "blocked"
  risk_flags: ContactRiskFlags

  // Communication + payment channels
  channels: ContactChannel[]

  // Optional Enigmatic + DD integration state
  enigmatic_identity?: EnigmaticContactBinding
  dd_counterparty_state?: DigiDollarCounterpartyState

  notes_encrypted?: bytes        // optional encrypted note
}
```

Contacts are **local to a profile** and never automatically broadcast.
Cloud backup / sync, if implemented, must be explicit and opt-in.

---

## 2. Risk Flags

Contact-level risk flags feed into Guardian / QWG scoring, but they are
always **advisory**, never absolute.

```ts
ContactRiskFlags {
  is_exchange?: boolean          // known CEX / DEX
  is_custodial_service?: boolean
  is_known_scam?: boolean
  is_suspicious?: boolean
  is_internal_wallet?: boolean   // another wallet owned by the user
  is_high_value_counterparty?: boolean
}
```

- `is_known_scam` SHOULD trigger **high / critical** risk in Guardian
  when sending funds.
- `is_internal_wallet` MAY relax some checks (e.g. allow faster flows).

---

## 3. Channels

Each contact may have multiple channels:

- DigiByte addresses (for on-chain payments)
- Enigmatic identities (for messaging)
- DD settlement details
- External references (email, website, etc.)

```ts
ContactChannel {
  id: string
  contact_id: string

  kind:
    | "dgb-address"
    | "dgb-extended"          // xpub, descriptor, etc.
    | "enigmatic-identity"
    | "dd-settlement"
    | "email"
    | "website"
    | "notes"
    | "other"

  label?: string               // "Main", "Cold", "Support", etc.

  // Generic payload: interpretation depends on kind.
  value: string

  // For DGB-specific channels:
  address_network?: "DGB-mainnet" | "DGB-testnet"
  is_change_address?: boolean
  is_watch_only?: boolean

  // For Enigmatic channels:
  enigmatic_protocol_version?: string  // e.g. "enigmatic-1"

  // UX + activity
  created_at: timestamp
  last_used_at?: timestamp
  usage_count: number
}
```

Examples:

- A **friend** might have:
  - 1× `dgb-address` channel
  - 1× `enigmatic-identity` channel
- An **exchange** might have:
  - 3× `dgb-address` channels (“Deposit 1”, “Deposit 2”, …)
  - 1× `website` channel
  - 1× `email` channel (“support@…”)

---

## 4. Enigmatic Binding

For contacts that are reachable over **Enigmatic**, we store a binding
that allows the wallet + messaging layer to coordinate identity.

```ts
EnigmaticContactBinding {
  enigmatic_id: string            // remote identity ID
  primary_channel_id?: string     // ContactChannel.id of type "enigmatic-identity"

  // Trust and UX hints
  is_verified: boolean            // local verification done (e.g. key handshake)
  verification_note?: string
  last_key_rotation_at?: timestamp
}
````

- `is_verified` indicates we have authenticated this contact via
  some trust ceremony (QR scan, shared secret, etc.).
- Guardian can treat **unverified** identities as slightly higher risk
  when sending payment requests.

---

## 5. DigiDollar Counterparty State

Some contacts may be DD-specific counterparties:

- OTC trading partners
- merchants accepting DD
- custodial vaults, if they ever exist

```ts
DigiDollarCounterpartyState {
  preferred_dd_channel_id?: string     // ContactChannel.id with kind "dd-settlement"
  last_settlement_at?: timestamp
  total_volume_dd?: number             // aggregated DD volume
  total_volume_satoshis?: number

  // Optional standing instructions
  auto_tag_transactions_as?: string[]  // e.g. ["merchant", "salary"]
  default_memo_template?: string       // e.g. "Monthly settlement – {month}"
}
```

This state helps the wallet show **clean history** and
give Guardian more context when DD flows involve this contact.

---

## 6. Self-Alias Contacts

The wallet may represent **user’s own other accounts / devices** as
contacts for clarity and future sync features.

In this case:

- `kind = "self-alias"`
- `risk_flags.is_internal_wallet = true`
- channels mostly contain DGB addresses belonging to other accounts
  the user controls.

Guardian and Shield MAY treat self-alias flows as lower risk, yet
still monitor them for anomalies (e.g. malware moving funds internally
in preparation for an external drain).

---

## 7. Example JSON Sketch

```json
{
  "id": "contact-123",
  "profile_id": "profile-1",
  "kind": "person",
  "display_name": "JohnnyLawDGB",
  "nickname": "Johnny",
  "is_favorite": true,
  "tags": ["dgb-core", "enigmatic"],
  "created_at": "2025-12-02T13:00:00Z",
  "trust_level": "high",
  "risk_flags": {
    "is_exchange": false,
    "is_internal_wallet": false
  },
  "channels": [
    {
      "id": "ch-1",
      "kind": "dgb-address",
      "label": "Main DGB",
      "value": "D1234...",
      "address_network": "DGB-mainnet",
      "created_at": "2025-12-02T13:00:00Z",
      "usage_count": 3
    },
    {
      "id": "ch-2",
      "kind": "enigmatic-identity",
      "label": "Enigmatic",
      "value": "enigmatic:johnny-law-id",
      "enigmatic_protocol_version": "enigmatic-1",
      "created_at": "2025-12-02T13:00:00Z",
      "usage_count": 10
    }
  ],
  "enigmatic_identity": {
    "enigmatic_id": "enigmatic:johnny-law-id",
    "primary_channel_id": "ch-2",
    "is_verified": true,
    "verification_note": "QR handshake at DGB conf 2026"
  }
}
```

---

## 8. Future Extensions

Later versions of this model may add:

- multi-profile shared contacts (family devices)
- federation / contact discovery (still privacy-preserving)
- extended verification methods (Web-of-Trust, signed attestations)
- richer tagging and search syntax.
```

