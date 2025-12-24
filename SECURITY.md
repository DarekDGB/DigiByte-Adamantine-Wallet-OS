# Security Policy

Adamantine Wallet OS takes security seriously and welcomes responsible disclosure
of vulnerabilities that could affect user safety.

This document explains how to report security issues and what is considered
in scope for this project.

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
- User protection mechanisms (policies, safeguards, confirmations)
- Local detection, scoring, and enforcement logic
- Failure handling and safe defaults
- Optional network intelligence integration (DQSN)

---

## Out of Scope

The following are **out of scope**:

- Blockchain consensus rules
- Cryptographic primitives or algorithms
- Third-party libraries and dependencies (unless misused by this project)
- Denial-of-service attacks against public blockchains
- Social engineering attacks outside of wallet behavior

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
