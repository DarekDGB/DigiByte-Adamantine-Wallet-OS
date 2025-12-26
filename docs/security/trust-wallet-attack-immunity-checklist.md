# Trust Wallet Attack Immunity Checklist
Author: **DarekDGB**  
Scope: **DigiByte Adamantine Wallet OS** (architecture + implementation guardrails)  

> Goal: Prevent Trust Wallet–style incidents (malicious update + seed/keys exposed in a browser/extension + silent signing + instant drain).
>
> This checklist turns the **5‑Layer Shield + Adaptive Core** into **testable, enforceable guarantees**.

---

## Threat model in one paragraph
Trust Wallet–style drains typically require: **(1) a web/extension distribution surface**, **(2) secrets (seed/private keys) entering that surface**, and/or **(3) signing authority in that surface**. The immunity strategy is therefore simple and absolute:
- **Browser/UI is untrusted** (display + intent only).
- **Core is sacred** (keys + signing only).
- **Updates are verified** (provenance + reproducibility).
- **Risk controls can halt signing** (policy + guardian + adaptive scoring).

---

## 0) “Never again” invariants (non‑negotiables)
These are architectural laws. If any are violated, you re‑inherit Trust Wallet risk.

### I0.1 — No secrets in the browser
- ✅ Browser/web client MAY be **watch‑only** or **connect-to-core**.
- ❌ Browser/web client MUST NEVER handle **seed phrases**, **private keys**, **xprv**, **signing keys**, or **unencrypted key material**.

**Acceptance test**
- Grep/lint must fail builds if web modules contain: `mnemonic|seed|bip39|xprv|private_key|signRaw|signTransaction`.

### I0.2 — No signing in the browser
- ✅ Browser/web client MAY create **Transaction Intent** objects.
- ❌ Browser/web client MUST NEVER sign.

**Acceptance test**
- Any signing function must exist only in Core modules with explicit “Signer” boundary.

### I0.3 — Signing lives behind Policy + Guardian
- ✅ Core signs only after:
  1) **Policy Engine** approves intent, and  
  2) **Guardian** secures explicit user authorization (secure surface), and  
  3) **Adaptive Core** risk score is below thresholds (or requires step‑up auth).

### I0.4 — Fail‑closed defaults
If integrity, provenance, or policy checks fail:
- Wallet MUST **refuse to sign**.
- UI MUST show “Safe Halt” status (not “try again”).

---

## 1) Map: Trust Wallet attack chain → Shield layers
Use this table to prove where an attack stops.

### Attack step A: Malicious update / supply‑chain injection
**Stops at:** Layer 1 (Integrity/Provenance) + Layer 5 (Adaptive Core “Safe Halt”)

Controls:
- Signed releases (client + core artifacts)
- Verified update channel
- Dependency hash pinning + lockfiles
- SBOM + vulnerability scans
- Reproducible builds (deterministic)

**Stop condition**
- If signature invalid or provenance missing → app halts signing.

### Attack step B: Seed capture during import
**Stops at:** Layer 2 (Key Isolation) + Layer 3 (Guardian)

Controls:
- No seed import in web UI
- Key ops only in Core, inside OS secure storage / enclave where possible
- Secure import modes (offline/QR/hardware assisted)

**Stop condition**
- Seed never enters compromised surface → nothing to steal.

### Attack step C: Silent signing / background drain
**Stops at:** Layer 3 (Guardian) + Layer 4 (Policy) + Layer 5 (Adaptive Core)

Controls:
- Intent→Policy→Guardian→Sign pipeline
- No background signing APIs
- Mandatory user confirmation screen for any spend/approval

**Stop condition**
- Without Guardian approval, Core refuses to sign.

### Attack step D: UI deception / phishing prompts
**Stops at:** Layer 4 (Policy) + Layer 5 (Adaptive Core)

Controls:
- Whitelists, spend limits, cooling periods
- New-address high-value step-up
- Unlimited approval detection
- Clear human-proof confirmations (address chunks + checksums)

**Stop condition**
- Risk score triggers step-up or timed delay; user sees explicit warnings.

---

## 2) Implementation checklist (make it real)

