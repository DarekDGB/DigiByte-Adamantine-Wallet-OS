# Adamantine iOS Client — README

This folder contains the **iOS** version of the DigiByte Adamantine Wallet, built using **Swift + SwiftUI**.

## 1. Purpose
The iOS client is the **flagship mobile experience** for Adamantine, designed to:
- run securely on iPhone and iPad
- leverage Secure Enclave & Face ID / Touch ID
- integrate deeply with Guardian Wallet
- provide DD mint/redeem and Enigmatic chat
- surface Shield diagnostics in a clean, native way

## 2. Technology Stack
- Swift
- SwiftUI
- Combine
- LocalAuthentication (biometrics)
- CryptoKit
- BackgroundTasks (periodic sync, shield pings)

## 3. Feature Overview (Skeleton)
- Multi-account DGB wallet
- DigiDollar (DD) balances & positions
- Enigmatic messaging view
- Guardian-aware send flows
- Shield status & diagnostics
- Settings, identity & privacy controls

MIT License — Author: DarekDGB
