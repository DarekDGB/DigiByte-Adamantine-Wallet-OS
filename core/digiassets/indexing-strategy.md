# DigiAssets — Indexing Strategy

Status: draft v0.1

This document defines how the Adamantine Wallet indexes **DigiAssets**
on top of the DigiByte UTXO set.  
The goal is to keep a local, consistent view of:

- asset definitions
- wallet-owned balances
- asset transaction history
- pending / conflicted states after reorgs

The indexer **does not** change consensus rules – it is a pure
client-side view built from standard DigiByte transactions.

---

## 1. Data Model

The indexer maintains four logical tables in the wallet database:

1. `assets`  
   - `asset_id`  
   - `issuer_txid`  
   - `supply_model` (fixed | capped | reissuable)  
   - `decimals`  
   - `symbol`, `name`  
   - `metadata_uri` (optional)  
   - `issuer_pubkey`  

2. `utxo_assets`  
   - `txid:vout`  
   - `asset_id`  
   - `amount`  
   - `owner_script`  

3. `wallet_balances`  
   - `asset_id`  
   - `wallet_account_id`  
   - `confirmed_amount`  
   - `pending_delta`  

4. `asset_history`  
   - `txid`  
   - `block_height` (nullable for mempool)  
   - `op_type` (issue | transfer | burn | reissue)  
   - `asset_id`  
   - `amount`  
   - `from_addr` / `to_addr` (where derivable)

---

## 2. Sync Strategy

### 2.1 Initial Sync

1. Determine address set for all wallet accounts.  
2. Stream DigiByte blocks from the node (RPC or light client).  
3. For each TX:
   - detect DigiAssets envelope
   - classify operation
   - update tables above

Initial sync may be **pruned** to the earliest block containing a
wallet-owned asset TX (checkpointed per wallet).

### 2.2 Incremental Sync

For new blocks:

1. Pull block headers and transactions.  
2. Apply same parsing and classification as during initial sync.  
3. Update balances and history in a single atomic DB transaction.  

For mempool:

- observe unconfirmed DigiAssets TXs affecting wallet addresses  
- mark `block_height = null` and keep `pending_delta` fields updated  

---

## 3. Reorg Handling

On chain reorg:

1. Identify orphaned blocks and affected TXs.  
2. Roll back **asset_history** entries for those TXs.  
3. Rebuild `utxo_assets` and `wallet_balances` for impacted asset IDs.  
4. Apply new main-chain blocks in order.

All changes are deterministic and derived only from the final chain.

---

## 4. Address & Account Mapping

The indexer treats the wallet as a tree of accounts:

- `wallet_account` → list of addresses / scripts  
- address ownership is determined from the local HD keys  

Any DigiAssets UTXO with an `owner_script` matching those addresses is
considered **wallet-owned** and counted toward balances.

---

## 5. Performance Considerations

- Cached lookups for `asset_id` metadata  
- Batched DB writes per block  
- Optional **“watchlist only”** mode that tracks a configured set of
  asset IDs rather than the entire chain

---

## 6. Export & Backup

The wallet may export:

- full asset list for backup  
- per-account balance summaries  
- raw history suitable for audit or migration

These exports are read-only views of the indexed state and can be
reconstructed from chain data if lost.
