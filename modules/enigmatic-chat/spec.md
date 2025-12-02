# Enigmatic Chat Module — Specification (spec.md)

Status: **draft v0.1 – internal skeleton**

The **Enigmatic** module is the secure communication layer integrated into
the DigiByte Adamantine Wallet.

It provides:
- end-to-end encrypted messaging between DigiByte identities,
- optional binding between chat and wallet accounts / addresses,
- hooks for value-carrying flows (payment requests, DD / DGB links),
- a foundation JohnnyLaw’s Enigmatic protocol can plug into.

It is designed so that:
- messaging can evolve independently of the wallet core,
- wallet features (Guardian, Shield, DD) **never depend** on chat,
- but when used together, they feel like one coherent experience.

---

## 1. Design Principles

1. **Wallet-first, not chat-first**
   - Enigmatic lives *inside* Adamantine, not the other way around.
2. **Strong separation of concerns**
   - cryptography & transport = Enigmatic core,
   - identity binding & risk = wallet integration.
3. **No silent value movement**
   - messages alone never move funds;
   - all value-related actions pass through Guardian.
4. **Extensible envelope**
   - text, files, commands (e.g. payment requests) all share one model.
5. **Minimal metadata**
   - as little routing / identity metadata as possible,
   - favour local state over server-side state.

---

## 2. Core Components

1. **Enigmatic Core (Johnny’s domain)**
   - key management for messaging
   - E2EE protocol
   - message routing & storage model (e.g. servers / relays / p2p)
   - spam resistance & onion/relay logic

2. **Wallet Integration (Adamantine domain)**
   - mapping between wallet accounts and Enigmatic identities
   - contact model integration
   - Guardian-checked payment requests
   - Shield-aware abuse & phishing detection

This document focuses on the **integration surface** and shared models.

---

## 3. Message Envelope (Shared Model)

Enigmatic messages visible to Adamantine use a **generic envelope**.

```ts
EnigmaticMessageEnvelope {
  id: string                     // local UUID or protocol ID
  direction: "incoming" | "outgoing"

  sender_enigmatic_id: string
  receiver_enigmatic_id: string

  // High-level type for UI & Guardian
  kind: "text" | "file" | "payment-request" | "status" | "system" | "custom"

  // Encrypted payload is opaque to wallet, except for some structured kinds
  encrypted_payload_ref: string  // pointer / handle for Enigmatic core

  // Optional structured content summary for wallet (if available)
  summary?: EnigmaticContentSummary

  // Timestamps
  created_at: timestamp
  received_at?: timestamp
  read_at?: timestamp

  // Flags
  is_starred?: boolean
  is_archived?: boolean
  is_spam_suspected?: boolean
}
```

`EnigmaticContentSummary` is a minimal, optional JSON that the wallet
can understand for smarter UX and Guardian hooks.

```ts
EnigmaticContentSummary {
  preview_text?: string         // e.g. first N chars for notifications
  has_attachments?: boolean
  payment_request?: PaymentRequestSummary
}
```

---

## 4. Payment Request Summary

For messages that represent a **payment request**, Enigmatic (Johnny’s
side) can optionally provide a small structured summary for the wallet.

```ts
PaymentRequestSummary {
  asset: "DGB" | "DD"
  amount: string                 // string to avoid float issues
  currency_hint?: string         // optional, e.g. "DGB"

  // Where to send
  to_address?: string            // direct DGB address
  to_contact_id?: string         // if contact link is known locally

  // Meta
  memo?: string
  expires_at?: timestamp

  // Integrity / verification hints
  request_id?: string
  signature_valid?: boolean
}
```

The **actual cryptographic authentication** of the request is performed
inside Enigmatic core; the wallet only sees validation results and IDs.

Any conversion of a payment request into a **real transaction** MUST
go through Guardian (see `message-flow.md`).

---

## 5. Identity Integration

Enigmatic identities are bound to wallet accounts using:

- `EnigmaticIdentityRef` in `wallet-state.md`
- `EnigmaticContactBinding` in `contact-model.md`

High-level rules:

- One profile can have **multiple** Enigmatic identities (e.g. work / personal).
- An identity may be **anchored** to a primary DGB address for that account,
  but chat keys remain logically separate from spend keys.
- Wallet never exposes private chat keys outside Enigmatic core; it only
  stores **references** or encrypted blobs.

Details are in `identity-and-addresses.md`.

---

## 6. Guardian Integration

Guardian is involved when messages:

- request a payment,
- attempt to modify wallet settings (in future),
- carry commands that can affect funds or security posture.

For such cases:

1. Enigmatic module parses and validates the message.
2. If it contains a **PaymentRequestSummary**, it constructs an
   `ActionRequest` with origin = `"enigmatic"`.
3. Guardian evaluates risk as for any other action.
4. UI presents:
   - payment details,
   - Guardian warnings / approvals,
   - clear “Accept” / “Reject” options.

Messages alone **never** bypass Guardian, even if they look legitimate.

---

## 7. Shield & Abuse Detection

Enigmatic can feed metadata to Shield / Adaptive Core such as:

- frequency of unsolicited payment requests,
- presence of patterns similar to known phishing campaigns,
- spam-like behaviour from certain identities.

Wallet integration hooks:

- flag conversations as `is_spam_suspected`,
- surface “Suspicious activity” banners,
- influence Risk Engine scores when payment requests come from flagged
  contacts or patterns.

Details are discussed in `security-and-abuse-controls.md`.

---

## 8. Storage & Sync

Message storage approach is **implementation-dependent** and may include:

- local-only with optional backup,
- server / relay storage managed by Enigmatic,
- hybrid models.

Adamantine’s concern:

- cache enough metadata locally to provide UX,
- integrate with contact + wallet state,
- not break if Enigmatic store is offline (graceful degradation).

---

## 9. Future Extensions

Potential future features:

- group chats bound to multi-sig wallets,
- read receipts & reactions,
- secure file transfer with Shield-aware scanning,
- bots / agents (e.g. shield assistant) with strict boundaries,
- message-level PQC upgrades coordinated with the shield roadmap.
