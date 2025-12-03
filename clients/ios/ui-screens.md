# Adamantine iOS Client — UI Screens

This file defines the **iOS UI layout** using SwiftUI conventions.

## 1. Dashboard
- DGB balance card
- DigiDollar (DD) balance card
- DigiAssets summary (top 3 assets + “View all”)
- Shield indicators (Sentinel / DQSN / ADN / Adaptive Core)
- Quick actions: Send / Receive / Mint DD / Send Asset / Messages

## 2. Accounts
- Account list
- Account details
- QR receive screen
- Transaction history (DGB / DD / DigiAssets filter tabs)

## 3. Send Flow (DGB / DD)
- Amount entry
- Asset selector (DGB / DD)
- Contact / address selector
- Guardian review screen
- Final confirmation + Shield diagnostics summary

## 4. DigiDollar (DD)
### Mint
- Select funding account
- Enter DD amount
- Oracle / rate info panel
- Review screen (fees, limits, shield hints)
- Shield diagnostics preflight
- Mint success screen with transaction hash

### Redeem
- Position selector
- Amount mode (full / partial)
- Guardian approval step
- Network fee preview
- TX confirmation + status updates

## 5. DigiAssets
### Asset List
- Shows all DigiAssets owned
- Filters: Fungible / NFTs / Favorites
- Search by name / ticker / asset ID

### Asset Detail
- Icon, name, ticker, balance
- Metadata section
- Supply info
- Asset-specific history
- Actions: Send / Receive

### Send Asset Flow
- Recipient entry
- Amount entry
- Guardian rule summary
- Shield risk summary
- Final confirmation

### Receive Asset
- QR code
- Address copy button
- Explanation: “Sender must use DigiAssets-compatible wallet”

### Issue / Mint New Asset
- Name, ticker, supply rules, decimals
- Metadata URI
- Fee estimate
- Shield preflight simulation
- Final confirmation with irreversible warning

## 6. Enigmatic Chat
- Conversation list
- Chat view with message bubbles
- Payment requests (DGB / DD / assets)
- Accept / Reject actions
- Encryption status indicator

## 7. Shield Diagnostics
- Global shield health
- Sentinel metrics
- DQSN confidence
- ADN node-status simulation
- Adaptive Core behaviour drift logs
- Export diagnostics

## 8. Settings
- Profile & display name
- Identity keys (view / rotate / backup instructions)
- Guardian rules
- Privacy & telemetry
- Network settings (RPC endpoints, testnet toggle)
