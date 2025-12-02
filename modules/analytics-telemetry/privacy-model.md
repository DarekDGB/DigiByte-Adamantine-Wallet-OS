# Analytics Telemetry — Privacy Model

This document defines the privacy guarantees, data‑minimization rules, and anonymization pipelines inside the DigiByte Adamantine Wallet analytics module.

## 1. Philosophy

The analytics system is designed with **zero personal identifiers**, **no tracking**, and **no cross‑session fingerprinting**.  
All telemetry is optional and cryptographically blinded.

## 2. Data Categories

### 2.1 Allowed (Safe-by-Design)
- Node health pings  
- Feature usage counters  
- Shield-engine signal metrics  
- Anonymous error codes  

### 2.2 Forbidden
- IP address storage  
- Device fingerprints  
- Account identifiers  
- Contact lists  
- Wallet addresses  

## 3. Anonymization Pipeline

1. Raw event  
2. Local hashing (non-reversible)  
3. Noise injection  
4. Batch aggregation  
5. Zero-trust submit (optional)

## 4. Retention

- Default: **0 days** (only aggregated counters kept)  
- Developer mode: local only, never uploaded  

## 5. Compliance

Designed to be compliant with:
- GDPR  
- UK Data Protection Act  
- Global privacy-by-design standards

