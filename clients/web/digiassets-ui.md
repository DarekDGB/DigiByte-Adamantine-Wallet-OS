# Adamantine Web Client — DigiAssets UI

This file defines the **DigiAssets-focused UI** for the Web client.  
It works together with the generic `ui-screens.md` file for an integrated experience.

## 1. DigiAssets Portfolio

**Route:** `/digiassets/portfolio`

- Table or card grid of all assets:
  - Icon / ticker / name
  - Balance (asset units)
  - Approximate DGB / fiat value (if feeds exist)
  - Badges: NFT / fungible / verified / suspicious (from shield)
- Filters:
  - Asset type (Fungible / NFT)
  - Network (mainnet / testnet)
  - Watchlist / favorites
- Search:
  - By name, ticker, or asset ID

## 2. Asset Detail Page

**Route:** `/digiassets/asset/:id`

Sections:

- Header:
  - Icon, name, ticker
  - Balance
  - Tag: `Fungible` / `NFT` / `Collection`

- Properties:
  - Asset ID / reference
  - Type and supply model
  - Total + circulating supply (if known)
  - Decimals
  - Issuer identity + trust / verification badge

- Metadata:
  - Human-readable fields (name, description, category)
  - Raw JSON viewer (expandable)
  - External links (website, docs, marketplace listing)

- Actions:
  - Send
  - Receive
  - View on DigiByte explorer

- Activity:
  - Per-asset transaction list with filters (incoming / outgoing / mint / burn / issuer ops)

## 3. Send Asset Wizard

**Route:** `/digiassets/send/:id` or `/digiassets/send`

Steps:

1. **Asset selection**
   - If launched context-free, user picks an asset.
   - If launched from asset detail, pre-filled.

2. **Recipient**
   - Address field with paste + QR-import (when supported)
   - Optional contact selector
   - Inline validation and network checks
   - Shield banner if destination has negative risk profile

3. **Amount**
   - Numeric input with:
     - Max button
     - Display of remaining balance
   - Optional DGB / fiat equivalent

4. **Guardian & Shield**
   - Display guardian policy hits:
     - exceeds daily limit?
     - new recipient?
   - Shield preflight summary:
     - unusual pattern / fees / asset flags

5. **Review & Confirm**
   - Summary card showing:
     - from account
     - recipient
     - amount
     - asset ID
     - estimated fees
   - Confirm button triggers signing & broadcast

6. **Result**
   - Success panel:
     - TX hash
     - Links: view in explorer, view in asset history
   - Error panel:
     - Clear message
     - Suggested fix if available

## 4. Receive Asset Screen

**Route:** `/digiassets/receive/:id`

- QR code for receiving DigiAssets at a compatible address
- Plain address with copy button
- Text hint:
  - “Only send DigiAssets for **this asset** on DigiByte to this address.”
- Optional:
  - toggle for “fresh address” vs reusing existing one
- Recent incoming transfers list

## 5. Issue / Mint Asset

**Route:** `/digiassets/create`

Steps:

1. **Intro / Warning**
   - Explain on-chain permanence
   - Explain that the wallet does not guarantee asset legality / compliance

2. **Definition**
   - Name, ticker, description
   - Type: fungible / NFT / collection
   - Initial supply
   - Decimals
   - Flags: re-issuable, burnable, freezeable

3. **Metadata**
   - Icon or image URL / IPFS hash
   - Additional metadata fields (key/value pairs)
   - Optional JSON preview

4. **Fees & Shield Check**
   - DGB fee estimate
   - Asset footprint note (approx. chain usage)
   - Shield simulation: suspicious settings, abnormal patterns

5. **Review**
   - Human-readable summary
   - Raw envelope preview (for experts)

6. **Confirm**
   - Checkbox “I understand this asset will be public and mostly permanent”
   - Final confirm button

7. **Success**
   - Asset ID
   - Link: open asset detail
   - Shortcut: send first transfer

## 6. Collections & NFTs

- Grid view for NFTs / collection items
- Filters: by collection, rarity (if metadata supports it)
- Item details:
  - Image/media viewer (where safe)
  - Traits / attributes list
  - Proof of ownership (on-chain reference)

## 7. Shield Integration

At the Web UI level, shield surfaces as:

- Risk badges on:
  - assets
  - issuers
  - recipients

- Preflight warnings:
  - “This issuer has been flagged by shield nodes.”
  - “This pattern resembles spam / dust attack behaviour.”

- Post-transaction signals:
  - “Asset transfer under observation – waiting for additional confirmations.”

All shield details & scoring models are defined in:

- `docs/risk-model.md`
- `docs/shield-integration.md`
- `core/risk-engine/*.md`
