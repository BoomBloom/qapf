# 13 — Build the point-in-time universe (fix survivorship bias)

**Type:** `wayfinder:task`
**Blocked by:** None — can start immediately.
**Status:** open · unclaimed

## Question

Ticket 10 decided: fix survivorship bias properly, before ticket 07's attempt 2 runs, and this does not
consume any of ticket 02's 5 validation attempts. This ticket is the actual build.

The current 15-name universe (AAPL, MSFT, GOOGL, AMZN, NVDA, JPM, V, WMT, KO, PEP, XOM, CVX, JNJ, PG, HD)
was hand-picked in 2026 with knowledge of which names became winners — every backtest result on it,
including ticket 07's attempt 1, is inflated by an unmeasured amount on every window tested.

## What to build

- [ ] Run Qlib's PIT constituents builder (`reference/qlib/scripts/data_collector/us_index/collector.py`,
      already vendored — see `docs/research/data-and-modelling-tooling.md` for the verification that
      found it) to get the real S&P 500 (or a defensible sub-universe) constituent history for the
      2008-2017 validation window.
- [ ] Wire delisted-price coverage via Sharadar (~$9/mo, verified yfinance returns 0 rows for delisted
      tickers — this is why the current universe silently excludes every name that failed).
- [ ] Decide and document the final universe-selection rule (e.g. "top N by market cap as of each
      rebalance date, from the real historical constituent list") — this replaces the hardcoded 15-ticker
      list in `.scratch/wayfinder-real-capital/validate_bar.py` and any other hardcoded universe.
- [ ] Cross-check: the new universe should include names that were later delisted, went bankrupt, or were
      acquired during 2008-2017 — if it doesn't, the PIT fix didn't actually work.
- [ ] Re-verify data coverage the same way `validate_bar.py` already does (per-ticker trading-day counts),
      now against the PIT universe instead of the hand-picked one.

## Interaction with ticket 01's account-size decision

Ticket 01 decided the strategy must shrink to mechanically fit a $1,000 account (fewer/cheaper names,
possibly lower rebalance frequency) rather than raising the account size. Whoever builds the PIT universe
here should keep that constraint in view — the final universe size feeding ticket 07's attempt 2 should
be chosen with both concerns in mind at once (bias-free AND $1,000-sized), not fixed independently and
then discovered to conflict.

## Not in scope here

Redesigning the factor set itself (momentum/reversal/low-vol/volume-trend) — that's ticket 07's attempt 2,
which consumes this ticket's output as an input, not the other way round.
