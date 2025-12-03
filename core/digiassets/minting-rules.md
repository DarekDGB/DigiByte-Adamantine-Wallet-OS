# DigiAssets — Minting Rules

Status: draft v0.1

This document describes wallet-side rules for **issuing DigiAssets**
through the Adamantine Wallet.  
It does not change DigiByte consensus – it defines UX and policy
constraints enforced by the wallet.

---

## 1. Asset Creation Models

Supported supply models:

1. `fixed`  
   - Supply defined once at issuance.  
   - No further minting allowed.

2. `capped`  
   - Total cap defined at issuance.  
   - Additional minting allowed until cap reached.  

3. `reissuable`  
   - No hard cap.  
   - Additional issuance allowed under issuer rules.

The model is stored in local metadata and, where supported, encoded in
the DigiAssets payload.

---

## 2. Required Fields

The minting form MUST collect:

- `name`  
- `symbol` (A–Z, 2–10 chars, no spaces)  
- `supply_model` (fixed | capped | reissuable)  
- `initial_supply`  
- `decimals` (0–8 typical)  
- `issuer_account` (wallet account / address)  
- `metadata_uri` (optional, IPFS/HTTPS)  

Optional governance fields:

- `reissue_guardian_required` (bool)  
- `burn_guardian_required` (bool)  

---

## 3. Validation Rules

Before building the mint TX:

- `initial_supply > 0`  
- `symbol` unique in local wallet context (avoid confusion)  
- `initial_supply` does not exceed cap for `capped` model  
- funding UTXO meets DigiByte fee and dust rules  
- issuer account passes Guardian & risk-engine checks  
- PQC container present (QWG integration)  

If any rule fails → mint operation is blocked in the UI.

---

## 4. Guardian Integration

If Guardian protection is enabled:

- mint request generates an **approval entry**  
- required guardians must sign before TX broadcast  
- policy may limit:
  - maximum supply per mint  
  - number of mints per time window  
  - allowed asset types (e.g. disallow reissuable)

---

## 5. Fee & Funding Policy

Minting must:

- pay at least minimum relay fee  
- respect wallet fee policy (fast / normal / eco)  
- optionally include an additional “asset registration” output if such
  convention emerges in the DigiAssets ecosystem

Fees are paid in DGB from the issuer account.

---

## 6. Post-Mint Indexing

After successful broadcast:

1. TX is handed to the DigiAssets indexer.  
2. A new `asset_id` is derived according to DigiAssets spec.  
3. `assets` and `wallet_balances` tables are updated.  
4. UI reflects the new asset in the issuer account.

---

## 7. Anti-Spam & Safety

Wallet may implement optional controls:

- soft limit on number of assets a single wallet can issue  
- warnings for reissuable assets with unlimited supply  
- prompts to review terms before issuing publicly traded tokens
