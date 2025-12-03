# DigiAssets Module — Specification (spec.md)

Status: **draft v0.1 – internal skeleton**

The **DigiAssets module** brings native DigiByte asset support into the
Adamantine Wallet. It covers:

- viewing DigiAssets held by the wallet,
- minting new DigiAssets,
- transferring existing DigiAssets,
- inspecting history & metadata,
- applying Guardian + Shield rules to all asset actions.

Adamantine does **not** replace the DigiAssets protocol or consensus.
It is a **security-first client** that speaks the standard DigiAssets
rules in a modern, guardian-protected UX.

---

## 1. Goals

1. Give the DigiByte community a **modern DigiAssets experience**
   (web, iOS, Android) after years of waiting.
2. Make DigiAssets **safe by default** using:
   - Guardian Wallet risk engine,
   - Quantum Wallet Guard (QWG),
   - Shield Bridge (Sentinel / DQSN / ADN / QAC / Adaptive).
3. Provide a clean integration layer so DigiByte Core / DigiAssets
   maintainers can:
   - audit behaviour,
   - extend flows,
   - or fork the implementation if desired.

---

## 2. Non-Goals

- No new DigiAssets consensus rules.
- No proprietary token standards.
- No centralised custody or off-chain IOU tokens.
- No ad-tech or invasive analytics around asset usage.

---

## 3. Core Capabilities

1. **Asset Discovery**
   - Enumerate DigiAssets associated with wallet addresses.
   - Query DigiAssets indexer / node plugin as required.
   - Display balances, tickers, icons, and basic metadata.

2. **Asset Minting**
   - Guided flow for:
     - fungible assets (tokens),
     - non-fungible assets (NFTs / collectibles),
     - “document / certificate” style assets.
   - Builds DigiAssets-compliant transactions with correct:
     - issuance metadata,
     - output structure,
     - OP_RETURN payloads.
   - Always routed through Guardian (no blind mint).

3. **Asset Transfer**
   - Safe send flow:
     - select asset,
     - select amount / token ID,
     - select recipient (address or contact),
     - Guardian review,
     - broadcast.
   - Handles change / remainders per DigiAssets rules.

4. **Metadata Inspection**
   - Human-readable view of:
     - name, symbol,
     - description,
     - URLs / hashes,
     - issuer info (if present),
     - media references.
   - Optional verification checks (hash integrity, signature if supported).

5. **History & Provenance**
   - Basic chain of custody:
     - issuance tx,
     - key transfers,
     - burns / revocations (if supported).
   - High-level view; deep indexing left to external explorers.

---

## 4. Integration Points

The DigiAssets module interacts with:

- **Wallet Core**
  - UTXO selection for DigiAssets transactions.
  - Address derivation & change outputs.

- **Guardian / Risk Engine**
  - High-value token transfers.
  - Suspicious or unknown recipients.
  - Contract / ruleset anomalies (where inspectable).

- **Shield Bridge**
  - Extra intel about risky assets / issuers (if available).
  - Chain-level anomalies affecting DigiAssets traffic.

- **Enigmatic Layer-0 (future)**
  - Optional state-plane signalling for authenticity and anti-forgery,
    coordinated with Johnny’s work.

---

## 5. File Layout (Module Local)

This module expects the following docs in `modules/digiassets/`:

- `spec.md` (this file) — high-level definition.
- `minting-flow.md` — UX + TX flow for asset issuance.
- `transfer-flow.md` — UX + TX flow for sending assets.
- `metadata-format.md` — how metadata is parsed and displayed.
- `guardian-rules.md` — risk model & Guardian integration specifics.
- `ui-wireframes.md` — wallet UI surface for DigiAssets.

Each of those files is written as a **specification**, not code.

---

## 6. Future Extensions

- Deeper integration with DigiAssets indexers and explorers.
- Multi-sig controlled issuance and transfer.
- Time-locked or conditionally-revocable certificates.
- Enigmatic-assisted authenticity beacons for high-value assets.

---

Author: **DarekDGB**  
License: **MIT**
