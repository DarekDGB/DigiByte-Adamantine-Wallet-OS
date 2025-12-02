# Adamantine iOS Client — UI Screens

This file describes the **screen structure** for the iOS app using SwiftUI patterns.

## 1. Main Tabs
- Home
- Wallet
- Enigmatic
- Shield
- Settings

## 2. Home / Dashboard
- Total DGB balance
- Total DD balance
- Quick actions: Send / Receive / Mint DD / Chat
- Small shield status strip (Sentinel / DQSN / ADN / Adaptive)

## 3. Wallet Screens
### 3.1 Accounts List
- List of accounts with balances
- Add / manage accounts

### 3.2 Account Detail
- Balance
- Recent transactions
- Buttons: Send / Receive / View DD

### 3.3 Send Flow
- Amount + asset (DGB)
- Contact / address picker
- Guardian pre-check sheet
- Confirmation view with TXID

## 4. DigiDollar (DD)
### 4.1 DD Overview
- Total DD + backing DGB
- Positions list preview
- Buttons: Mint / Redeem

### 4.2 Mint Flow
- Select backing account
- Enter amount
- Review + shield insight
- Confirmation

### 4.3 Redeem Flow
- Select position or amount
- Choose target address
- Guardian step
- Redeem confirmation

## 5. Enigmatic
- Conversation list (with unread badges)
- Chat view (bubbles, timestamps)
- Payment request bubbles with Accept/Reject
- Contact info sheet (trust, verification status)

## 6. Shield
- Overall shield status overview
- Sentinel / DQSN / ADN / Adaptive cards
- “More details” links to diagnostics

## 7. Settings
- Profile & identity
- Guardian profiles & thresholds
- Telemetry opt-in
- Advanced / developer options