### 2.1 Release & provenance hardening (Supply chain)
**Must-have**
- [ ] Signed Git tags for releases  
- [ ] Signed release artifacts (APK/IPA/desktop binaries)  
- [ ] Build provenance (e.g., SLSA-style attestations)  
- [ ] SBOM generated per build  
- [ ] Dependency lockfiles (pinned versions)  
- [ ] Hash pinning for critical dependencies  
- [ ] CI gate: block merges if vulnerabilities exceed threshold  
- [ ] “Two-person rule” for releasing (2 approvals + CI green)

**Nice-to-have**
- [ ] Reproducible builds with public verification steps  
- [ ] Separate signing keys per platform + rotation plan

### 2.2 Key custody & storage (Keys never leak)
**Must-have**
- [ ] Private keys stored only in Core trust boundary  
- [ ] Prefer OS KeyStore / Secure Enclave where possible  
- [ ] Encrypted at rest with modern KDF (Argon2id/scrypt) + strong params  
- [ ] Zeroization of sensitive buffers where applicable  
- [ ] No logging of secrets (unit tests enforce this)

**Nice-to-have**
- [ ] Shamir / split backup (“ultra mode”)  
- [ ] Hardware wallet integration for high-value accounts

### 2.3 Transaction pipeline (Intent → Policy → Guardian → Sign)
**Must-have**
- [ ] Transaction Intent schema (chain, to, amount, fee, memo, asset, approvals)  
- [ ] Policy engine runs BEFORE any signing  
- [ ] Guardian confirmation is mandatory for spends/approvals  
- [ ] Core signer refuses unsigned policy/guardian tokens  
- [ ] Deterministic transaction preview shown to the user (no ambiguity)

**Nice-to-have**
- [ ] Pluggable policy sets (Normal / Strict / Paranoid modes)

### 2.4 Adaptive Core risk engine (the “smarter” part)
**Must-have**
- [ ] Local, privacy-preserving anomaly scoring  
- [ ] High-risk conditions require step-up or delay:
  - new address + large spend
  - fee spikes
  - “unlimited approvals”
  - sudden chain/network switches
- [ ] “Panic Lock” that disables signing instantly  
- [ ] Cooldown / time-lock option for large transfers  
- [ ] Daily spend limits + per-asset thresholds

**Nice-to-have**
- [ ] Optional second factor for high-risk signing (passkey / hardware prompt)

### 2.5 UI hardening (assume UI can be hostile)
**Must-have**
- [ ] UI never receives private keys  
- [ ] UI never signs  
- [ ] UI cannot bypass policy checks  
- [ ] Confirmations are rendered by Guardian secure surface (not normal web view)  
- [ ] Address display uses checksum + chunking; warns on lookalikes

**Nice-to-have**
- [ ] Anti-screenshot for sensitive confirmation surfaces (platform dependent)

---

## 3) Verification suite (prove immunity)
These tests are what let you confidently say: “Not TrustWallet‑class vulnerable.”

### 3.1 Static checks (CI)
- [ ] Secret-handling forbidden in web packages (regex + AST scanning)
- [ ] Signing APIs forbidden outside Core boundary
- [ ] Dependency audit + SBOM generation
- [ ] Lint: no secrets in logs / exceptions / traces

### 3.2 Dynamic checks
- [ ] “Compromised UI simulation” tests:
  - UI tries to sign directly → must fail
  - UI crafts malicious intent → policy must reject or require step-up
- [ ] “Update tamper” test:
  - modified artifact without valid signature → must refuse install/run

### 3.3 Threat regression tests
- [ ] Add a regression test for every incident you learn from (like this Trust Wallet case)

---

## 4) Operational playbook (when an incident happens elsewhere)
When the ecosystem gets hit again:
1) Extract the attack chain (A→B→C…).
2) Map each step to Shield layers.
3) Add/adjust controls.
4) Add regression tests.
5) Document changes in `SECURITY_NOTES.md`.

---

## 5) Communication rule (protect yourself legally + reputationally)
Use careful wording publicly:
- Prefer: “Designed to *reduce* browser/extension risks via isolation.”
- Avoid absolute guarantees like “unhackable.”
- Always distinguish: **architecture** vs **implementation maturity**.

MIT license covers code reuse, but it does not make security claims for you.

---

## Appendix: One-line elevator proof
> “Even if the UI is compromised, it can only propose intents. Keys and signing live only in Core behind Policy + Guardian + Adaptive Core, and updates are verified by signature—so the Trust Wallet drain path is structurally blocked.”

