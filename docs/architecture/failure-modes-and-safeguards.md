# Failure Modes and Safeguards

This document describes how the Adamantine Wallet behaves under failure,
uncertainty, or degraded conditions, and what safeguards are applied to
protect the user.

Key ideas:
- Fail-safe defaults
- Graceful degradation
- User remains the final authority
- No single point of failure

---

## Failure Modes and Safeguards

Legend:
- Solid arrows = runtime behavior
- Dashed arrows = fallback paths
- Red boxes = failure conditions
- Green boxes = safeguards

```mermaid
graph TB
    User([User]) --> UI["Guardian Wallet<br/>UI + Policy"]

    UI --> Gate["QWG<br/>Transaction Gate"]

    Gate --> Detect["Sentinel AI v2<br/>Detection"]

    %% =========================
    %% FAILURE CONDITIONS
    %% =========================
    Detect -->|Normal| Assess["Risk Assessment"]
    Detect -->|Failure| FailDetect["Detection Failure<br/>(Crash / Timeout)"]

    Assess -->|Low Risk| Proceed["Proceed"]
    Assess -->|Uncertain| Uncertain["Uncertain Risk"]
    Assess -->|High Risk| HighRisk["High Risk"]

    %% =========================
    %% SAFEGUARDS
    %% =========================
    FailDetect --> SafeBlock["Fail-Safe Block"]
    Uncertain --> Challenge["Require User Confirmation"]
    HighRisk --> Block["Block Transaction"]

    Proceed --> UI
    Challenge --> UI
    Block --> UI
    SafeBlock --> UI

    UI --> Decision{Authorize?}
    Decision -->|Approve| Broadcast["Prepare / Broadcast Transaction"]
    Decision -->|Reject| Stop["Stop / Edit Transaction"]

    %% =========================
    %% NETWORK FAILURE
    %% =========================
    subgraph NetworkFailure["Network / Intelligence Failure"]
        NetDown["DQSN Unavailable<br/>Offline / Timeout"]
    end

    NetDown -.Fallback.-> Detect

    %% =========================
    %% STYLING
    %% =========================
    style FailDetect fill:#FDEDEC,stroke:#C0392B
    style HighRisk fill:#FDEDEC,stroke:#C0392B
    style SafeBlock fill:#E8F8F5,stroke:#27AE60
    style Challenge fill:#FCF3CF,stroke:#F1C40F
```

---

## Safeguard Principles

- When in doubt, slow down.
- When uncertain, ask the user.
- When failing, block safely.
- When offline, continue locally.

---

## Notes

These safeguards ensure that even under degraded conditions,
the wallet never acts autonomously or unsafely.
