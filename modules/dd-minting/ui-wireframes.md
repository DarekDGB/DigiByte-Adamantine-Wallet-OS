# DigiDollar (DD) — UI Wireframes (ui-wireframes.md)

Status: **draft v0.1 – internal skeleton**

This document describes the **screen flows and elements** for the DigiDollar
(DD) experience in the Adamantine Wallet.

It is **not** a visual design specification, but a structural guide for
web / iOS / Android clients (`clients/web`, `clients/ios`, `clients/android`).

---

## 1. Screens Overview

Key DD-related screens:

1. **DD Overview**
   - Shows total DD balance and backing DGB.
   - Entry point for mint / redeem.
2. **Mint DD — Wizard**
   - Step-by-step flow to create DD.
3. **Redeem DD — Wizard**
   - Step-by-step flow to burn DD and unlock DGB.
4. **DD Positions / History**
   - List of individual DD positions.
5. **DD Settings**
   - Auto-rollover, preferred account, oracle visibility, etc.

---

## 2. DD Overview Screen

Elements (conceptual):

```text
[ Header ]
  Title: DigiDollar (DD)
  Sub: Backed by locked DigiByte (DGB)

[ Balances Card ]
  - Total DD:  1 234.56 DD
  - Backing:  1 234.56 DGB
  - (Optional) ≈ Fiat:  $X (if oracle available)

[ Status / Shield Row ]
  - Shield status:  [● Guardian: Enforce] [● Shield: Online]
  - Tap → diagnostics

[ Actions ]
  [ Mint DD ]   [ Redeem DD ]

[ Positions Preview ]
  - List top 3 active positions
  - Each item: amount, created_at, status badge (Pending, Active, etc.)
  - “View all positions” link
```

---

## 3. Mint DD — Wizard

Suggested steps:

### Step 1: Choose Account & Amount

```text
[ Choose Backing Account ]
  - Dropdown / list of DGB accounts with balances

[ Amount Input ]
  - Input: Amount in DGB  (primary)
  - Optional toggle: "Enter DD amount instead"

  - Inline info:
    - Available: XX DGB
    - Min / Max hints
    - Approx DD: YY (if needed)

[ Info ]
  - Text: "DD is backed 1:1 by locked DigiByte UTXOs."
  - Link: "Learn more" → docs/ or help screen.

[ Button ]
  [ Continue ]
```

### Step 2: Review & Guardian Pre-Check

```text
[ Summary ]
  - From account:  <name>
  - Backing amount: XX DGB
  - New DD:         YY DD
  - Fee estimate:   ~ZZ DGB

[ Shield Insight ]
  - Badge: e.g. "Network: Normal" or "Network: Degraded"
  - Text:  "Guardian will check this operation before broadcasting."

[ Button ]
  [ Continue ]  [ Cancel ]
```

When user taps Continue, UI builds `ActionRequest` and calls Guardian.
If Guardian requires a challenge, show biometric / passphrase step.

### Step 3: Confirmation

```text
[ Result ]
  - State: "Mint submitted"
  - TXID (shortened): abc123...
  - Status: "Waiting for confirmations"

[ Actions ]
  - [ View details ]
  - [ Done ]
```

---

## 4. Redeem DD — Wizard

Similar structure, mirrored.

### Step 1: Choose Position or Amount

Option A — by position:

```text
[ List of positions ]
  - Each row: amount, created_at, status
  - Select one or multiple
```

Option B — by amount:

```text
[ Amount Input ]
  - Input: Amount in DD
  - Show: Max redeemable: XX DD
```

Also show:

```text
[ Target Address ]
  - Default: main receive address for account
  - Advanced: choose custom address (e.g. cold storage)
```

### Step 2: Review & Guardian Check

```text
[ Summary ]
  - Redeem:   XX DD
  - Backing:  YY DGB
  - To:       <address or contact>
  - Fee est:  ~ZZ DGB

[ Shield Insight ]
  - "Guardian will evaluate this redeem operation."

[ Button ]
  [ Continue ] [ Cancel ]
```

After Guardian, handle actions as usual (allow / challenge / block).

### Step 3: Completion

```text
[ Result ]
  - "Redeem transaction submitted"
  - TXID
  - Status: "Confirming"

[ Actions ]
  - [ View in history ]
  - [ Done ]
```

---

## 5. DD Positions / History Screen

```text
[ Filter Bar ]
  - Tabs:  Active | Redeeming | Redeemed | All

[ List ]
  For each position:
    - Amount:   XX DD
    - Backing:  YY DGB
    - Created:  date/time
    - Status:   badge
    - Tap → details
```

Details view may include:

- mint TXID
- backing UTXOs (summarised)
- confirm/count
- QAC confidence level
- history of state changes.

---

## 6. DD Settings Screen

Elements:

```text
[ General ]
  - Default backing account: <dropdown>
  - DD overview in main dashboard: [On/Off]

[ Behaviour ]
  - Auto-rollover options (future)
  - Show fiat equivalent: [On/Off]

[ Safety ]
  - Min Guardian challenge amount for DD actions
  - Misc explanatory text
```

All safety-sensitive settings (like disabling advanced checks) must be
guarded through the **Guardian settings-change flow**.

---

## 7. Platform Notes

- **Web**: can show richer tables and tooltips.
- **Mobile (iOS/Android)**: should focus on clarity, larger tap targets.
- Shared concepts must map cleanly to each platform’s design system
  (SwiftUI, Jetpack Compose, etc.).

Concrete visual design is left to the UI / UX implementation phase.
