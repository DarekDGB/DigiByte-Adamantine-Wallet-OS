# DigiAssets — Transaction Parsing

Status: draft v0.1

This document defines how the Adamantine Wallet interprets raw DigiByte
transactions as **DigiAssets operations**.

Parsing is **stateless and deterministic**: any node or wallet that
applies the same rules to the same TX must arrive at the same result.

---

## 1. Detection

A transaction is considered a **candidate DigiAssets TX** when:

- it contains an output following the DigiAssets envelope pattern
  (e.g. OP_RETURN with recognised prefix), or  
- it is linked via protocol-specific markers to a known asset TX.

If no envelope is present, the TX is treated as a pure DGB transaction.

---

## 2. Envelope Structure (Abstract)

For indexing purposes we treat the payload generically:

```
[protocol_prefix][version][operation][payload...]
```

Where:

- `protocol_prefix` = DigiAssets identifier bytes  
- `version`         = format version (e.g. 0x01)  
- `operation`       = ISSUE | TRANSFER | BURN | REISSUE  
- `payload`         = operation-specific fields

The exact on-chain encoding is delegated to the canonical DigiAssets
specification; the wallet only needs enough structure to parse fields.

---

## 3. Operation Mapping

From `operation` and context we derive:

- `op_type`         (issue | transfer | burn | reissue)  
- `asset_id`        (from issuer TX or explicit reference)  
- `amount`          (per output)  
- `source_utxos`    (inputs)  
- `target_outputs`  (ownership scripts carrying assets)

---

## 4. Output Assignment

The parser maps DigiAssets amounts to specific UTXOs using:

1. Operation payload ordering rules.  
2. The set of outputs flagged as carrying assets.  
3. Any embedded quantity fields per output.

Outputs not marked as carrying DigiAssets remain regular DGB-only UTXOs.

---

## 5. Error Handling

If parsing fails:

- malformed envelope → TX ignored for DigiAssets purposes  
- unknown `operation` → logged as **unsupported** and skipped  
- inconsistent amounts (e.g. negative, overflow) → TX ignored  

The raw DGB value transfer is still processed by the wallet.

---

## 6. Wallet Ownership

After parsing, the wallet checks:

- whether any **inputs** or **outputs** belong to wallet accounts  
- if yes, it updates:
  - `utxo_assets`  
  - `wallet_balances`  
  - `asset_history`  

This allows correct balances even when only one side of the transfer
belongs to the local wallet.

---

## 7. Extensibility

The parser is designed to support:

- additional operation types (e.g. metadata updates, freeze)  
- multiple DigiAssets versions  
- testnet/signet prefixes distinct from mainnet

Version and network tags are part of the envelope and must be honoured
by the parser to avoid cross-network confusion.
