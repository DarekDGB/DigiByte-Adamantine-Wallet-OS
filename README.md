# 🚀 DigiByte Adamantine Wallet  
### *Next‑Generation Quantum‑Secure Wallet & 5‑Layer Defense Architecture*  
**By @Darek_DGB — MIT Licensed**

---

# 🛡️ What Is Adamantine?

The **DigiByte Adamantine Wallet** is the first wallet designed as a complete  
**multi‑layer defensive system**, integrating:

- **Sentinel AI v2** — mempool anomaly detection  
- **DQSN v2** — network safety & multi‑node confirmation  
- **ADN v2** — autonomous defense node (lockdown engine)  
- **QWG** — Quantum Wallet Guard (key posture + PQC migration)  
- **Adaptive Core** — behavior‑based immune system  
- **Guardian Wallet** — rule & policy engine  
- **Shield Bridge** — risk aggregation & cross‑layer coordination  
- **DigiAssets Engine** — minting, transfers, parsing & indexing  
- **DigiDollar (DD) minting engine**  
- **Enigmatic Chat** — Layer‑0 messaging protocol  
- **Clients** — Android / iOS / Web skeletons

Adamantine is not “a wallet.”  
It is a **security operating system** for DigiByte.

---

# 🌍 Vision

To create the most secure, self‑healing, multi‑asset wallet ever built for DigiByte —  
designed for everyday users *and* for future quantum‑threat environments.

---

# 🔗 Node Connectivity (RPC + DigiMobile / Enigmatic)

Adamantine includes a flexible node‑connection layer inside:

```
core/node/
  rpc_client.py
  node_client.py
  node_manager.py
  health.py
```

This layer provides:

### ✔ Standard DigiByte Node Connectivity  
Supports full RPC for:
- block fetch  
- mempool state  
- tx broadcast  
- node health checks  
- reorg awareness  
- peer analysis  

### ✔ Lightweight Node Mode — Compatible With JohnnyLaw’s **DigiMobile**  
Adamantine can operate using a lightweight node backend such as  
**DigiMobile**, because:

- `node_client` does not require full RPC  
- works with partial RPC, proxy APIs, or custom endpoints  
- Enigmatic Layer‑0 signals integrate directly into Guardian + Shield Bridge  

DigiMobile integration is achieved through:

- pluggable node adapters  
- fallback RPC modes  
- Enigmatic transaction‑plane communication  

### ✔ Why This Matters

Users will be able to run Adamantine:

- with a **full node**  
- with a **remote node**  
- with **DigiMobile lightweight node**  
- or hybrid mode: DigiMobile (messaging) + RPC (confirmations)

This makes Adamantine extremely flexible and ideal for mobile devices.

---

# 🛠️ Developer Quickstart

This repository contains the full **v0.2 architecture + runtime skeleton**, including:

- 5-layer Quantum Shield  
- Guardian Wallet policy engine  
- Shield Bridge runtime  
- DigiAssets engine + schemas  
- DD minting  
- Enigmatic integration  
- Node RPC & safety layer  
- Adaptive Core  
- 65 passing tests  
- Full CI stack (Android/iOS/Web/Python)

---

## 📌 Project Status — v0.2 Complete

| Component | Status |
|----------|--------|
| Architecture | ✅ Complete |
| Runtime Skeleton | ✅ Done |
| Shield Bridge | ✅ v0.2 implemented |
| Guardian Engine | ✅ Skeleton done |
| DigiAssets Spec | ✅ Full |
| QWG (Quantum Guard) | ✅ Spec done |
| DD Minting | ✅ Implemented |
| Node Glue | ✅ Implemented |
| Tests | ✅ 65 passing |
| CI | ✅ All green |
| Next Phase | v0.3 Implementation |

The project is **ready for DigiByte Core developer onboarding**.

---

# 📁 Repository Structure

```
core/
  adaptive-core/
  digiassets/
  guardian-wallet/
  node/
  pqc-containers/
  qwg/
  risk-engine/
  shield-bridge/
modules/
  dd-minting/
  digiassets/
  enigmatic-chat/
clients/
  android/
  ios/
  web/
docs/
tests/
.github/
```

Each subsystem is fully documented in `docs/` with API files for Sentinel, DQSN, ADN, QWG, Adaptive Core & Shield Bridge.

---

# ▶️ Running Tests

Requirement: **Python 3.11**

```bash
git clone https://github.com/.../DigiByte-Adamantine-Wallet.git
cd DigiByte-Adamantine-Wallet

python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# or .venv\Scripts\activate  # Windows

pip install -r requirements.txt   # if provided
pytest -q
```

Expected:

```
65 passed in X.XXs
```

---

# 🧱 Architecture Layers — Summary

### **1. Sentinel AI v2**  
Mempool, topology & fee‑plane analysis.

### **2. DQSN v2**  
Network disagreement, multi‑node confirmation, reorg signals.

### **3. ADN v2**  
Node reflex + lockdown engine.

### **4. QWG**  
Quantum Wallet Guard (PQC posture & signing protection).

### **5. Adaptive Core**  
Behavioral immune system (learning stability index).

### **6. Guardian Wallet**  
Rule-based policy engine (approve, deny, challenge flows).

### **7. Shield Bridge**  
RiskPacket → Layer evaluations → aggregated RiskMap.

### **8. DigiAssets Engine**  
Minting, burning, validation, indexing & metadata safety rules.

### **9. Enigmatic (Layer‑0 Messaging)**  
DigiByte transaction topology as messaging channels.

---

# 🔒 Security Model

Adamantine’s layered model:

- isolates risk  
- detects anomalies early  
- aggregates multiple perspectives  
- integrates node safety + mempool safety + PQC posture + behavior models  
- produces deterministic Guardian decisions  

This creates a **digital immune system**.

---

# 📜 Roadmap (v0.2 → v0.3)

See full roadmap at:

```
docs/roadmap.md
```

Current status:

- v0.2 fully completed  
- v0.3 scheduled to implement live adapters + UI clients  
- future versions to expand cross-layer intelligence  

---

# 🤝 Contributing

1. Follow naming standards:  
   - `snake_case` for Python  
   - `kebab-case` for documentation  

2. New features must include tests.  
3. Update relevant docs before submitting PRs.  
4. Keep CI green.  
5. Maintain MIT-compatible contributions.

---

# 🙏 Credits & Intent

Built with discipline, vision, and faith.  
For DigiByte, for security, for the future.

**Glory to God.**  
**Created by @Darek_DGB.**
