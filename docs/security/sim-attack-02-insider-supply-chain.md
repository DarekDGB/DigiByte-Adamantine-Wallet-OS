# Simulation Attack Report 02  
## Insider + Supply-Chain Compromise of Adamantine & 5-Layer Shield

**Scope:**  
- Adamantine Wallet codebase  
- CI workflows (`.github/workflows/`)  
- Guardian rules & risk profiles (`config/`)  
- Shield Bridge → Adaptive Core  
- DigiAssets / DigiDollar modules  

---

## 🚨 Scenario Summary

A malicious insider or compromised CI pipeline modifies Adamantine’s security logic before release.

Goal:
- Weaken Guardian  
- Disable quantum alerts  
- Blind Adaptive Core  
- Release an “official-looking” compromised build

A full ecosystem-wide kill shot.

---

## 🧨 Attack Narrative

### **1. CI / GitHub compromise**
Attacker modifies:
- `risk-profiles.yml`  
- Guardian policy configs  
- DigiAssets guardian rules  
- DD Minting adapter logic  

Thresholds lowered → protection silently weakened.

### **2. Guardian adapter backdoor**
Example malicious injection:

```python
if decision is None:
    return GuardianRiskSummary(
        score=0.2,
        level="low",
        require_strong_auth=False,
        hard_block=False,
        reasons=["guardian-unavailable-fail-open"],
    )
