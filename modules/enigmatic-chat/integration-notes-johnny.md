# Enigmatic Integration Notes for Johnny (integration-notes-johnny.md)

Status: **draft v0.1 – internal skeleton**

This document is a **bridge note** for JohnnyLaw and any contributors
working on Enigmatic, explaining how Adamantine expects to integrate.

It focuses on **interfaces & responsibilities**, not implementation
details of Enigmatic’s internals.

---

## 1. Separation of Concerns

**Enigmatic Core (Johnny & co):**

- messaging protocol design,
- E2EE crypto & identity keys,
- relays / servers / routing,
- message persistence logic,
- spam resistance at protocol level.

**Adamantine (wallet side):**

- contact & wallet binding,
- Guardian & Risk Engine,
- UI flows for payment requests,
- Shield & Adaptive Core integration,
- local abuse stats & UX protections.

The **contract** between the two:

- shared data models (envelopes, summaries, identity refs),
- clear hooks where messages become wallet actions.

---

## 2. Expected Interfaces (Conceptual)

Optional, high-level TypeScript-style interfaces from Adamantine’s POV:

```ts
interface EnigmaticCore {
  // Identity lifecycle
  createIdentity(profileId: string): Promise<EnigmaticIdentityRef>
  rotateIdentity(identityId: string): Promise<void>
  revokeIdentity(identityId: string): Promise<void>

  // Messaging
  sendMessage(opts: {
    from_identity_id: string
    to_enigmatic_id: string
    kind: "text" | "payment-request" | "custom"
    payload: any                     // Enigmatic-defined shape
  }): Promise<{ message_id: string }>

  // Subscription / callbacks for incoming messages
  onMessage(handler: (envelope: EnigmaticMessageEnvelope) => void): void
}
```

Adamantine does **not** dictate protocol internals – these interfaces
are just to show what kind of integration surface it expects.

---

## 3. Payment Requests

For payment requests, the wallet expects:

- A **structured summary** alongside the encrypted payload, e.g.:

  ```ts
  PaymentRequestSummary {
    asset: "DGB" | "DD"
    amount: string
    to_address?: string
    memo?: string
    expires_at?: timestamp
    request_id?: string
    signature_valid?: boolean
  }
  ```

- Enigmatic core handles:
  - signing the request under the sender’s identity,
  - verifying incoming requests,
  - exposing `signature_valid` to the wallet.

- Wallet handles:
  - mapping to contacts / addresses,
  - Guardian evaluation before any TX is created,
  - UI around accept / reject.

---

## 4. Identity Verification

Adamantine will expose **verification ceremonies** in the UI, but
Enigmatic core may:

- generate QR payloads representing an identity,
- provide short verification codes,
- help manage trust markers (verified vs unverified).

Wallet will store results in `EnigmaticContactBinding` and feed them
into Risk Engine for payment requests.

---

## 5. Abuse & Spam Signals

From Enigmatic → Adamantine:

- optional flags on identities / connections (e.g. suspected spammer),
- rate-limited event notifications for flood / abuse patterns.

From Adamantine → Enigmatic:

- user actions like “block identity”, “mark as spam”,
- optional, anonymised stats if user opts-in to shield telemetry.

These loops allow both the protocol and wallet to **learn** and improve
without sharing raw message content.

---

## 6. Minimal Viable Integration

A realistic first milestone:

1. Single identity per profile.
2. Basic one-to-one encrypted messaging.
3. Simple payment request messages:
   - DGB only,
   - manually typed addresses,
   - single “Accept → send” path via Guardian.

Adamantine can start with this and gradually layer in:

- DD support,
- richer abuse handling,
- multiple identities, etc.

---

## 7. Long-Term Vision

- Enigmatic + Adamantine form a **Layer-0 communication channel** for
  DigiByte users and node operators.
- Quantum Shield + Adaptive Core can learn from anonymised, aggregated
  patterns across both TX flows and messaging flows.
- Over time, the ecosystem gets:
  - safer payments,
  - safer coordination,
  - and a UX that feels like “chat + wallet + shield” in one.

This document will evolve as Enigmatic’s concrete API and protocol
details become available.
