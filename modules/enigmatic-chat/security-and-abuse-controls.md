# Enigmatic — Security & Abuse Controls (security-and-abuse-controls.md)

Status: **draft v0.1 – internal skeleton**

This document outlines how Adamantine + Enigmatic work together to
handle **security, spam, phishing, and abuse** in messaging.

It builds on:

- envelope model (`spec.md`)
- identity binding (`identity-and-addresses.md`)
- payment flows (`message-flow.md`)
- Risk Engine & Guardian logic.

---

## 1. Threat Types

Key threats in a wallet-integrated chat:

1. **Phishing payment requests**
   - fake “support”, “airdrop”, “KYC” messages.
2. **Impersonation**
   - someone pretending to be a known contact / service.
3. **Spam / flooding**
   - large volumes of unwanted messages or requests.
4. **Malicious links / attachments**
   - attempts to deliver malware or trick users outside the wallet.
5. **Social engineering**
   - high-pressure tactics, repeated nagging, emotional manipulation.

---

## 2. Protective Layers

1. **Protocol-level** (Enigmatic core / Johnny’s side)
   - strong identity keys,
   - message authentication,
   - optional relay / server-side abuse filters.

2. **Wallet-level** (Adamantine)
   - Guardian checks for value-moving actions,
   - risk-aware UI for requests and unknown contacts,
   - contact trust signals.

3. **Shield / Adaptive Core**
   - pattern recognition across anonymised events,
   - raising risk overlays for known scam patterns.

---

## 3. Local Abuse Model

Adamantine tracks basic local stats per contact / identity:

```ts
AbuseStats {
  contact_id?: string
  enigmatic_id?: string

  total_messages: number
  total_payment_requests: number

  rejected_requests: number
  marked_as_spam: boolean

  last_message_at?: timestamp
  last_request_at?: timestamp
}
```

These stats feed into Risk Engine and UX:

- repeated, unsolicited payment requests → **suspicion score up**,
- many rejections → suggest blocking,
- `marked_as_spam` → direct risk bump for future requests.

---

## 4. UI Defences

1. **Unknown contacts**
   - show clear “Unknown sender” badge,
   - avoid showing payment buttons too prominently,
   - encourage user to verify identity before large sends.

2. **Unverified identities**
   - highlight “Not verified” under contact name,
   - show info explaining verification ceremonies.

3. **Large or unusual requests**
   - show Guardian’s risk assessment clearly,
   - require explicit confirmation steps.

4. **Suspicious link warnings**
   - basic checks on URLs (e.g. punycode, known phishing domains),
   - optional extra scanning depending on platform capabilities.

---

## 5. Guardian Hooks

When Enigmatic payment requests are turned into ActionRequests:

- Risk Engine receives `AbuseStats` and identity verification state
  via `LocalContextSnapshot.counterparty`.
- Guardian can escalate actions when:
  - trust is low,
  - abuse stats are high,
  - patterns match known phishing (from Adaptive overlays).

Example behaviours:

- require biometric / passphrase for payments to low-trust identities,
- block large requests from identities marked as spam,
- show “This contact has sent many requests recently” warning.

---

## 6. Blocking & Muting

Users must be able to:

- **Mute** a conversation:
  - stop notifications,
  - still allow manual review.

- **Block** an identity / contact:
  - prevent further incoming messages (where protocol allows),
  - auto-mark future payment requests as invalid.

The wallet should also mark such contacts as `trust_level = "blocked"`
in the contact model for consistency.

---

## 7. Privacy & Telemetry

If abuse-related telemetry is sent to Adaptive Core:

- no raw message content,
- no raw addresses,
- minimal, hashed identifiers where needed,
- focus on pattern-level data (counts, frequencies, categories).

Example event (conceptual):

```json
{
  "kind": "enigmatic-abuse-pattern",
  "timestamp": "2025-12-02T14:00:00Z",
  "pattern": "repeated-payment-requests",
  "frequency_bucket": "high"
}
```

Opt-in only, never default-on for typical users.

---

## 8. Future Enhancements

- shared, privacy-preserving blocklists,
- scam pattern signatures shared via shield,
- community-verified identities / services,
- richer education prompts (e.g. mini guides when a first phishing-like
  request is detected).
