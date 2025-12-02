# DigiDollar (DD) — Oracle & Risk Model (oracle-and-risks.md)

Status: **draft v0.1 – internal skeleton**

This document explains how **oracle data** (if used) interacts with the
DigiDollar (DD) module and how associated risks are handled.

Adamantine is designed to work **safely even without any oracle**.
Oracles are strictly optional hints, not hard dependencies.

---

## 1. Oracle Role (Optional)

Potential uses of an oracle in DD:

- provide **DGB ↔ fiat** rate hints for UI and conversion helpers,
- suggest **bucketed risk levels** based on volatility,
- flag abnormal market conditions (flash crashes, spikes).

Oracle does **not**:

- set final DD value,
- replace DGB backing guarantees,
- control mint / redeem eligibility directly.

---

## 2. OracleSnapshot Structure

Conceptual structure (for UI + hints):

```ts
OracleSnapshot {
  dgb_fiat_rate: number           // e.g. price per DGB in chosen fiat
  fiat_code: string               // "USD", "GBP", etc.

  volatility_index: number        // 0.0 – 1.0 (0 = calm, 1 = extreme)
  market_regime: "calm" | "normal" | "volatile" | "extreme"

  last_update_at: timestamp
  is_stale: boolean
  source: string                  // e.g. "oracle1.example"
}
```

Wallet MUST treat oracle data as **untrusted input**:

- always check timestamps,
- mark stale data clearly,
- degrade behaviour safely if missing or inconsistent.

---

## 3. Conversion Logic (Hinting Only)

For DD, the simplest model is:

- 1 DD ≈ 1 DGB (or another clear unit agreed on in spec).

Oracle can be used to **display** equivalent fiat values and to
optionally warn users when volatility is very high.

Example UX:

- “You are converting 100 DGB into ~100 DD (~$X at current rates).”
- If volatility is extreme, show banner:
  - “Market volatility is high; DD minting may carry extra risk.”

The underlying backing remains in DGB; the oracle does not change that.

---

## 4. Risk Model Around Oracles

Oracle-related risks include:

- **Stale data**: user sees outdated rates.
- **Manipulated data**: malicious source feeds wrong prices.
- **Outage**: no oracle data at all.

Mitigations:

1. **Multiple sources (optional)**:
   - cross-check different providers,
   - mark disagreements clearly in diagnostics.

2. **Staleness checks**:
   - treat snapshots older than a configured threshold as `is_stale = true`,
   - do not base any strict limits on stale values.

3. **Guardian integration**:
   - Risk Engine may add a **small** risk score bump when:
     - oracle is stale,
     - or market_regime = "extreme".

4. **No critical dependency**:
   - mint / redeem flows must remain possible without oracle,
   - Guardian decisions rely primarily on on-chain & shield data,
     not external price feeds.

---

## 5. Guardian & Risk Engine Use

Risk Engine may consider oracle hints as a **minor factor**:

- if `market_regime = "extreme"`:
  - increase score slightly for large mints / redeems,
  - possibly push them from `medium` → `high` for some profiles.

- if oracle data is **missing or inconsistent**:
  - do **not** downgrade risk,
  - simply avoid using oracle as a stabilising factor.

Guardian configs (`configs.md`) should never assume oracle presence.

---

## 6. UI Behaviour

The UI should:

- show fiat equivalents as **approximate**:
  - “≈ $X”, not “= $X”.
- show a small indicator when oracle data is stale or unavailable.
- clearly separate:
  - DD balance (backed by DGB),
  - fiat equivalence (just a view).

During high volatility, consider subtle but clear messaging, e.g.:

- “DD is fully backed by DGB, but DGB price is moving fast today.”

---

## 7. No Implicit Promises

Documentation and UI must avoid language that suggests:

- guaranteed peg to any fiat currency,
- insurance or external guarantees,
- centralised redemption rights beyond what the wallet implements.

DD’s promise is purely:
- “This wallet tracks a fully backed DGB synthetic unit.”

Oracle data is **informational only**.

---

## 8. Future Extensions

Potential future directions:

- multiple DD “views” (e.g. DGB-backed, multi-asset backed),
- pluggable oracle modules,
- user-selectable oracle providers with transparency,
- threshold-based warnings (“don’t mint if volatility > X unless confirmed”).
