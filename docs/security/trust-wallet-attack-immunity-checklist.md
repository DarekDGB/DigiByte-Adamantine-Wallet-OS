# Trust Wallet Attack Immunity Checklist
Author: **DarekDGB**  
Scope: **DigiByte Adamantine Wallet OS** (architecture + implementation guardrails)  

> Goal: Prevent Trust Wallet–style incidents (malicious update + analytics trojans + seed/keys exposed in a browser/extension + silent signing + instant drain).
>
> This checklist turns the **5‑Layer Shield + Adaptive Core** into **testable, enforceable guarantees**.

---

## Threat model in one paragraph
Trust Wallet–style drains typically require: **(1) a web/extension distribution surface**, **(2) secrets (seed/private keys) entering that surface**, **(3) signing authority in that surface**, and increasingly **(4) telemetry/analytics code sharing the same trust boundary as secrets**.  
The immunity strategy is therefore simple and absolute:
- **Browser/UI is untrusted** (display + intent only).
- **Core is sacred** (keys + signing only).
- **Analytics is sandboxed** (never co‑resident with secrets).
- **Updates are verified** (provenance + reproducibility).
- **Risk controls can halt signing** (policy + guardian + adaptive scoring).

---

## 0) “Never again” invariants (non‑negotiables)
These are architectural laws. If any are violated, you re‑inherit Trust Wallet risk.

### I0.1 — No secrets in the browser
- ✅ Browser/web client MAY be **watch‑only** or **connect-to-core**.
- ❌ Browser/web client MUST NEVER handle **seed phrases**, **private keys**, **xprv**, **signing keys**, or **unencrypted key material**.

**Acceptance test**
- Grep/lint must fail builds if web modules contain:  
  `mnemonic|seed|bip39|xprv|private_key|signRaw|signTransaction`.

---

### I0.2 — No signing in the browser
- ✅ Browser/web client MAY create **Transaction Intent** objects.
- ❌ Browser/web client MUST NEVER sign.

**Acceptance test**
- Any signing function must exist only in Core modules with an explicit “Signer” boundary.

---

### I0.3 — Signing lives behind Policy + Guardian
- ✅ Core signs only after:
  1) **Policy Engine** approves intent  
  2) **Guardian** secures explicit user authorization  
  3) **Adaptive Core** risk score is acceptable (or requires step‑up)

---

### I0.4 — Analytics & telemetry isolation (**NEW — mandatory**)
- ❌ Analytics/telemetry MUST NEVER execute in the same trust boundary as:
  - seed generation or import
  - key storage
  - signing
- ❌ Analytics MUST NOT observe, hook, infer, or react to seed/import flows.
- ❌ Analytics MUST NOT have network access during sensitive operations.

**Required behavior**
- During seed import, wallet restore, or key generation:
  - telemetry = **hard disabled**
  - outbound network = **restricted**
- Any analytics initialization during these flows triggers **Safe Halt**.

---

### I0.5 — Fail‑closed defaults
If integrity, provenance, policy, or isolation checks fail:
- Wallet MUST **refuse to sign**
- UI MUST show **Safe Halt**

---

## 1) Map: Trust Wallet attack chain → Shield layers

### Attack A: Malicious update / supply‑chain injection
**Stops at:** Integrity / Provenance + Adaptive Core  
Controls: signed releases, SBOM, pinned dependencies  
**Result:** signing halted

---

### Attack B: Analytics trojan / hidden exfiltration
**Stops at:** Isolation + Policy + Adaptive Core  
Controls: sandboxed analytics, no telemetry during key flows  
**Result:** Safe Halt

---

### Attack C: Seed capture during import
**Stops at:** Key Isolation + Guardian  
Controls: no web seed import, core‑only key ops  
**Result:** nothing to steal

---

### Attack D: Silent signing
**Stops at:** Guardian + Policy  
Controls: explicit confirmation, no background signing  
**Result:** signing denied

---

### Attack E: UI deception
**Stops at:** Policy + Adaptive Core  
Controls: limits, delays, human‑proof confirmations  
**Result:** user warned or action blocked

---

## Appendix: One‑line proof
> “Even if the UI or analytics layer is compromised, it can only propose intents. Keys and signing live only in Core behind Policy, Guardian, and Adaptive Core, with verified updates—so the Trust Wallet drain path is structurally blocked.”
