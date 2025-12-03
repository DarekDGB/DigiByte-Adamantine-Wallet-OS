# DigiAssets UI Wireframes (ui-wireframes.md)

Status: **draft v0.1 – internal skeleton**

This document describes the **screen layout and UX structure** for
DigiAssets inside the Adamantine Wallet on:

- iOS (SwiftUI)
- Android (Jetpack Compose)
- Web (PWA)

The goal is to keep all three platforms visually aligned while using
their native UI components.

---

# 1. Navigation Overview

DigiAssets will surface in two main places:

1. **Main tab structure** (example):
   - Home
   - Wallet
   - **Assets**
   - Enigmatic
   - Shield
   - Settings

2. **Per-account view**:
   - `Account → Assets` section (DGB balance + assets balance)

---

# 2. Assets Tab – Overview Screen

### Layout

- **Header**
  - Title: `Assets`
  - Subtext: `DigiAssets held by this wallet`

- **Sections**
  1. **Summary cards**
     - `Total asset types`: e.g. 12
     - `NFTs`: e.g. 5
     - `Tokens`: e.g. 6
     - `Certificates`: e.g. 1
  2. **Filter bar**
     - All | Tokens | NFTs | Certificates
  3. **Asset list**
     - Repeating rows/cards:

       ```
       [Thumbnail]  [Asset Name]
                    [Ticker] • [Type]
                    [Balance / Ownership status]
       ```

- **Floating action button (mobile) / Primary button (web)**
  - Label: `Mint DigiAsset`
  - Takes user to **Mint flow**.

---

# 3. Asset Detail Screen

### Layout

- **Header**
  - Asset name
  - Ticker
  - Type badge (Token / NFT / Certificate)

- **Top info section**
  - Thumbnail / image (for NFT + certificate)
  - “Owned by you” / “Partially owned” / “Not owned” status
  - Balance (for tokens)

- **Tabs or sections**
  1. **Overview**
     - Description
     - Basic metadata (type, asset ID short, issuer label)
     - External links (open in browser, clearly labelled)
  2. **History**
     - List of recent transfers involving this wallet:
       - date/time
       - direction (sent / received)
       - counterparty label or address stub
       - amount
       - txid (link to explorer)
  3. **Metadata**
     - Raw metadata view (key/value grid)
     - Hash verification status:
       - Green: “Content hash verified”
       - Yellow: “Not verified”
       - Red: “Hash mismatch” (block actions)

- **Actions**
  - Primary: `Send`
  - Secondary: `View in Explorer`
  - For tokens: `View Holders` (if indexer supports)
  - For NFTs/certificates: `View Certificate` / `View Full Media`

---

# 4. Mint DigiAsset Flow — Screens

## 4.1 Mint Type Selection

Screen:

- Title: `Mint DigiAsset`
- Buttons/cards:
  - `Fungible Token`
  - `NFT / Collectible`
  - `Certificate / Document`

Each shows short description underneath.

---

## 4.2 Common Details Screen

Fields:

- Name (text field)
- Ticker / Symbol (short text)
- Description (multiline)
- Category (dropdown or tag row)
- Issuing account (account selector)

At bottom:

- `Next` button.

---

## 4.3 Mode-Specific Screens

### 4.3.1 Fungible Token

Fields:

- Total supply
- Divisibility (decimals, if supported)
- Initial allocation (default: full supply to issuing account)

Buttons:

- `Back`
- `Review Mint`

---

### 4.3.2 NFT / Collectible

Fields:

- Edition size (defaults to 1)
- Media:
  - Pick image / media (mobile: gallery/file picker)
  - Or paste URL
- Metadata hash (optional but recommended)

Buttons:

- `Back`
- `Review Mint`

---

### 4.3.3 Certificate / Document

Fields:

- Subject (text)
- Validity (from / to)
- Reference ID (optional)
- Document hash (text) or “Compute from file” button (future)

Buttons:

- `Back`
- `Review Mint`

---

## 4.4 Mint Review + Guardian Screen

Shows:

- Asset summary:
  - Name, type, symbol
  - Supply / edition
  - Subject (for certificates)
- Issuing account & address
- Fee estimate
- Guardian risk level:

  ```
  Risk: LOW / MEDIUM / HIGH / CRITICAL
  [Reason labels: new issuer, high value, etc.]
  ```

If risk is:

- LOW → “Ready to mint” with simple confirmation.
- MEDIUM → show yellow warning, require extra tap: `I understand, continue`.
- HIGH → require biometric / PIN.
- CRITICAL → disable `Mint` button, show reason.

Buttons:

- `Cancel`
- `Mint`

---

# 5. Send DigiAsset Flow — Screens

## 5.1 Send Form

Header: `Send DigiAsset`

- From:
  - Account selector
- Asset:
  - Asset picker or pre-selected asset
- To:
  - Address input
  - QR scan button
  - Contact picker (icon)
- Amount:
  - Text field for tokens
  - For NFTs/certificates:
    - Dropdown of owned items / IDs

Optional:

- Note (local only, or off-chain tag)

Bottom:

- `Next: Review & Secure Send`

---

## 5.2 Send Review + Guardian Screen

Shows:

- Asset name, symbol, type
- Amount or NFT identifier
- From account
- To address / contact label
- Network fee estimate
- Guardian summary card:

  ```
  Guardian Verdict: MEDIUM RISK
  - Unknown recipient
  - New contact
  ```

Buttons:

- `Back`
- `Send` (if allowed)
- If risk CRITICAL → `Send` disabled, only `Back` / `Details`.

---

# 6. NFT / Certificate Dedicated Views

## 6.1 NFT Viewer

Layout:

- Large image at top.
- Name + edition (e.g. `#1 of 10`).
- Owned status (Owned / Not owned).
- Description.
- Metadata hash status.
- Buttons:
  - `Send`
  - `View raw metadata`
  - `Open external link`

---

## 6.2 Certificate Viewer

Layout:

- Stylised certificate panel:
  - Subject name
  - Issuer
  - Validity dates
  - Reference ID
- Status chips:
  - `Valid`
  - `Expired`
  - `Revoked` (if supported in future)
- Buttons:
  - `Send`
  - `Verify Document Hash` (future flow)
  - `View raw metadata`

---

# 7. Warnings & Risk UI

### Warning banner styles

- **Yellow** – caution:
  - Unknown recipient
  - Incomplete metadata
  - New issuer address

- **Red** – danger:
  - Metadata hash mismatch
  - Shield lockdown
  - Chain reorg / critical alerts

Each warning includes a short, readable explanation.

---

# 8. Platform Notes

### iOS (SwiftUI)

- Use NavigationStack for flows.
- Large titles for main screens.
- FAB replaced with trailing nav bar button: `+ Mint`.

### Android (Compose)

- Bottom navigation for tabs.
- Floating Action Button (`Mint`) in Assets list.
- Material 3 cards for asset items.

### Web

- Left sidebar navigation.
- Top toolbar with `Mint` button.
- Asset list as responsive grid on larger screens.

---

Author: **DarekDGB**  
License: MIT
