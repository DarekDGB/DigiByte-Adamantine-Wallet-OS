# DigiAssets Minting Flow (minting-flow.md)

Status: **draft v0.1 – internal skeleton**

This document describes how the Adamantine Wallet guides a user through
**minting new DigiAssets**, while respecting the DigiAssets protocol and
Adamantine’s Guardian + Shield model.

It focuses on:

- UX steps,
- transaction structure expectations,
- oracle / metadata handling,
- and risk checks.

It does **not** redefine DigiAssets consensus rules.

---

## 1. Minting Modes

Adamantine supports three primary mint types:

1. **Fungible Asset (Token)**
   - Fixed or capped supply.
   - Transferable, divisible per DigiAssets rules.

2. **Non-Fungible Asset (NFT / Collectible)**
   - Unique ID.
   - Typically 1-of-1 or very small supply.
   - Metadata usually includes media (image / audio / document).

3. **Certificate / Document Asset**
   - Represents ownership/attestation of:
     - rights,
     - achievements,
     - licenses,
     - other off-chain facts.
   - Strong emphasis on metadata integrity.

Future modes (time-locked, revocable, etc.) can extend this framework.

---

## 2. High-Level UX Flow

### 2.1 Entry point

User navigates to:

> **Assets → Mint DigiAsset**

UI then asks to choose a mode:

- “Create Fungible Token”
- “Create NFT / Collectible”
- “Create Certificate / Document Asset”

The following steps adapt slightly by mode.

---

## 3. Common Steps Across All Modes

### 3.1 Choose Issuing Account

User selects an account:

- `from_account` (DGB UTXOs used for issuance fees + anchoring)
- Optional label: “Issuer identity” displayed in UI.

### 3.2 Basic Asset Details

Fields:

- **Name** (human readable)
- **Ticker / Symbol** (short code, e.g. `DGBGOLD`)
- **Description** (plain text)
- **Category** (Token, NFT, Certificate, etc.)

Validation:

- Name non-empty.
- Symbol within allowed length and charset.
- Description within reasonable size limit.

### 3.3 Metadata Attachments

Optional but recommended:

- External URL (landing page, project site).
- Media URL (for NFT or image-based assets).
- Content hash (e.g. SHA-256) for integrity.
- Additional metadata fields defined in `metadata-format.md`.

UI should clearly state:

> “Metadata may be stored off-chain. Use hashes when you want
>  verifiable linkage between the asset and external content.”

---

## 4. Mode-Specific Behaviour

### 4.1 Fungible Token

Additional fields:

- **Total Supply** (number of units).
- **Decimals / divisibility** (if applicable to DigiAssets implementation).
- **Initial distribution** (all to issuer address, or split).

Checks:

- No negative or zero supply.
- Optional max caps or warnings for extremely large numbers.

TX notes (conceptual):

- Issuance transaction encodes:
  - asset definition metadata,
  - total supply,
  - allocation outputs.

### 4.2 NFT / Collectible

Additional fields:

- **Edition Size**:
  - `1` for pure 1-of-1 NFT,
  - or small integer for limited editions.
- **Media reference** (image, video, etc. via URL or IPFS-style link).
- **Content hash** strongly recommended.

Checks:

- Edition size > 0.
- Large edition sizes might be flagged by UX as “token-like”.

### 4.3 Certificate / Document Asset

Additional fields:

- **Subject name / entity** (person, organisation, asset owner).
- **Validity period** (from / to), optional.
- **Reference ID** (external system or document number).

Checks:

- Subject non-empty.
- Validity end date > start date (if provided).

---

## 5. Pre-Mint Review Screen

Before any transaction is built, Adamantine shows a **summary page**:

- Mode: Token / NFT / Certificate.
- Asset name + symbol.
- Total supply or edition.
- Issuing account and address.
- Fees estimate (DGB).
- High-level metadata summary.
- Short security checklist (e.g. “Double-check spelling, this is on-chain”).

User must explicitly tap **“Review & Secure Mint”** to proceed.

---

## 6. Guardian + Risk Engine Checks

When user proceeds:

1. Wallet builds a **MintActionRequest** from the form data.
2. Risk Engine evaluates context:
   - issuing account age,
   - past behaviour,
   - shield status,
   - value of implied issuance (if applicable),
   - telemetry / abuse signals (e.g. spam issuance).
3. Shield Bridge consulted:
   - network stability,
   - anomaly overlays.

Possible outcomes:

- **ALLOW** – proceed to transaction build.
- **WARN** – show warnings, require extra confirmation (e.g. biometric).
- **BLOCK** – hard stop with clear reason (e.g. chain instability or lockdown).

---

## 7. Transaction Construction (Conceptual)

The mint operation builds a DigiAssets-compliant transaction with:

- correct UTXO inputs from `from_account`,
- asset-defining outputs,
- possible change outputs,
- OP_RETURN (or equivalent) metadata payload.

Key invariants:

- No dust outputs.
- Fees sufficient and within safe bounds.
- Asset-id and metadata structured per DigiAssets spec.

Exact byte-level structure and examples shall be documented separately
once final DigiAssets node/indexer specs for Adamantine are locked in.

---

## 8. Broadcast & Confirmation

### 8.1 Preview

Before final send, user sees:

- final fee,
- tx summary,
- “mint is permanent” reminder.

### 8.2 Broadcast

Upon acceptance:

1. TX signed and broadcast to DigiByte.
2. Local state moves to “Pending mint…” with txid.

### 8.3 Confirmation

When on-chain:

- Asset appears in wallet’s **DigiAssets** list.
- Issuing account shows relevant history.
- Optionally surfacing:
  - issuance height,
  - initial holders (usually the issuer address).

---

## 9. Failure Modes & Edge Cases

- **Broadcast failure**: show clear retry / error state.
- **Fee too low**: surface node rejection reason and suggest higher fee.
- **Chain reorg**: asset list re-syncs based on final chain state.
- **User cancels at last step**: no partial or ghost assets — mint only
  recorded after confirmed broadcast.

---

## 10. Logging & Audit

Minimal structured logs for:

- minted asset ID,
- mode,
- originating account,
- timestamp,
- risk level at time of mint (LOW/MED/HIGH/CRITICAL).

No sensitive user data stored beyond what is necessary to re-derive
asset history and security posture.

---

Author: **DarekDGB**  
License: MIT
