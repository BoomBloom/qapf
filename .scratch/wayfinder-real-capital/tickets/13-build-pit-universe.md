# 13 — Build the point-in-time universe (fix survivorship bias)

**Type:** `wayfinder:task`
**Blocked by:** None — can start immediately.
**Status:** HALF DONE, 2026-08-19 — membership fixed for free; delisted prices need the operator (see Resolution)

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

## Resolution (2026-08-19) — real progress, and one real limit found by actually running it

**Discovered while running Qlib's vendored PIT collector for real, not assumed from prior research:**
Wikipedia's "List of S&P 500 companies" article no longer has the "Selected changes" section at all as
of 2026 (verified directly — fetched the live page, only 2 tables come back; the MediaWiki API's own
section list confirms the section is gone). The collector's `get_changes()` depends entirely on that
table and crashes against the live page. Not a bug in this project's code — an upstream content change
the earlier research (which called this builder "free and already vendored") didn't anticipate because
it never actually ran the tool.

**Real fix, verified working:** Wikipedia keeps full revision history. The changes table existed as of
the 2024-05-23 revision (id `1225357006`) — confirmed by fetching that exact revision and finding a
345-row table with the columns the collector expects, covering 1997-06-17 through 2024-05-08 (189 of
those 345 changes fall inside the 2008-2017 validation window). `.scratch/wayfinder-real-capital/
build_pit_universe.py` subclasses `SP500Index`, points `WIKISP500_CHANGES_URL` at that historical
revision instead of the live page, and runs `parse_instruments()` unmodified otherwise.

**Ran successfully.** Wrote `~/.qlib/qlib_data/us_data/instruments/sp500.txt` — 829 symbol-interval
rows. Verified against real, independently-checkable 2008 events, not trusted on faith: **Lehman
Brothers (removed 2008-09-15), Fannie Mae and Freddie Mac (removed 2008-09-11, conservatorship), and
Wachovia (removed 2008-12-30, Wells Fargo acquisition) all appear with correct removal dates.** These
are exactly the names a 2026-hindsight-picked 15-name universe structurally cannot include — this is
real progress on the actual bias, not just a relabeled current constituent list.

**The genuine remaining gap, found by checking rather than assuming:** membership is now point-in-time
correct, but Qlib's bundled price dataset has **zero rows** for delisted names (verified: `LEH`, `FNM`,
`FRE`, `WB` all return 0 observations) — and yfinance does too (re-verified live, not just trusted the
earlier research note: all four return "possibly delisted; no price data found"). **Fixing membership
without delisted prices is a real, partial improvement — it removes hindsight bias on which names get
ADDED to a period's universe — but a backtest still can't price a name's actual loss on the way to
delisting/bankruptcy without price data that only a provider like Sharadar has.** That $9/mo signup is
the operator's to do, not mine — CLAUDE.md's safety rules mean I cannot create accounts or enter payment
details on your behalf, so this ticket cannot fully close without you.

**Left for whoever picks this up next:** wire the new `sp500.txt` into `validate_bar.py`'s universe
selection (currently still the hand-picked 15 names) once a decision is made on whether to proceed with
membership-only correction now or wait for delisted prices before running ticket 07's attempt 2.
