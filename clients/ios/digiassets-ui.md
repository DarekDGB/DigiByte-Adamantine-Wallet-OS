# Adamantine iOS Client — DigiAssets UI

This file defines the **DigiAssets UI layer** for the iOS client.

## 1. DigiAssets Dashboard
- Total asset value
- Asset list with icons + balances
- Filters for Fungible / NFTs / Favorites
- Highlight newly received assets

## 2. Asset Detail Screen
- Hero header with icon + ticker
- Metadata viewer (description, issuer, website, hashes)
- Supply and circulating info
- Transaction history tab
- Actions: Send / Receive / View on explorer

## 3. Send Asset Flow
### Step 1 — Recipient
- Paste / scan QR / contact picker
- Inline validation + shield warnings

### Step 2 — Amount
- Units entry
- Max button
- DGB-fee preview

### Step 3 — Guardian & Shield Check
- Guardian approval requirements
- Shield preflight anomaly hints

### Step 4 — Confirmation
- Final TX summary
- Biometric confirmation (Face ID)

## 4. Receive Asset
- Asset-specific address
- QR code
- Copy/share address
- Metadata preview (optional)

## 5. Issue / Mint New Asset
- Asset definition form (name, ticker, supply, decimals)
- Metadata URI or inline JSON preview
- Shield simulation results
- Irreversibility warning
- Mint success screen with asset ID

## 6. Collections
- Sorted NFT collections
- Grid view
- Tap → NFT detail + metadata

## 7. Shield Integration
- Metadata authenticity verification
- Provenance scoring
- Preflight risk detection before transfers
  
