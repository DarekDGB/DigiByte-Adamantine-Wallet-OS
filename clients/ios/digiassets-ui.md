# DigiAssets UI — iOS Client

Status: **draft v0.1 – UX/flows skeleton**  
Target platform: **iOS (SwiftUI)**  
Scope: **DigiByte-Adamantine-Wallet – DigiAssets module**

This document defines the **screen map, navigation flows, and key UX rules**
for DigiAssets support on the **iOS client**. It mirrors the Android / Web
DigiAssets UX so that behaviour is consistent across platforms.

---

## 1. High–level UX goals

1. Simple entry: DigiAssets live in a **separate tab/section**, but are
   always one tap away from the main wallet home.
2. Clear separation: Users always see **which chain-layer** a thing belongs
   to:
   - DGB (UTXO coins)
   - DigiAssets (token layer on top of DGB)
   - DigiDollar (if enabled)
3. Safety first:
   - Every send/mint/redemption flow has **2-step confirmation**.
   - Risk engine + shield flags (from Guardian / Shield Bridge) are shown
     as **banners, badges, or warnings** where relevant.
4. Performance:
   - Use **lazy lists** and **incremental loading** for large portfolios
     or history.
5. Accessibility:
   - Dynamic type, VoiceOver, and high-contrast aware color choices.

(Actual colors/branding will follow the global Adamantine Wallet design
system.)

---

## 2. Navigation map

Primary entry points on iOS:

- **Tab bar** item: `Assets`
  - Icon: token / layered-circle motif (TBD in design system).
  - Badge: shows **unread activity** count for assets (mints, burns,
    transfers, airdrops).

Sub–navigation within the Assets tab:

1. **AssetsHomeView**
   - Portfolio summary
   - List of held assets
   - CTAs: *Receive*, *Send*, *Mint* (if enabled), *Explore*

2. **AssetDetailView**
   - Asset identity + metadata
   - Balance and valuation (if price-feed exists)
   - Tabs:
     - Overview
     - History
     - Holders (optional)
     - Governance / Rules (if applicable)

3. **SendAssetFlow**
   - Recipient entry
   - Amount / token selection
   - Fees + risk signals
   - Final confirmation (with DGB fee breakdown)

4. **ReceiveAssetView**
   - Asset–specific receive address / path
   - QR & copy buttons
   - Network tips

5. **MintAssetFlow** (for issuers)
   - Asset definition
   - Supply rules
   - Collateral / DGB anchoring
   - Final review

6. **ActivityCenterView**
   - Filterable feed of asset events (mints, sends, burns, redemptions).

---

## 3. Screen–level specs

### 3.1 AssetsHomeView (portfolio)

**Route**: `assets/home`  
**Type**: `SwiftUI view`

**Sections**:

1. **Header**
   - Wallet name / account selector.
   - `Total Assets Value` (optional, only if price feeds exist).
   - Shield health badge (read-only signal from Shield Bridge / Guardian).

2. **Primary actions**
   - `Receive` – opens ReceiveAssetView (asset pre-selected if launched
     from AssetDetailView, otherwise generic).
   - `Send` – opens asset picker then SendAssetFlow.
   - `Mint` – only shown if advanced mode is enabled.

3. **Assets list**
   - `ForEach` over user assets, sorted by:
     - Pinned > custom order > market value.
   - Cell content:
     - Asset icon / color band.
     - Asset name + short symbol.
     - Balance + fiat equivalent (if available).
     - Small shield/risk chip if asset is on a watchlist or has
       non‑default risk score.

4. **Empty state**
   - Illustration + copy:
     > “You don’t hold any DigiAssets yet. Receive your first token or
     > explore supported asset issuers.”
   - Buttons: `Receive token`, `Explore`.

---

### 3.2 AssetDetailView

**Route**: `assets/{assetId}`

**Header**:

