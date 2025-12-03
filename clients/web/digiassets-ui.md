# DigiAssets Web UI — Screen & Flow Notes

Status: draft v0.1

This document sketches the **first-generation DigiAssets experience in the Adamantine Wallet (web client)**.
It focuses on *flows* and *screens*, not implementation details. Everything here is intentionally modular so
it can evolve with the core DigiAssets standard and community feedback.

---

## 1. Core UX Principles

1. **DigiByte‑first, assets second**  
   - The DGB balance, UTXOs and fee health are always visible.  
   - Every asset action clearly shows the underlying DGB cost and required UTXOs.

2. **Clarity over cleverness**  
   - Plain language labels (e.g. “Send Asset”, “Burn”, “Freeze”).  
   - Warnings in human language, not protocol jargon.

3. **Auditability**  
   - Every action links to “View raw transaction” + “View in block explorer”.  
   - For advanced users, there is a “Show protocol envelope” panel that reveals DigiAssets fields.

4. **Safety rails**  
   - Domain / address sanity checks on send.  
   - Confirmations for irreversible actions (burn, freeze, revoke).  
   - Clear distinction between *testnet* and *mainnet* contexts.

---

## 2. Main Navigation

In the web client sidebar / top nav we add a dedicated section:

- **Wallet**
  - Overview
  - Transactions
- **DigiAssets**
  - Portfolio
  - Create / Issue
  - Manage
  - History
- **DigiDollar (DD)**
- **Security**
  - Shield status
  - Devices & sessions

On narrow/mobile web views, these appear as tabs in a collapsible menu.

---

## 3. Screens

### 3.1 Portfolio

**Route:** `/digiassets/portfolio`

**Purpose:** High‑level view of all DigiAssets controlled by the wallet.

**Key elements:**

- Asset list table / cards:  
  - Icon / color ring (per asset)  
  - Asset name & ticker (e.g. `DGBVLT`, `DUSDT`)  
  - Balance (human format) and raw units  
  - Network (mainnet / testnet)  
  - Status badges: `frozen`, `issuer`, `watch-only`, `suspicious` (from shield)  
- Global search & filter (by name, ticker, issuer, tag, network)
- Quick actions on hover / tap: `Send`, `Receive`, `Details`

**Optional advanced widgets:**

- “Concentration risk” badge if a single issuer dominates portfolio.
- Link to “shield risk” if any asset issuer or script pattern is flagged.

---

### 3.2 Asset Details

**Route:** `/digiassets/asset/:id`

**Purpose:** Deep view for a single asset instance.

**Sections:**

1. **Header**
   - Asset name, ticker, icon.
   - Balance, total supply (if visible) and decimals.
   - Issuer label (clickable) + verification / trust badges.

2. **Properties**
   - Asset ID / contract reference.
   - Issuance type: fixed, re‑issuable, NFT, collection, etc.
   - Rules flags: mintable, burnable, freezeable, transferable.
   - Metadata summary (link to full JSON / IPFS / URL).

3. **Actions**
   - Buttons: `Send`, `Receive`, `Burn` (if allowed), `Freeze` (if issuer), `Reissue` (if allowed).

4. **Activity**
   - Recent transactions table limited to this asset.  
   - Columns: time, type (issue / send / receive / burn / freeze / thaw), amount, counterparty, txid.

5. **Diagnostics (advanced tab)**
   - Raw DigiAssets envelope.
   - Underlying DGB transaction ID(s).
   - Shield risk notes & last scan time.

---

### 3.3 Create / Issue Asset

**Route:** `/digiassets/create`

**Purpose:** Wizard for creating a new DigiAsset.

**Step 1 – Basics**
- Asset name (required)
- Ticker / symbol (optional, with suggested length)
- Description
- Category / tags (e.g. “community token”, “stablecoin”, “NFT”, “ticket”)

**Step 2 – Supply & Rules**
- Supply model: fixed / re‑issuable / NFT / collection
- Initial supply (with helper for decimals)
- Decimals
- Cap for re‑issuable assets (optional)
- Flags:  
  - Allow future minting  
  - Allow burning  
  - Allow freezing / blacklisting  
- Toggle for “Testnet only / experimental asset”

