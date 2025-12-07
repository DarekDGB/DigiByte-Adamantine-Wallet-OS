# 🧪 DigiAssets Test Plan — DigiByte Adamantine Wallet

Status: **v0.2 – reference test strategy**  
Scope: **`modules/digiassets` + `core/digiassets` + Guardian / Shield Bridge integration**  

This document describes how tests around the DigiAssets engine are structured
and how DigiByte Core / wallet developers can extend them.

The goal is to keep DigiAssets behaviour **predictable, safe and transparent**
across all layers:

- parsing and validation of DigiAssets flows
- engine + indexer correctness
- Guardian integration (rules + adapter)
- Shield Bridge + Risk Engine expectations

---

## 1. Test Files & Layout

All DigiAssets‑focused tests live under:

- `tests/test_digiassets_engine.py`  
- `tests/test_digiassets_indexer.py`  
- `tests/test_digiassets_parser.py`  
- (this document) `tests/digiassets-tests.md`

Supporting code and docs:

- `core/digiassets/engine.py`  
- `core/digiassets/indexer.py`  
- `core/digiassets/tx_parser.py`  
- `core/digiassets/minting_rules.py`  
- `core/digiassets/models.py`  
- `modules/digiassets/engine.py`  
- `modules/digiassets/guardian_bridge.py`  
- `modules/digiassets/guardian-rules.md`  
- `modules/digiassets/spec.md`

The intention is simple:

> **Every behaviour described in the DigiAssets spec should be backed by at
> least one test case in this suite.**

---

## 2. Engine Tests — `test_digiassets_engine.py`

These tests exercise the **high‑level DigiAssets engine API**.  
Typical expectations:

1. **Basic asset registration**
   - Given a minimal mint transaction, the engine builds a consistent
     in‑memory representation of the asset (id, supply, issuer, metadata
     pointer).
   - The engine does not allow negative or zero supply.

2. **Transfer semantics**
   - Transfers cannot move more asset units than the source UTXO / balance.
   - Burning is explicit and cannot be triggered accidentally by malformed
     metadata.

3. **Idempotency & determinism**
   - Re‑processing the same chain segment produces identical engine state.
   - Engine reactions to malformed inputs are stable across runs (same
     exceptions or error codes).

4. **Guardian integration hooks**
   - For every operation that touches user funds (mint / burn / transfer),
     the engine exposes enough context to build a `RiskPacket` for Guardian
     / Shield Bridge (amounts, addresses, asset id, metadata size).

When adding new engine features, extend this file with focussed tests that
verify the public behaviour — not the internal implementation details.

---

## 3. Indexer Tests — `test_digiassets_indexer.py`

Tests around `core/digiassets/indexer.py` focus on **chain‑to‑engine
synchronisation**:

1. **Block / transaction scanning**
   - Indexer recognises DigiAssets‑bearing transactions according to the
     encoding rules in `spec.md`.
   - Non‑asset transactions are ignored without throwing.

2. **Reorg handling**
   - Simulated short reorgs cause the indexer to rollback and re‑apply the
     affected range without corrupting asset state.
   - Engine receives a consistent view of the final main chain.

3. **Pagination / performance envelopes**
   - Indexer can walk ranges of block heights without leaking state between
     runs (suitable for cron‑like jobs).
   - Large ranges are processed incrementally, with clear checkpoints
     for external orchestration.

4. **Error isolation**
   - Individual bad transactions do not stop the whole indexing loop; they
     are reported as structured errors for logging and further analysis.

These tests ensure that DigiAssets behaviour stays correct even under
typical main‑chain stress (reorgs, spam, large volumes).

---

## 4. Parsing & Validation Tests — `test_digiassets_parser.py`

These tests focus on the **transaction‑level view** of DigiAssets data,
without the full engine and indexer context.

Typical coverage:

1. **Metadata decoding**
   - Valid DigiAssets metadata is decoded into a structured object with
     clear fields (version, type, asset id, amounts, optional fields).
   - Oversized, truncated or malformed payloads are rejected with
     deterministic errors.

2. **Operation classification**
   - The parser recognises operation types (MINT, BURN, TRANSFER, UPDATE,
     CUSTOM) and exposes them for the engine and Guardian.
   - Unknown operation types are surfaced as "unknown" / "unsupported"
     without crashing.

3. **Safety checks**
   - Parsing never trusts external input for direct execution decisions.
   - Every parsing failure is explicit and testable; no silent fall‑through
     paths.

These tests are the first line of defence against malformed DigiAssets
transactions reaching the higher layers.

---

## 5. Guardian + Shield Bridge Expectations

While most Guardian logic is exercised in `tests/test_guardian_engine.py`
and risk‑engine tests, DigiAssets‑specific expectations are documented here
for core developers:

1. **RiskPacket mapping**
   - For DigiAssets flows, Guardian must be able to construct a
     `RiskPacket` that includes:
       - `flow_type` (e.g. `"ASSET_MINT"`, `"ASSET_TRANSFER"`)
       - `amount_sats` for underlying DGB value
       - `asset_id` and total asset units moved
       - `metadata_size` for payload risk heuristics
   - Tests should verify that missing fields are treated as high‑risk or
     rejected, not silently accepted.

2. **Rule interaction**
   - `modules/digiassets/guardian-rules.md` defines suggested guard rails
     (max supply, issuer whitelists, AML / abuse patterns).
   - Integration tests should confirm that these rules can be expressed via
     Guardian’s policy engine and that the right deny / challenge decisions
     are produced for synthetic scenarios.

3. **Shield Bridge propagation**
   - When DD minting or other modules construct a RiskPacket that includes
     DigiAssets context, Shield Bridge must forward the data unchanged to
     Sentinel / DQSN / ADN / QWG / Adaptive layers.

Future work may move some of these expectations into explicit Python tests
once Guardian + Bridge wiring for DigiAssets is fully implemented.

---

## 6. How To Extend The DigiAssets Test Suite

When DigiByte Core or wallet developers implement new DigiAssets features,
they should:

1. **Add or update tests before wiring real mainnet logic.**
2. Prefer focussed, **small tests** that verify outcomes, not internals.
3. Mirror every new rule or invariant in `modules/digiassets/spec.md` with
   at least one test in this directory.
4. Keep fixtures realistic but minimal — if possible, encode small synthetic
   DigiAssets examples instead of copying entire mainnet blocks.

Suggested additions for future versions:

- regression tests for historical DigiAssets incidents (if any are
  disclosed)
- cross‑module tests where DigiAssets, DD minting and Enigmatic all touch
  the same transaction set
- performance tests for high‑throughput mint / transfer bursts in test
  environments

---

## 7. Summary

The DigiAssets test suite is the **safety net** for all asset‑layer
behaviour in the DigiByte Adamantine Wallet.

By keeping this document and the corresponding tests up to date, we ensure
that:

- DigiAssets remain predictable and safe for end users,
- Guardian + Shield Bridge receive the information they need,
- future contributors can extend the system without breaking existing
  assumptions.

If you add new DigiAssets features, **start by updating this file and the
three Python test modules**, then wire the behaviour into the engine and
indexer. In this project, tests and specs move first — code follows.