- Icon, name, symbol.
- Issuer tag (verified / unverified).
- Current balance.
- Fiat equivalent + 24h change if supported.

**Tabbed content** (segmented control):

1. **Overview tab**
   - Short description.
   - Asset type (fungible, NFT, multi-asset).
   - Supply and circulating info if available.
   - External links (website, docs, issuer profile).

2. **History tab**
   - Reverse-chronological list of transactions for this asset.
   - Each row:
     - Direction (in/out).
     - Counterparty (if resolved).
     - Amount.
     - Timestamp + status.
     - Shield/risk icon if event was flagged.

3. **Holders tab (optional)**
   - Only for public / on-chain visible holder sets.
   - Paginated list with basic anonymised info.

4. **Rules / Governance tab (optional)**
   - Redemption rules, mint/burn policy, KYC notes, etc.

**Footer actions**:

- `Send`
- `Receive`
- `More` (overflow menu: Add to favourites, Hide asset, View on explorer).

---

### 3.3 SendAssetFlow (multi-step)

**Route**: `assets/{assetId}/send`

**Step 1 – Recipient**

- Text field with paste / QR buttons.
- Optional contact picker.
- Live validation banner:
  - “Valid DigiByte address” / error states.
- Shield/risk banner if destination is on a watchlist.

**Step 2 – Amount**

- Numeric input (token amount).
- Available balance summary.
- “Send max” pill.
- Fee info row:
  - DGB network fee (estimated).
  - Additional asset-specific fees (if any).

**Step 3 – Review & confirm**

- Static summary card:
  - From account.
  - To address (shortened, tappable to expand).
  - Asset + amount.
  - Total DGB fee.
- Risk summary chip, e.g.:
  - “Low risk – standard send”
  - “Warning – high fee, slow confirmation expected”
- `Confirm & Send` button (requires biometric / passcode if enabled).

---

### 3.4 ReceiveAssetView

**Route**: `assets/{assetId}/receive`

- QR code for receive address/path.
- Full address (copy button).
- “Share” button (system share sheet).
- Short helper text:
  - “Only send **{assetName}** on DigiByte to this address.”
- Option to copy **DGB fallback address** if some issuers require it.

---

### 3.5 MintAssetFlow (advanced / issuer mode)

**Guardrail**: Only shown when **Advanced Issuer Mode** is enabled in
settings.

Steps:

1. **Define asset**
   - Name, symbol, description.
   - Asset type (fungible/NFT/multi-asset).
   - Optional icon (URL or future on-chain reference).

2. **Supply rules**
   - Total supply, decimals.
   - Mutable vs fixed supply flag.
   - Optional freeze/burn permissions.

3. **Anchoring & fees**
   - DGB collateral/fee summary.
   - Preview of underlying DigiByte transaction pattern.

4. **Review & mint**
   - Full summary card.
   - Confirmation with explicit “this may be permanent” text.

---

## 4. Integration points

- **Guardian / Shield Bridge**
  - Read-only risk signals (per-asset + per-transaction).
  - UI surfaces:
    - badges on list rows,
    - banners on confirm screens,
    - modals for severe risk.

- **Analytics & Telemetry**
  - Log only **non-PII, coarse UX events**, e.g.:
    - asset_view_opened, send_flow_started, mint_flow_completed.
  - Respect privacy model from `modules/analytics-telemetry/` docs.

- **DigiAssets Core Module**
  - All state (balances, metadata, history) comes from the shared
    DigiAssets core service; iOS UI is a **thin client**.

---

## 5. Open questions / TODOs

- Final visual design, colors, and typography – to follow global wallet
  design system.
- Exact mapping between DigiAssets protocol fields and UI metadata
  fields (names, icons, custom fields).
- NFT gallery layouts and media handling strategies.
- Per-asset notification preferences (mints only, all transfers, none).

When these items are clarified, this spec should be upgraded from
**draft v0.1** to **v1.0** and wired into the iOS implementation plan.
