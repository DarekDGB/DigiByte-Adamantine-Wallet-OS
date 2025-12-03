# DigiAssets Guardian Rules (guardian-rules.md)

Status: **draft v0.1 – internal skeleton**

This document defines the **security, risk, and guardian policies**
applied to DigiAssets inside the Adamantine Wallet.

The goal is to prevent:

- scams,
- malicious metadata,
- unsafe transfers,
- abusive issuances,
- spam assets,
- risky counterparties,
- and chain-level anomalies from impacting users.

These rules extend Adamantine’s existing security layers:

- **Guardian Wallet**
- **Risk Engine**
- **Quantum Wallet Guard (QWG)**
- **Shield Bridge**
- **Sentinel AI v2**
- **DQSN**
- **ADN**
- **Quantum Adaptive Core**

---

# 1. Risk Categories

Guardian evaluates DigiAssets actions across 4 main categories:

1. **Recipient risk**
2. **Asset risk**
3. **Metadata risk**
4. **Chain / environment risk**

Each category outputs a risk level:

- LOW  
- MEDIUM  
- HIGH  
- CRITICAL  

Guardian aggregates these into a final verdict:

- ALLOW  
- WARN  
- REQUIRE_CONFIRMATION  
- BLOCK  

---

# 2. Recipient Risk Rules

### 2.1 Unknown recipient address  
If the address has:
- no prior interactions with user,
- no label or contact entry,
- no transaction history with this wallet,

→ Risk: **MEDIUM**  
→ Action: show warning: *“Unknown receiver — double‑check address”*

### 2.2 Suspicious recipient patterns  
Seen in:
- scam lists,
- phishing clusters,
- darknet-pattern address clusters (from Sentinel or Shield Bridge),

→ Risk: **HIGH** or **CRITICAL**  
→ Action: **BLOCK** or require strong confirmation.

### 2.3 New or untrusted contacts  
If contact was added recently or from QR scan:

→ Risk: **MEDIUM**  
→ Require biometric confirmation.

---

# 3. Asset Risk Rules

### 3.1 High-value asset  
NFTs or tokens with large off-chain monetary value (estimated via oracle):

→ Risk: **MEDIUM → HIGH**  
→ Extra confirmation required.

### 3.2 Rare NFT / certificate  
If asset has only **1 edition**:

→ Risk: **HIGH**  
→ Confirmation + shield call.

### 3.3 Spam asset  
If incoming asset is:
- unknown issuer,
- zero metadata,
- repeated across many addresses,
- flagged by indexers as spam airdrop,

→ Risk: **LOW → MEDIUM**  
→ Warn user when interacting.

### 3.4 Malformed asset  
Missing critical metadata:
- name,
- type,
- asset_id,

→ Risk: **MEDIUM**  
→ Show bright warning.

---

# 4. Metadata Risk Rules

### 4.1 Metadata hash mismatch  
If the wallet downloads metadata and computed hash != expected:

→ Risk: **CRITICAL**  
→ BLOCK transfer + show:  
*“Metadata integrity failure – possible forgery.”*

### 4.2 URL reputation  
For external media / metadata URLs:

- bad domain → **HIGH**
- unknown domain → **MEDIUM**
- trusted domain → **LOW**

Provided by Shield Bridge or local heuristic list.

### 4.3 Oversized or dangerous media  
If media file too large or suspicious:

→ Risk: **MEDIUM**  
→ UI shows warning.

### 4.4 Non-HTTPS URLs  
Except for IPFS:

→ Risk: **MEDIUM**  
→ “Use caution — unencrypted link.”

---

# 5. Chain / Environment Risk

### 5.1 Sentinel chain anomaly  
Heavy mempool anomaly or suspicious cluster:

→ Risk overlay = **heightened**  
→ Guardian raises to MEDIUM/HIGH.

### 5.2 DQSN reorg risk  
Deep reorg indicators:

→ Risk overlay = **critical_chain_risk**  
→ BLOCK all high-value DigiAssets transfers.

### 5.3 ADN lockdown  
ADN in lockdown:

→ **BLOCK all transfers**, even low value.

### 5.4 QAC heightened mode  
Adaptive Core detects unusual patterns:

→ Require confirmation OR block (depending on mode).

---

# 6. Issuance (Mint) Risk Rules

### 6.1 New issuer address  
If address is recently created:

→ Risk: **MEDIUM**  
→ Warn user: *“New issuer address – verify authenticity.”*

### 6.2 Excessive minting  
Rapid or repeated mints in short time window:

→ Risk: **HIGH**  
→ Warn or block spam-like minting.

### 6.3 Suspicious metadata during mint  
Bad links, unsafe URLs, mismatched hashes:

→ Risk: **HIGH**  
→ BLOCK mint.

### 6.4 Large-supply fungible token  
Huge supply (> configured threshold):

→ Risk: **MEDIUM**  
→ Ask for confirmation.

---

# 7. Guardian Verdict Logic

### LOW  
- Transfer allowed.  
- Normal UX.

### MEDIUM  
- Requires confirmation (biometric / PIN).  
- Display warnings.

### HIGH  
- Double confirmation or shield escalation.  
- Transfer may be blocked if metadata risk is HIGH.

### CRITICAL  
- Always **BLOCK**.  
- Example: metadata hash mismatch, Shield lockdown, reorg risk.

---

# 8. Shield Bridge Integration

Guardian sends:

```
/shield/pre_asset_action
/shield/post_asset_action
```

Payload includes:

- asset_id (hashed),
- recipient classification,
- metadata hash state,
- risk factors triggered,
- action type (mint/transfer).

Shield Bridge returns overlays:

- none  
- elevated  
- heightened  
- critical_chain_risk  
- lockdown  

These overlays adjust Guardian’s decision.

---

# 9. UI Behaviour Summary

### Warnings
Displayed for:
- unknown recipients,
- bad metadata links,
- trusted but new issuers,
- large token transfers.

### Blocks
Triggered for:
- CRITICAL metadata risk,
- chain anomaly overlays,
- shield lockdowns,
- suspicious recipients.

---

Author: **DarekDGB**  
License: MIT
