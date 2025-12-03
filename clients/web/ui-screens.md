# Adamantine Web Client — UI Screens

This file defines the **Web UI layout** using standard responsive web conventions
(e.g. React + TypeScript, but framework-agnostic at the spec level).

## 1. Dashboard
- DGB balance overview
- DigiDollar (DD) balance overview
- DigiAssets summary widget (total assets + top movers)
- Shield indicators (Sentinel / DQSN / ADN / Adaptive Core)
- Quick actions:
  - Send
  - Receive
  - Mint DD
  - Send Asset
  - Enigmatic Messages

## 2. Accounts
- Account list panel
- Account details view
- QR receive modal
- Transaction history table with filters:
  - Type (DGB / DD / DigiAssets)
  - Direction (in / out)
  - Status (pending / confirmed / failed)

## 3. Send Flow (DGB / DD)
- Step 1: Asset selector (DGB or DD)
- Step 2: Amount entry with live balance + fee estimate
- Step 3: Recipient entry (address / contact)
- Step 4: Guardian review (limits, policy hits)
- Step 5: Shield diagnostics summary
- Step 6: Final confirm + progress state

## 4. DigiDollar (DD)
### Mint
- Account selector
- Amount input
- Current rate / oracle info (if applicable)
- Shield preflight check (liquidity, abnormal activity)
- Review & confirm panel
- Result screen with tx hash and status

### Redeem
- Position selector (choose DD source if multiple)
- Amount input (partial / full)
- Guardian approval (if thresholds reached)
- Network fee preview
- Confirmation and result

## 5. Enigmatic Messaging
- Conversation list sidebar
- Message thread view
- Composer with:
  - Text
  - Optional payment request (DGB / DD / Asset)
- Accept / Reject payment request buttons
- “View on chain” link for Enigmatic frames (advanced users)

## 6. Shield Diagnostics
- Overview page:
  - Shield status banner (green / amber / red)
  - Recent alerts list
- Tabs:
  - Sentinel: network drift, mempool anomalies
  - DQSN: node consensus health
  - ADN: node lockdown / policy events
  - Adaptive Core: learning highlights, unusual pattern notes
- Export logs button

## 7. Settings
- Profile
- Key management (view xpub, export instructions)
- Guardian rules configuration
- Privacy / telemetry toggles
- Network configuration (mainnet / testnet, custom RPCs)

## 8. DigiAssets (high-level)
- Link to dedicated DigiAssets area:
  - Portfolio
  - Asset details
  - Send / Receive
  - Issue / Mint
  - History
