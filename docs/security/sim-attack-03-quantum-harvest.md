# Simulation Attack Report 03  
## Quantum-Harvest & PQC Downgrade Attack on Adamantine + Shield + Adaptive Core

Scope:
- PQC Containers (core/pqc-containers/)  
- Node Manager (core/node_manager.py)  
- QWG (Quantum Wallet Guard)  
- Risk Engine (core/risk-engine/)  
- Guardian Wallet  
- Shield Bridge → Adaptive Core  

---

Scenario Summary

A well-funded attacker collects classical DigiByte signatures and addresses TODAY and stores them until Q-Day.  
This is the “harvest now, decrypt later” model.

Attacker goals:
- Force Adamantine into classical fallback  
- Prevent or delay PQC migration  
- Maximize exposure of classical signatures  
- Break wallets instantly when quantum attacks become real  

---

Attack Narrative

1. Harvest-now phase  
The attacker operates many honest-looking DigiByte nodes and silently logs:
- All classical signatures  
- All scriptPubKeys  
- Address reuse patterns  
- DigiAssets and DigiDollar related metadata  
- Timing correlations and spending habits  

Every classical signature recorded today becomes a future vulnerability.

2. PQC rollout confusion  
Adamantine introduces PQC containers, but:
- Some users stay on classical keys  
- Some nodes do not support PQC  
- Wallet may allow fallback for convenience  

The attacker exploits this by forcing PQC negotiation failures so the wallet silently signs with classical keys.

3. PQC downgrade attack  
Attacker injects MITM or network-level manipulation causing PQC handshake failure.  
Wallet code that allows:
- “Fallback to classical mode”  
- “Graceful downgrade”  
- “Mixed mode”  

becomes a fatal weakness.

User thinks they are quantum-safe.  
Wallet appears normal.  
Transactions are actually classical.  
Attacker stores all signatures for future quantum cracking.

4. QWG neutralized  
If the Risk Engine or Guardian ignores quantum-related warnings, QWG cannot enforce protections.

Example logic failure pattern:

    if inputs.quantum_alert:
        continue  # effectively ignored

Quantum downgrade attacks and signature anomalies produce no escalation.

5. Q-Day  
Once quantum computers reach the necessary threshold, the attacker:
- Feeds years of harvested data into quantum solvers  
- Reconstructs private keys  
- Drains UTXOs immediately  
- Front-runs user attempts to move funds  
- Executes chain-level attacks faster than blocks can confirm  

Any user who ever fell back to classical mode becomes compromised instantly.

---

Layers Engaged

- PQC Containers: determines whether addresses and signatures are quantum-safe  
- Node Manager: determines which nodes are trusted and how PQC negotiation happens  
- QWG: detects downgrade attempts and suspicious patterns  
- Risk Engine: decides if downgrade triggers high-risk classification  
- Guardian Wallet: can enforce mandatory PQC after a certain block height  
- Adaptive Core: learns downgrade patterns across the network  

---

Brutal Findings

1. If PQC is optional, users die optional deaths.  
2. Downgrade attacks are far easier than breaking PQC itself.  
3. QWG warnings are useless if the wallet ignores them.  
4. Address reuse becomes catastrophic under PQC migration.  
5. Harvest-now attacks cannot be undone; once data is harvested, it is forever vulnerable.

---

Testnet Training Recommendations

1. Simulate mass PQC handshake failures  
On testnet:
- Cause PQC negotiation failures on purpose  
- Ensure wallet does NOT silently fall back  
- Require explicit user override or hard-block  

2. Mandatory PQC policies  
Guardian should enforce:
- No classical sends after testnet block X  
- Automatic “Move to PQC outputs now” flows  

3. Adaptive Core quantum anomaly training  
Train on patterns such as:
- Nodes that consistently cause PQC failures  
- Repeated downgrade attempts  
- IP clusters sending mixed-mode attacks  

Adaptive Core should:
- Mark nodes as hostile  
- Recommend quarantine  
- Adjust global threat signatures  

4. Quantum posture metrics in Risk Engine  
Risk Engine must classify:
- 0% PQC = high risk  
- Mixed = medium risk  
- Fully PQC = low risk  

Wallet should encourage migration automatically.

---

Objective

Ensure Adamantine does NOT allow downgrade attacks that expose users to future quantum breakage.  
When Q-Day arrives, DigiByte users must already be migrated, trained, and protected — not harvested victims.
