# Simulation Attack Report 02  
## Insider + Supply-Chain Compromise of Adamantine & 5-Layer Shield

Scope:
- Adamantine Wallet codebase  
- CI workflows (.github/workflows/)  
- Guardian rules & risk profiles (config/)  
- Shield Bridge → Adaptive Core  
- DigiAssets / DigiDollar modules  

---

Scenario Summary

A malicious insider or compromised CI pipeline silently modifies Adamantine’s security logic before release.

Attacker goals:
- Weaken Guardian  
- Disable QWG quantum alerts  
- Blind Adaptive Core  
- Ship a legitimate-looking compromised build  

This is the most catastrophic attack vector because it affects every user at scale.

---

Attack Narrative

1. CI / GitHub compromise  
Attacker gains access to CI or GitHub and edits critical security files:
- config/risk-profiles.yml  
- Guardian rule definitions  
- DigiAssets Guardian hooks  
- DigiDollar Guardian adapter  

Small edits cause massive vulnerabilities:
- Thresholds lowered  
- Escalations disabled  
- High-risk behaviours downgraded  
- Quantum alerts muted  

2. Guardian adapter backdoor  
Attacker inserts a silent bypass by adding logic equivalent to:

    if decision is None:
        return GuardianRiskSummary(score=0.2, level="low", require_strong_auth=False, hard_block=False, reasons=["guardian-unavailable-fail-open"])

Meaning:
If Guardian fails for ANY reason → automatically approve.
Guardian is neutralized.

3. QWG neutralized  
Attacker disables quantum escalation with logic similar to:

    if inputs.quantum_alert:
        pass  # intentionally ignored

Quantum downgrade attacks and PQC failures are completely ignored.

4. Telemetry blinding  
Attacker removes high-risk events from telemetry.  
Adaptive Core becomes:
- Blind  
- Deaf  
- Unable to detect coordinated attacks  
- Unable to learn patterns  

5. Shipping the compromised build  
The final build:
- Looks normal  
- Passes CI  
- Claims “Quantum secure”  

But internally:
- Guardian bypassed  
- QWG disabled  
- Risk Engine misled  
- Adaptive Core starved  

---

Layers Engaged

- Adamantine Core: source compromised  
- Guardian Wallet: bypassed  
- Risk Engine: manipulated signals  
- QWG: ineffective  
- Shield Bridge: reduced telemetry  
- Adaptive Core: blind to attacks  

---

Brutal Findings

1. Supply-chain compromise = total system collapse  
2. One malicious line can destroy the entire shield  
3. Telemetry tampering hides all attacks from Adaptive Core  
4. CI pipelines are the most dangerous attack surface  

---

Testnet Training Recommendations

1. Simulate insider attacks
   - Lower thresholds  
   - Disable Guardian  
   - Mute quantum alerts  
   CI must reject these changes.

2. Signed configuration bundles  
   config/ must be immutable and cryptographically signed.  
   Wallet must refuse startup on tampering.

3. Telemetry integrity checks  
   Adaptive Core must receive every high-risk, Guardian-block, and QWG anomaly event.  
   Missing events = failure.

4. Mandatory fail-closed behaviour  
   - Guardian unreachable → hard block  
   - QWG anomaly → no fallback  
   - Config mismatch → lockdown mode  

---

Objective  
Ensure no insider, CI compromise, or subtle code edit can silently weaken Adamantine or the 5-Layer Quantum Shield before releasing the mainnet wallet build.