**Step 3 – Metadata**
- Upload / link icon (URL or IPFS hash)
- Optional external links: website, terms, docs.
- Arbitrary key/value metadata fields.

**Step 4 – Funding & Fees**
- Display required DGB fee + dust requirements.
- Option to select the funding UTXO set (simple / advanced view).
- Shield pre‑check: warn if wallet fee health is poor or if any rule looks dangerous.

**Step 5 – Review & Confirm**
- Human‑readable summary of all choices.
- Show reconstructed raw envelope preview.
- Final confirmation modal: “Create Asset”.

After broadcast, redirect to the **Asset Details** screen with a success banner and tx link.

---

### 3.4 Send Asset

**Route:** `/digiassets/send/:id` or `/digiassets/send` (with asset selector)

**Fields:**

- From account / label.  
- Asset selector (if not in context).  
- Recipient address or DigiByte name (future).  
- Amount (with “max” helper).  
- Network (mainnet / testnet, locked by context).  
- Optional memo / reference.  

**Safety checks:**

- Validate address format and network.  
- Check available balance (asset + DGB fees).  
- If sending to a new / unseen address, show “new recipient” warning.  
- If the risk engine flags the recipient, issue a clear shield warning and require extra confirmation.

**Confirmation panel:**

- Show amount, recipient, estimated fee, and total DGB to be spent.  
- Show underlying DigiByte tx size estimate.  
- “View raw transaction details” expandable section.

---

### 3.5 Receive Asset

**Route:** `/digiassets/receive/:id`

**Purpose:** Help the user share an appropriate receiving address / QR code for a specific asset.

**Elements:**

- Selected asset info (name, ticker, icon).  
- Dedicated receiving address (or derivation path label).  
- QR code including optional memo.  
- Copy buttons: address, payment URI.  
- “Advanced” panel explaining whether the same address can hold multiple assets, privacy trade‑offs, etc.

---

### 3.6 Manage Issued Assets (Issuer Console)

**Route:** `/digiassets/manage`

**Visible only** if the wallet is an issuer for one or more assets.

**Sections:**

- Table of assets where this wallet has issuer rights.  
- For each asset: quick links to `Reissue`, `Freeze / Thaw`, `Burn`, `Update metadata` (where protocol allows).

**Management flows:**

- **Reissue / Mint more** – wizard similar to send, but from issuer context.  
- **Freeze address** – choose asset, target address, reason (optional), confirm.  
- **Burn from treasury** – burn amounts from issuer’s own holdings with clear warnings.  

Each action clearly logs to the **History** screen with an “issuer action” label.

---

### 3.7 History

**Route:** `/digiassets/history`

**Purpose:** Unified list of all DigiAssets‑related activity for this wallet.

**Filters:**

- Asset, time range, direction (in / out / issuer ops), network, status (confirmed / pending / failed).

**Columns:**

- Time, asset, direction, amount, counterparty, tx status, action type.

Each row links to both **Asset Details** and **DigiByte tx explorer**.

---

## 4. Shield & Risk Integration Hooks

The web client integrates Adamantine’s shield stack in subtle, user‑friendly ways:

- **Inline risk badges** on assets and recipients, powered by the risk engine.  
- **Pre‑flight checks** before broadcasting:  
  - Look for suspicious script patterns.  
  - Check issuer reputation / previous flags.  
- **Explainable warnings**: “This issuer has been flagged by X% of shield nodes for suspicious minting.”

A separate technical spec (`modules/digiassets/spec.md`) defines the exact signal vocabulary and API calls.

---

## 5. Progressive Enhancement Plan

v0.1 (MVP web client)
- Portfolio, Asset Details, Send, Receive, basic Create.  
- Minimal issuer console.  
- Basic shield warnings.

v0.2+
- Rich dashboards (charts, issuer analytics).  
- Collection / NFT gallery views.  
- Advanced multi‑sig and hardware wallet flows for high‑value assets.  
- Tight Enigmatic hooks for encrypted signaling about asset governance.

---

## 6. Open Questions (to refine with community)

- Default privacy level for asset receives (fresh address per asset vs shared).  
- Recommended UX for “watch‑only” assets.  
- Standard set of metadata keys for common asset classes.  
- How far to go with in‑wallet discovery vs respecting DigiByte’s minimal‑promotion ethos.

(End of draft)
