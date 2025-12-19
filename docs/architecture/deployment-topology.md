# Deployment Topology

This document describes how Adamantine components are deployed,
what runs locally on the user device, and what is optional network-assisted
infrastructure.

Key ideas:
- Core protection works fully offline
- Network components are optional and non-authoritative
- No single point of failure or mandatory server dependency

---

## Deployment Topology

Legend:
- Solid boxes = on-device components
- Dashed boxes = optional network components
- Solid arrows = runtime interaction
- Dotted arrows = optional intelligence exchange

```mermaid
graph TB
    %% =========================
    %% USER DEVICE
    %% =========================
    subgraph Device["USER DEVICE (Mobile / Desktop)"]
        UI["Guardian Wallet<br/>UI + Policy"]
        Gate["QWG<br/>Transaction Gate"]
        Detect["Sentinel AI v2<br/>Local Detection"]
        Learn["Adaptive Core v2<br/>Local Memory"]
        Node["Optional Local Node<br/>(SPV / Full)"]
    end

    UI --> Gate
    Gate --> Detect
    Detect --> Gate
    Gate --> UI

    Detect --> Learn
    Learn -.Updates.-> Detect
    Learn -.Suggestions.-> UI

    Gate -->|Approved Tx| Node

    %% =========================
    %% BLOCKCHAIN NETWORK
    %% =========================
    subgraph Chain["BLOCKCHAIN NETWORK"]
        Net["DigiByte Network<br/>Consensus Nodes"]
    end

    Node --> Net

    %% =========================
    %% OPTIONAL INTELLIGENCE
    %% =========================
    subgraph Optional["OPTIONAL NETWORK SERVICES"]
        DQSN["DQSN v2<br/>Threat Intelligence"]
        Update["Model / Rule Feeds<br/>(Signed, Versioned)"]
    end

    Detect -.Anonymized Signals.-> DQSN
    DQSN -.Aggregated Context.-> Detect

    Update -.Verified Updates.-> Learn

    %% =========================
    %% STYLING
    %% =========================
    style Device fill:#E8F4F8,stroke:#999
    style Optional fill:#F4E8F8,stroke:#999
    style Chain fill:#EEEEEE,stroke:#999
```

---

## Offline Behavior

When the device is offline:
- Transactions can still be prepared and reviewed
- Local detection and policy enforcement remain active
- Network intelligence is skipped without failure

---

## Trust Boundaries

- Private keys never leave the user device
- Network intelligence cannot authorize transactions
- Updates are optional and cryptographically verified

---

## Notes

This topology is designed to scale from mobile wallets
to advanced users running local nodes,
without changing the trust model.
