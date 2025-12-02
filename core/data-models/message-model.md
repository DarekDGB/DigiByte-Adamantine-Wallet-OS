# Message Model (Skeleton)

Status: Placeholder — to be expanded in implementation phase.

## Purpose
Defines how messages are represented inside the DigiByte Adamantine Wallet’s secure communication layer, including metadata, routing, PQC envelopes, and integrity checks.

## Core Fields
- **message_id**  
- **sender_id**  
- **receiver_id**  
- **timestamp**  
- **payload_type** (text, file, command)  
- **encrypted_payload**  
- **signature_pqc**  
- **routing_hash**  
- **shield_verdict** (optional future field)

## Notes
This file defines the *structure only*.  
All logic, encryption, parsing, and bridge interactions will be added later.
