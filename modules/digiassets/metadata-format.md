# DigiAssets Metadata Format Specification (metadata-format.md)

Status: **draft v0.1 – internal skeleton**

This document defines how the Adamantine Wallet reads, interprets,
verifies, and displays **DigiAssets metadata**.

Metadata is the soul of a DigiAsset:
- name  
- description  
- image / media link  
- document hash  
- issuer info  
- certificate details  

Adamantine must render all metadata **cleanly, safely, and consistently**.

---

# 1. Metadata Sources

DigiAssets metadata can come from:

### 1. OP_RETURN payloads  
Embedded metadata or pointers stored directly in the DigiByte
transaction.

### 2. External URLs  
HTTP(S) links to:
- JSON metadata files,
- images / thumbnails,
- documents.

### 3. Content Hashes  
Strong verification using:
- SHA-256,
- or other supported digests.

### 4. DigiAssets Indexer  
An external service that aggregates:
- asset definitions,
- metadata bundles,
- provenance info.

Adamantine supports all 4, preferring **hash-verified data** when
available.

---

# 2. Metadata Structure (Conceptual)

Standard DigiAssets models typically include fields like:

```json
{
  "asset_id": "string",
  "type": "token | nft | certificate",
  "name": "Example Asset",
  "ticker": "EXA",
  "description": "Human-readable description.",
  "media": {
    "image": "https://example.com/image.png",
    "thumbnail": "https://example.com/thumb.png"
  },
  "urls": [
    "https://example.com",
    "ipfs://QmHash"
  ],
  "hashes": {
    "content": "sha256:abcdef12345..."
  },
  "certificate": {
    "subject": "Name / company",
    "valid_from": "ISO8601 date",
    "valid_to": "ISO8601 date",
    "reference_id": "external id"
  }
}
```

Adamantine will define a **canonical internal structure** to store this
data in the wallet UI model.

---

# 3. Metadata Retrieval Pipeline

When viewing a DigiAsset, Adamantine performs:

### Step 1 — Read on-chain metadata  
From OP_RETURN or protocol-specific fields.

### Step 2 — Parse DigiAssets metadata object  
If present in encoded form.

### Step 3 — Resolve external URLs  
Fetch JSON metadata or media when needed.

### Step 4 — Verify content hashes  
If metadata contains SHA-256 digest:
- hash the retrieved content,
- validate against expected hash.

### Step 5 — Merge metadata  
Local canonical object:
- on-chain → always trusted,
- off-chain → trusted only if verified or user accepts warning.

---

# 4. Metadata Validation Rules

### 4.1 Required fields
- `name`
- `asset_id`
- `type`

### 4.2 Optional but recommended
- `description`
- `image`
- `content hashes`

### 4.3 Warnings for missing fields
If required metadata is missing or malformed:
- UI shows “Incomplete metadata” warning  
- Asset still usable (unless metadata defines essential logic)

### 4.4 URL safety checks
Adamantine must:
- block non-HTTPS URLs by default (except IPFS),
- check for dangerous redirects,
- warn on oversized media files.

---

# 5. Certificates / Document Metadata

For certificate-type DigiAssets:

- `subject` → required  
- `valid_from` / `valid_to` → optional  
- `reference_id` → optional but useful  

Adamantine renders a **Certificate View**:

- subject  
- issuer  
- validity  
- hash of referenced document  
- button “Verify Document Hash”  

(Requires user supplying a file or URL.)

---

# 6. NFT Metadata Display Rules

NFT view includes:

- main image (thumbnail first, full image loaded later)  
- name + description  
- edition number (if part of a set)  
- metadata hash verification status  
- link to view raw metadata  

No auto-downloading videos/audio without user tap.

---

# 7. Fungible Token Metadata

Minimal view:

- asset name  
- ticker  
- total supply (if available)  
- divisibility  
- issuer account  
- external project link  

Additional fields displayed if indexer provides richer metadata.

---

# 8. Guardian + Risk Engine Hooks

Metadata may be abused in scams (fake URLs, phishing).  
Guardian must perform:

- **URL trust check**  
- **domain reputation score**  
- **hash mismatch detection**  
- **known rogue asset lists** (from Shield Bridge if available)

If risky:
- asset marked with yellow warning,
- risky transfers may require confirmation,
- extreme cases blocked entirely.

---

# 9. Offline Mode Considerations

Adamantine must still display:

- on-chain metadata,
- cached metadata,
- cached thumbnails,
- essential certificate data,

even without internet.

External URLs become “Tap to fetch when online”.

---

# 10. Privacy Rules

Metadata fetches must:

- not leak wallet addresses,
- not include personal data,
- use privacy-friendly headers.

No third-party trackers allowed in requests.

---

Author: **DarekDGB**  
License: MIT
