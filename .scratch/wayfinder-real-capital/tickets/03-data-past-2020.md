# 03 — How do we obtain point-in-time US equity data past 2020-11-10?

**Type:** `wayfinder:research`
**Blocked by:** None — can start immediately.
**Status:** open · unclaimed

## Question

How do we obtain point-in-time US equity data past 2020-11-10?

Qlib's bundled dataset — the only price source verified compatible with its execution engine — has a
calendar that stops at 2020-11-10. Every backtest this project has run therefore ends there, and spans
only 2018-2020.

That is disqualifying for a real-capital decision on its own: three years is thin for a
regime-conditional strategy (it observes each macro regime roughly once), the window is dominated by
COVID, and nothing after 2020 has been tested at all — including the 2022 inflation regime, which is
exactly the kind of environment the strategy claims to condition on.

What is needed: a data source that is point-in-time correct (no survivorship bias, no restatements),
covers a materially longer history, and can drive Qlib's execution engine — or a documented decision to
replace that engine.

Investigate: Qlib's own data-collector scripts for building a fresh bundle from Yahoo; commercial
point-in-time vendors and their cost; whether survivorship bias in free sources is severe enough to
invalidate results. Record what each option actually costs in money and effort.

### Reframed by ticket 02's resolution (2026-08-19)

**No longer on the critical path.** Ticket 02 established that 2008-2017 is an untouched validation
window available in the existing bundle, so validation can proceed today without this.

This ticket now serves the **final holdout** — the window looked at exactly once, after the strategy has
already cleared the bar on 2008-2017. That raises the standard for the data: it must be point-in-time
correct, because a final holdout contaminated by survivorship or restatement bias is worse than no
holdout at all (it manufactures false confidence at the exact moment capital is committed).

### New evidence (2026-08-19) — `docs/research/data-and-modelling-tooling.md`

A research pass dispatched from the operator's resource links (not itself a wayfinder ticket) found a
concrete, mostly-free path:

- **`reference/qlib/scripts/data_collector/us_index/collector.py`** (already vendored in this repo)
  builds a point-in-time S&P 500 constituents file from 1999 — `$0`. Cross-check against MIT-licensed
  `fja05680/sp500` before trusting it; it scrapes a user-editable Wikipedia table.
- **`reference/qlib/scripts/dump_bin.py`** rebuilds the price bundle past the 2020-11-10 cliff — `$0`.
  The cliff was never a data-availability problem, just a bundle nobody regenerated.
- **Delisted-security prices are the one real gap.** Verified empirically in this repo's venv: yfinance
  returns 0 rows for TWTR, ATVI, FRC, SIVBQ, CERN, ENRNQ. Cheapest verified fix: **Sharadar Prices,
  $9/month**, 21,000 active+delisted tickers to 1998 (free DJIA-30 tier to trial first).
- OpenBB rejected as a fix: no delisted data in its codebase, sells no data of its own, and is
  AGPL-3.0 — a real license conflict with this project's Apache-2.0/MIT posture.

Recommended order: `dump_bin.py` -> Qlib's PIT collector, cross-checked -> trial Sharadar's free tier ->
re-run Agent 9 on a real 2021-2024 PIT universe. Still a TASK (AFK) — this is now well-specified enough
to execute, not yet executed.
