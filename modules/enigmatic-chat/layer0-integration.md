# Enigmatic Layer‑0 Integration (layer0-integration.md)

Status: **draft v0.1 – internal skeleton**

This document defines how the Adamantine Wallet integrates **Enigmatic’s Layer‑0 communication protocol** directly into DigiByte’s UTXO, fee, cardinality, topology, and block‑placement planes.

The goal is to make Adamantine the **first wallet in the world that can read, interpret, plan, and broadcast Enigmatic dialects natively**.

---

# 1. Purpose

Enigmatic is not a chat system.  
It is a **Layer‑0 intent channel** embedded inside DigiByte transactions using:

- **Value plane**  
- **Fee plane**  
- **Cardinality plane**  
- **Topology plane**  
- **Block‑placement plane**  
- **Optional metadata plane (OP_RETURN)**  

Adamantine needs to:

1. Observe on‑chain Enigmatic frames  
2. Decode state vectors  
3. Interpret dialect symbols  
4. Display them in a human‑readable form  
5. Build & broadcast Enigmatic messages (dry‑run → Guardian → send)  
6. Interface with Johnny’s Python reference stack when available  

---

# 2. Architecture Overview

Adamantine uses three subsystems for Layer‑0 Enigmatic:

### **2.1 Decoder**
Reads UTXOs and transactions → produces:

```ts
DecodedStateVector {
  txid: string
  planes: {
    value: number[]
    fee: number
    cardinality: { inputs: number, outputs: number }
    topology: string[]
    block_delta: number
    metadata?: string
  }
  dialect_symbol?: string
  confidence: number
}
```

### **2.2 Planner**
Prepares a state vector without broadcasting:

```ts
PlannedVector {
  target_symbol: string
  required_utxos: string[]
  draft_tx_hex: string
  preview_vector: DecodedStateVector
}
```

### **2.3 Executor**
When Guardian approves, planner's TX can be broadcast.

---

# 3. Wallet → Enigmatic Integration Points

### **3.1 Inbox (On‑Chain Observation)**
Adamantine periodically watches:

- new blocks  
- local UTXO changes  
- mempool (optional)  

Decoded Enigmatic signals appear in a UI panel:

```
Shield → Enigmatic Plane View
```

Example entries:

- HEARTBEAT (symbol)
- digidollar_steady (DD dialect)
- halving_cycle
- custom intel symbol

---

# 4. Outgoing Layer‑0 Enigmatic Messages

Flow:

1. User opens:
   ```
   Wallet → Enigmatic → Send Signal
   ```
2. Selects dialect + symbol
3. Adamantine calls planner → produces `PlannedVector`
4. Guardian evaluates:
   - UTXO pattern safety  
   - topology risks  
   - transaction fees  
   - shield overlays  
5. If allowed → show broadcast preview  
6. User taps **Send**

This mirrors:
```
enigmatic-dgb plan-symbol
enigmatic-dgb send-symbol
```

---

# 5. Guardian Integration

Every Layer‑0 message is treated as a **high-sensitivity action**.

Guardian evaluates:

- unusual cardinality  
- suspicious fee patterns  
- topology anomalies  
- timing patterns  
- shield warnings (Sentinel / DQSN / ADN / Adaptive Core)

Verdicts:

- allow  
- require-local-confirmation  
- require-biometric  
- delay-and-retry  
- block-and-alert  

---

# 6. Dialect Management

Adamantine loads dialect definitions from:

```
dialects/
   heartbeat.yaml
   intel.yaml
   digidollar_steady.yaml
   showcase.yaml
```

(These will be added later.)

UI shows:

```
[ Dialect: heartbeat ]
Symbols:
   - HEARTBEAT
   - RIPPLE
   - BURST
```

---

# 7. UI Surfaces in Adamantine

### **7.1 Enigmatic Dashboard**
- Latest decoded signals  
- Active dialects  
- Confidence badges  
- On‑chain vs off‑chain modes  

### **7.2 Decode Viewer**
Shows a single transaction’s planes:

```
Value Plane: [21.21, 7.00]
Fee Plane: 0.21 cadence
Cardinality: 21-in / 21-out
Topology: mirrored swarm
Block Δ: 3
Metadata: none
Symbol Decoded: HEARTBEAT
```

### **7.3 Planner Preview**
Shows draft state vector before broadcast.

---

# 8. Adaptive Core Integration

Adaptive Core learns:

- frequency of Layer‑0 signals  
- expected plane patterns  
- anomalous dialect deviations  
- chain noise fingerprints  
- potential misuse (covert channels)

Adaptive overlays influence Guardian risk scoring for future sends.

---

# 9. API Surface (Simplified)

```ts
interface EnigmaticLayer0 {
  decodeTx(tx_hex: string): DecodedStateVector
  decodeBlock(block_hash: string): DecodedStateVector[]

  planSymbol(symbol: string): PlannedVector
  planChain(symbols: string[]): PlannedVector[]

  broadcastPlanned(planned: PlannedVector): { txid: string }
}
```

Backend implementation may call Johnny’s Python stack over local RPC.

---

# 10. Future Extensions

- Full visual plane inspector  
- Dialect‑builder UI for advanced users  
- P2P Enigmatic relays  
- Layer‑0 secure group channels  
- PQC‑strengthened state-plane signatures  

---

# 11. License
MIT — Author: DarekDGB
