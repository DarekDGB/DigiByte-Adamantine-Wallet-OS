# Digi-Mobile Integration (Android)

Adamantine Wallet supports multiple DigiByte node backends.  
On Android, the wallet can run in **local full-node mode** thanks to integration with **Digi-Mobile**, a pruned and mobile-friendly DigiByte Core build.

---

## Overview

Digi-Mobile provides:

- A fully validated DigiByte Core daemon  
- Pruned mode suitable for mobile storage  
- Standard JSON-RPC interface on `127.0.0.1:<port>`  
- An Android wrapper for managing the local node lifecycle  

Adamantine detects this local daemon and prioritizes it over remote nodes.

---

## Architecture

When Digi-Mobile is active:

```
Android Device
┌────────────────────────────┐
│  Digi-Mobile (local node)  │  ← Pruned DigiByte Core
└───────────────┬────────────┘
                │ JSON-RPC
┌───────────────▼────────────┐
│    Adamantine Wallet        │
│  (Guardian + Shield Stack)  │
└─────────────────────────────┘
```

### Benefits

- Trustless validation  
- No external RPC leaks  
- No reliance on third-party nodes  
- Better privacy, reliability, and security  
- Shield and Guardian rules operate on *local* chain data

---

## Fallback Strategy

If Digi-Mobile is not reachable:

1. Adamantine checks remote nodes from `config/example-nodes.yml`.
2. Node priority rules determine the best available backend.
3. The wallet remains fully functional — only decentralization mode changes.

---

## Why This Matters

Digi-Mobile brings DigiByte Core into the mobile world.  
Adamantine turns it into a **secure, intelligent, multi-layer digital fortress** on Android.

Together they provide:

- Local full-node validation  
- Quantum-aware shielding  
- Guardian rule enforcement  
- Full DigiAssets and DigiDollar support  
- Enigmatic Layer-0 messaging  
- True end-to-end on-device sovereignty  

This makes Android one of the strongest possible environments for the DigiByte ecosystem.
