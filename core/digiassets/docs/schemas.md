# 📘 DigiAssets Schemas — Core Schema Definitions (v0.2)

This document defines the **canonical schemas** used by the DigiAssets subsystem inside Adamantine Wallet.  
All structures are versioned, strongly typed, and validated before being consumed by the engine, Guardian, or Shield‑Bridge.

---

# 1. AssetDefinition Schema

```json
{
  "version": "1.0",
  "asset_id": "string",
  "name": "string",
  "ticker": "string",
  "supply": {
    "cap": "integer | null",
    "initial": "integer",
    "mutable": "boolean"
  },
  "metadata": {
    "type": "object",
    "properties": {}
  },
  "rules": {
    "transferable": "boolean",
    "burnable": "boolean",
    "freeze_enabled": "boolean"
  }
}
```

### Notes
- `cap = null` enables infinite issuance (Guardian will warn).
- `mutable = false` ensures mint rules cannot change after issuance.
- Metadata is free-form but size-limited by the encoding strategy.

---

# 2. AssetInstance Schema

Represents a **specific quantity** of an asset held by a user.

```json
{
  "version": "1.0",
  "asset_id": "string",
  "amount": "integer",
  "owner_utxo": "string",
  "timestamp": "integer"
}
```

---

# 3. TransferIntent Schema

Defines a transfer request **before it becomes a DigiByte transaction**.

```json
{
  "version": "1.0",
  "asset_id": "string",
  "inputs": [
    {
      "utxo": "string",
      "amount": "integer"
    }
  ],
  "outputs": [
    {
      "address": "string",
      "amount": "integer"
    }
  ],
  "change_address": "string",
  "fee_rate": "integer",
  "metadata": {}
}
```

### Guardian consumes this structure *before* signing.

---

# 4. MintIntent Schema

Defines minting rules for new DigiAssets **or DigiDollar DD**.

```json
{
  "version": "1.0",
  "asset_id": "string",
  "mint_amount": "integer",
  "destination_address": "string",
  "metadata": {},
  "supply_rules": {
    "cap": "integer | null",
    "remaining_supply": "integer"
  }
}
```

Guardian ensures:
- supply is not exceeded,
- metadata matches asset definition,
- mint flow is safe.

---

# 5. BurnIntent Schema

```json
{
  "version": "1.0",
  "asset_id": "string",
  "amount": "integer",
  "burn_utxo": "string",
  "reason": "string | null"
}
```

---

# 6. Metadata Schema

Metadata is free-form but must follow a constrained envelope.

```json
{
  "version": "1.0",
  "schema": "digiasset-metadata-v1",
  "attributes": {
    "name": "string",
    "description": "string",
    "image_url": "string | null",
    "external_url": "string | null",
    "properties": {}
  }
}
```

Size limit: **within DigiByte's OP_RETURN 80-byte payload plane**, using compression + plane splitting.

---

# 7. RuleSet Schema

```json
{
  "version": "1.0",
  "transfer_rules": {
    "allowed": "boolean",
    "max_batch": "integer",
    "restricted_addresses": []
  },
  "mint_rules": {
    "allowed": "boolean",
    "max_per_tx": "integer"
  },
  "burn_rules": {
    "allowed": "boolean"
  }
}
```

Guardian uses these in:
- scoring
- contextual rules
- lockdown events

---

# 8. IndexerRecord Schema

What the Indexer writes as a normalized record:

```json
{
  "asset_id": "string",
  "txid": "string",
  "height": "integer",
  "timestamp": "integer",
  "event_type": "MINT | TRANSFER | BURN",
  "changes": [
    {
      "address": "string",
      "delta": "integer"
    }
  ],
  "metadata": {}
}
```

---

# 9. Validation Schema (for internal engine checks)

```json
{
  "required_fields": ["version", "asset_id"],
  "allowed_versions": ["1.0"],
  "max_metadata_size": 4096,
  "max_outputs": 32,
  "max_inputs": 32
}
```

---

# 10. Guardian Consumption Summary

Guardian consumes all schema types via:

- `guardian_adapter.py`
- `guardian_policy.py`
- `guardian_config.py`

For each schema:
- **TransferIntent** → runs full scoring + risk evaluation  
- **MintIntent** → enforces supply integrity  
- **RuleSet** → determines block/allow states  
- **Metadata** → scanned for anomalies via Shield‑Bridge  

---

# 11. File Placement

Place this file at:

```
core/digiassets/docs/schemas.md
```

---

# 12. Version

```
Schema package version: 0.2
```

