# Wallet Protection Stack

This document provides a high-level view of the Adamantine Wallet protection stack,
showing what runs locally inside the wallet and what is optional network-assisted intelligence.

Key ideas:
- Enforcement happens locally (user remains in control)
- Network intelligence is optional (DQSN can be enabled or disabled)
- Learning improves protection without removing agency

---

## Wallet Protection Stack

Legend:
- Solid arrows = runtime path (what happens when a user prepares/sends a transaction)
- Dotted arrows = optional intelligence sharing (non-blocking)

```mermaid
graph TB
    User([User]) --> UI

    subgraph Device["ON-DEVICE (Adamantine Wallet)"]
        UI["Guardian Wallet<br/>UI + Policy"]
        Gate["QWG<br/>Transaction Gate"]
        Detect["Sentinel AI v2<br/>Local Detection"]
        Learn["Adaptive Core v2<br/>Local Memory + Learning"]
    end

    UI -->|Policy + Intent| Gate
    Gate -->|Signals| Detect
    Detect -->|Outcome + Evidence| Gate
    Gate -->|Risk Summary| UI

    UI --> Decision{Authorize?}
    Decision -->|Approve| Broadcast["Broadcast Transaction"]
    Decision -->|Reject| Stop["Stop / Edit Transaction"]

    subgraph Optional["OPTIONAL NETWORK INTELLIGENCE"]
        DQSN["DQSN v2<br/>Threat Intelligence Network"]
    end

    Detect -.Threat Signals.-> DQSN
    DQSN -.Aggregated Context.-> Detect

    Detect -->|Feedback| Learn
    Learn -.Model/Rule Updates.-> Detect
    Learn -.Policy Suggestions.-> UI
```

---

## Notes

- The wallet remains the enforcement point: decisions are made locally.
- DQSN is optional: protection continues to work without network access.
- The Adaptive Core improves detection and user experience over time without taking control.
