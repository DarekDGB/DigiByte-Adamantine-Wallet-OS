# Enigmatic — Message & Payment Request Flow (message-flow.md)

Status: **draft v0.1 – internal skeleton**

This document describes how **messages move through Adamantine** and
how **payment requests** are safely transformed into real wallet actions.

---

## 1. Normal Chat Message Flow (No Value)

### Outgoing

```text
1. User types a message in a conversation.
2. UI creates a message draft (text only, no value).
3. Enigmatic core:
   - encrypts payload,
   - wraps it in its own protocol envelope,
   - handles routing / delivery.
4. Wallet stores minimal metadata:
   - direction = "outgoing"
   - timestamps
   - local status (sent / delivered / failed).
```

Guardian is **not** involved for pure text messages.

### Incoming

```text
1. Enigmatic core receives an encrypted message.
2. Core decrypts & verifies authenticity.
3. It passes a summary (kind, preview, optional PaymentRequestSummary)
   to wallet integration.
4. Wallet stores envelope metadata & updates UI.
```

---

## 2. Payment Request Message Flow

When a message contains a **payment request** (as defined in
`spec.md` under `PaymentRequestSummary`):

### 2.1 Incoming Payment Request

```text
1. Enigmatic core validates the message signature & integrity.
2. It extracts a PaymentRequestSummary (if available).
3. Wallet integration:
   - links summary to the relevant contact (if known),
   - creates a local "pending action" object (not yet executed).
4. Conversation UI shows a payment request bubble with:
   - asset, amount,
   - to whom / from whom,
   - buttons: [Accept] [Reject] [More info].
```

No funds move yet.

### 2.2 User Accepts Payment Request

When user taps **Accept**:

```text
1. Wallet maps PaymentRequestSummary → ActionRequest:
     - kind = "send-dgb" or "mint-dd" etc.
     - uses contact & address mapping from identity-and-addresses.md
2. This ActionRequest is passed into Guardian (via Risk Engine).
3. Guardian returns a GuardianVerdict.
4. UI:
     - shows any warnings,
     - may require biometric / passphrase,
     - if verdict is "allow", proceeds to TX Builder.
5. TX Builder constructs & broadcasts the transaction.
6. Wallet marks the payment request as "completed" or "failed".
```

If Guardian says `block-and-alert`, UI must clearly show that the
request was **blocked by security policy**, not just ignored.

---

## 3. Outgoing Payment Request Flow

When **user sends** a payment request to another Enigmatic identity:

```text
1. User picks a contact & amount in the UI.
2. Wallet builds a PaymentRequestSummary.
3. Enigmatic core:
     - embeds summary into the encrypted message,
     - signs as required by the protocol,
     - sends to the peer.
4. Wallet logs an "outgoing request" entry for that contact.
```

This does not require Guardian because no funds leave the wallet yet.
Guardian is only involved when the **receiver** chooses to act on it.

---

## 4. Rejection & Expiry

- User can **reject** an incoming payment request:
  - wallet marks it as rejected,
  - Enigmatic MAY (optionally) send a rejection message.
- Payment requests can **expire**:
  - `expires_at` in summary,
  - wallet hides or marks them as expired,
  - Guardian may treat expired requests as invalid without evaluation.

---

## 5. Abuse & Spam Flows (High Level)

If many unwanted payment requests or spammy messages arrive from an
identity or contact:

```text
1. Wallet increments abuse counters (per contact / identity).
2. Once thresholds are met:
     - mark contact or conversation as "suspected spam",
     - optionally suggest blocking or muting,
     - adjust Risk Engine inputs for future requests from that identity.
3. Adaptive Core can receive anonymised stats (optional) and learn patterns.
```

Details are elaborated in `security-and-abuse-controls.md`.

---

## 6. Diagnostics & Logs

For debugging and advanced users, a diagnostics view may show:

- recent payment requests (incoming/outgoing),
- how they mapped into ActionRequests,
- associated GuardianVerdicts,
- shield status at the time.

Sensitive data must be minimised or redacted according to the privacy
model, especially if logs are persisted or exported.
