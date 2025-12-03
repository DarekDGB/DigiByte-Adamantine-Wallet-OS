# DigiAssets Transfer Flow (transfer-flow.md)

Status: **draft v0.1 – internal skeleton**

This document describes how DigiAssets **transfers** are handled inside
the Adamantine Wallet, including:

- UX flows for sending assets,
- transaction construction expectations,
- Guardian + Risk Engine integration,
- Shield Bridge signalling,
- and failure / edge cases.

It assumes the existence of a DigiAssets-aware indexer or node view
exposing which assets belong to which addresses.

---

## 1. High-Level UX Flow

### 1.1 Entry Points

User can initiate a DigiAssets transfer from:

1. **Asset List View**
   - `Assets → DigiAssets → [Select Asset] → Send`

2. **Contact View** (if contact has addresses)
   - `Contacts → [Contact] → Send Asset`

Both lead to a **Send DigiAsset** form.

---

## 2. Send Form Basics

Core fields:

- **From account** (wallet account / address that holds the asset).
- **Asset** (pre-selected if user came from asset detail view).
- **Recipient**:
  - DigiByte address (pasted / scanned),
  - or contact selection.
- **Amount**:
  - For fungible tokens: numeric amount,
  - For NFTs / certificates: “Select token / instance”.

Optional:

- **Memo / reference** (not guaranteed to be on-chain, depends on protocol).
- **Fee level** (standard / priority).

Validation:

- From account must actually hold the chosen asset.
- Recipient address must be a valid DigiByte address.
- Amount > 0 and ≤ available asset balance.

---

## 3. Asset-Type Specific Behaviour

### 3.1 Fungible DigiAssets (Tokens)

- Model is similar to sending DGB:
  - subtract `amount` from sender’s asset balance,
  - credit `amount` to recipient’s asset balance.
- Remainder (if any) may be returned as change to sender, depending
  on protocol specifics.

UI clarifications:

- Show **current balance** and **post-transfer balance**.
- Indicate if transfer will leave dust balances.

### 3.2 NFTs / Collectibles

- User typically selects:
  - a specific token ID, or
  - a specific edition number in a collection.

Behaviour:

- Entire token is moved to recipient (no partial amounts).
- After transfer:
  - sender no longer owns that token ID,
  - recipient becomes the owner.

UI clarifications:

- Show thumbnail / metadata preview.
- Prominent “You will no longer own this item after transfer” message.

### 3.3 Certificates / Documents

- Transfer semantics can vary:
  - **Ownership transfer**: recipient gains full certificate.
  - **Copy/share**: not a true transfer, but a parallel issuance.

Adamantine v1 should start with **simple ownership transfer** only:

- One owner at a time.
- Transfer = move certificate to new holder.

Anything more complex can be handled in a later design iteration.

---

## 4. Pre-Transfer Review Screen

Before building and signing a transaction, show a **review panel**:

- Asset name + symbol.
- Asset type (Token / NFT / Certificate).
- From account label + address.
- Recipient (address and/or contact name).
- Amount (or NFT ID).
- Estimated network fee.
- Guardian risk level preview (if pre-evaluated).

User must explicitly tap **“Review & Secure Send”** before the engine
starts Guardian + Shield evaluation.

---

## 5. Guardian + Risk Engine Integration

### 5.1 Constructing the Action Request

The send form is transformed into:

```yaml
AssetTransferActionRequest:
  type: "digiasset_transfer"
  asset_id: string
  asset_kind: "fungible" | "nft" | "certificate"
  from_account_id: string
  to_address: string
  to_contact_id: string | null
  amount: string        # "1" for NFTs (full unit)
  metadata_ref: string | null
  approximate_value_dgb: float | null
```

This request is then fed to the **Risk Engine**, which considers:

- Value (if approximate DGB/USD value is known).
- Contact trust level.
- Shield status (Sentinel / DQSN / ADN / QAC).
- History of asset movements (e.g. spam or suspected scams).
- Device posture (normal / hardened / unknown).

### 5.2 Guardian Decisions

Guardian produces a verdict:

- `ALLOW`
- `WARN`
- `REQUIRE_CONFIRMATION` (e.g. biometric)
- `BLOCK`

UI reactions:

- **ALLOW**: proceed directly to transaction construction.
- **WARN**: display warnings (unknown recipient, high value, low shield confidence, etc.).
- **REQUIRE_CONFIRMATION**: require local biometric / passcode.
- **BLOCK**: clearly state the reason and do not construct a TX.

---

## 6. Transaction Construction (Conceptual)

The DigiAssets transfer transaction must respect:

- underlying DigiAssets protocol rules:
  - correct asset-id handling,
  - output ordering / tagging,
  - required OP_RETURN metadata if applicable.
- DigiByte UTXO rules:
  - dust limits,
  - fee sufficiency.

Steps:

1. Select DGB UTXOs for fees + asset-carrying UTXOs for the asset.
2. Create outputs:
   - one or more for the asset recipient,
   - one or more change outputs back to sender (asset + DGB change).
3. Add metadata/asset markers as required by DigiAssets encoding.
4. Ensure:
   - no forbidden patterns in fees / cardinality that conflict with
     shield policies (QWG can add checks here).
   - transaction remains policy-compliant for DigiByte nodes.

Adamantine doesn’t hardcode all rules in this document; rather, it
relies on the DigiAssets protocol spec and implementation library used.

---

## 7. Broadcast & Confirmation

### 7.1 Final Confirmation

A final confirmation screen shows:

- asset and amount,
- sender and recipient,
- fees,
- Guardian verdict (e.g. “Low Risk”, “Medium – please double-check”).

User approves:

- sign transaction,
- broadcast to DigiByte node.

### 7.2 Pending State

After broadcast:

- Transfer appears as “Pending” in:
  - asset detail view,
  - transaction history for the account.

### 7.3 Confirmed State

Once confirmed:

- Balances are updated:
  - sender balance reduced,
  - recipient balance (if the same wallet or a watched address) increased.
- History shows the transfer as completed.

---

## 8. History & Provenance View

For each asset:

- Show list of **key transfers** involving this wallet:
  - date,
  - from / to label (if known),
  - txid (linkable to explorer).
- For NFTs & certificates, show “Current owner (me / someone else)”
  when resolvable.

This can rely on a combination of:

- local wallet knowledge,
- DigiAssets indexers / APIs.

---

## 9. Error & Edge Case Handling

- **Insufficient asset balance**:
  - Block before any call to Risk Engine; show friendly error.
- **Insufficient DGB for fees**:
  - Offer to switch to a top-up / DGB receive flow.
- **Invalid recipient address**:
  - Prevent send until corrected.
- **Shield in lockdown mode**:
  - All transfers blocked with clear “Security Lockdown” message.
- **Chain reorg / double-spend**:
  - Transfer status may move from “confirmed” back to “pending/conflict”
    until final chain is stable (coordinated with Shield / ADN policy).

---

## 10. Logging & Audit

Minimal internal logs for:

- asset id,
- transfer amount,
- sender account summary (non-sensitive ID),
- risk level at time of transfer.

No private keys, seeds, or device identifiers are logged.

---

Author: **DarekDGB**  
License: MIT
