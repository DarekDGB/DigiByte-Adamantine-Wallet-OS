# Enigmatic — Identity & Address Binding (identity-and-addresses.md)

Status: **draft v0.1 – internal skeleton**

This document defines **how Enigmatic identities relate to DigiByte
accounts and addresses** inside the Adamantine Wallet.

The goals:

- Let users chat as identities that can be **optionally linked** to
  their wallet accounts.
- Allow **payment requests** to refer to known contacts / addresses.
- Preserve separation between **spend keys** and **chat keys**.

---

## 1. Identity Objects

The primary reference is `EnigmaticIdentityRef` in `wallet-state.md`:

```ts
EnigmaticIdentityRef {
  id: string                    // local UUID
  protocol_version: string      // e.g. "enigmatic-1"

  primary_account_id: string
  primary_address: string       // DGB address used as identity anchor

  public_key: string
  encrypted_private_key_ref: string

  display_name?: string
  avatar_url?: string
}
```

Notes:

- `primary_address` is an **anchor**, not the only address used for
  payments. It gives other users a stable way to associate this identity
  with a wallet context.
- `encrypted_private_key_ref` is a handle managed by Enigmatic core;
  the wallet doesn’t store raw private keys in clear.

---

## 2. Identity Lifecycles

Basic lifecycle states (conceptual):

- **created**: identity exists locally, not yet “announced”.
- **published**: identity is usable for incoming messages.
- **rotated**: keys rotated, old ID deprecated.
- **revoked**: identity no longer used.

Wallet responsibilities:

- keep track of active identities per profile,
- indicate which identity is “active” in the UI for messaging,
- allow users to create / rename / rotate identities (delegating
  crypto details to Enigmatic core).

---

## 3. Binding to Contacts

For remote users, `EnigmaticContactBinding` in `contact-model.md` is used:

```ts
EnigmaticContactBinding {
  enigmatic_id: string
  primary_channel_id?: string   // ContactChannel.id of type "enigmatic-identity"

  is_verified: boolean
  verification_note?: string
  last_key_rotation_at?: timestamp
}
```

Verification ceremony examples:

- QR code scan in person,
- short code comparison,
- shared secret phrase.

Wallet should treat **unverified** identities as slightly higher risk
when processing payment requests (Risk Engine input).

---

## 4. Address Associations

A contact can have both:

- one or more DGB addresses (`ContactChannel` kind = "dgb-address"),
- one or more Enigmatic identities (`kind = "enigmatic-identity"`).

Mapping examples:

- A merchant:
  - `enigmatic-identity` for support chat,
  - `dgb-address` for payments.

- A friend:
  - `enigmatic-identity` for chat,
  - optional DGB address for simple sends.

In some flows, payment requests may suggest a DGB address that doesn’t
yet exist in the contact model; wallet can offer to **add it** as a new
channel after verification.

---

## 5. Self-Binding (User’s Own Accounts)

Adamantine may create **self-alias contacts** for the user’s own
Enigmatic identities and DGB addresses, e.g.:

- “Me — Main Wallet”
- “Me — Cold Storage”

Benefits:

- unify UX between “send to myself” and “send to contact”,
- support future multi-device sync,
- allow Guardian to treat self-flows differently.

---

## 6. Security Considerations

1. **Do not auto-trust identities** just because they claim to be
   linked to certain addresses; verification is always local.
2. **Avoid automatic payment address changes** based purely on messages —
   require user confirmation and, ideally, Guardian checks.
3. Support **key rotation** and revocation signals coming from Enigmatic
   core and surface them clearly in the UI.

---

## 7. Future Directions

- multiple identities per account (work / personal / anon),
- group identities mapped to multi-sig wallets,
- “verified merchant” badges using signed attestations.
