# Security Policy

Adamantine Wallet OS takes security seriously and welcomes responsible disclosure
of vulnerabilities that could affect user safety.

This document explains how to report security issues, what is considered
in scope for this project, and how security architecture decisions are enforced.

---

## Security Architecture (Important)

Adamantine Wallet OS follows a **defense-in-depth Wallet OS model** built around
a **5-layer shield and Adaptive Core**. The project explicitly avoids
browser-based signing, browser seed handling, and extension-level trust.

For a clear, testable definition of what attack classes are **structurally blocked**
(including Trust Wallet–style extension attacks), see:

- **[Trust Wallet Attack Immunity Checklist](docs/security/trust-wallet-attack-immunity-checklist.md)**

This checklist defines **non-negotiable security invariants** and serves as an
architectural contract for contributors and reviewers.

---

## Reporting a Vulnerability

If you believe you have found a security vulnerability, please **do not open a public issue**.

Instead, report it responsibly using one of the following methods:

- GitHub **Private Security Advisory** (preferred)
- Direct contact with the project maintainer (if provided elsewhere)

Please include:
- A clear description of the issue
- Steps to reproduce (if applicable)
- Potential impact
- Any relevant logs, screenshots, or proofs of concept

You will receive an acknowledgment as soon as possible.

---

## Scope

The following areas are **in scope**:

- Wallet-layer logic and transaction handling
- Key custody boundaries and signing authorization flows
- Policy enforcement and Guardian confirmation mechanisms
- Adaptive Core risk evaluation and safe-halt behavior
- Failure handling and secure defaults
- Update integrity, provenance, and release verification
- Optional network intelligence integration (DQSN)

---

## Out of Scope

The following are **out of scope**:

- Blockchain consensus rules
- Cryptographic primitives or algorithms themselves
- Third-party libraries and dependencies (unless misused by this project)
- Denial-of-service attacks against public blockchains
- Social engineering attacks outside of wallet behavior
- Vulnerabilities that require violating documented security invariants
  (e.g. browser seed entry or browser signing)

---

## Disclosure Process

- Please allow reasonable time for investigation and remediation
- Coordinated disclosure is preferred over public release
- Once resolved, disclosure details may be published with attribution (if desired)

---

## Supported Versions

This project is under active development.
Only the latest version on the main branch is considered supported
for security reporting purposes.

---

## Notes

Adamantine Wallet OS prioritizes user sovereignty, safety,
and responsible handling of security research.

Security claims are based on **architecture and enforced boundaries**,
not marketing guarantees.
