# 10 — How do we handle survivorship bias in the universe?

**Type:** `wayfinder:grilling`
**Blocked by:** None — can start immediately.
**Status:** open · unclaimed

## Question

Surfaced while resolving ticket 02, and sharp enough to ticket.

The 15-name universe (AAPL, MSFT, GOOGL, AMZN, NVDA, JPM, V, WMT, KO, PEP, XOM, CVX, JNJ, PG, HD) was
hand-picked in 2026 with full knowledge of which companies became winners. Backtesting it over any
historical window partly measures "what if you had known in advance that NVDA and AAPL would win."

This inflates results on **every** window, validation or holdout, and **no amount of holdout discipline
fixes it** — the bias is in the universe, not the dates. Only a point-in-time universe (the index
constituents as they actually stood on each historical date, including names later delisted or acquired)
would solve it.

The decision is what to do about it, given it cannot be ignored before committing real capital:

- **Accept and document it** — report every result with the caveat attached, and let the paper-trading
  stage (which is inherently free of the bias, since it trades forward) be what actually settles it.
- **Fix it properly** — source point-in-time index constituents and rebuild the universe historically.
  Correct, and materially more work; Qlib's bundle does not carry constituent history.
- **Reduce it** — pick the universe by a rule applied at the window's start (e.g. the largest 15 by
  market cap as of 2008) rather than by hindsight. Cheaper than a full fix, and removes the worst of the
  bias.

Note the interaction with ticket 02's five-attempt budget: changing the universe is arguably a new
attempt, and should probably be counted as one.

### New evidence (2026-08-19) — `docs/research/data-and-modelling-tooling.md`

Changes the cost of the "fix it properly" option from a guess to a number. Originally scoped as
"materially more work" with no estimate. Now: Qlib's own PIT constituents builder is free and already
vendored, and delisted-price data costs $9/month via Sharadar. **"Fix it properly" may now be cheaper
than "accept and document," which was the assumption when this ticket was opened.** Still the operator's
decision — this is new information for it, not a resolution.
