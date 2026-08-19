# 07 — Does the strategy clear the bar on data it has never been tuned on?

**Type:** `wayfinder:task`
**Blocked by:** 06 (regime-weights-decision) — ticket 02 is now CLOSED, and its resolution removed
the dependency on ticket 03 by establishing that 2008-2017 is an untouched window available today.
**Status:** open · unclaimed

## Question

Does the strategy clear the bar on data it has never been tuned on?

The moment of truth for this map. Runs the strategy — with whatever weights ticket 06 settles on —
against the untouched window from ticket 02, using the extended data from ticket 03, and reports
whether it clears the bar.

Resolution records the actual numbers, whatever they are. A failure here is a legitimate and likely
outcome, and resolves this ticket just as validly as a pass. What happens next in that case is
deliberately left in the map's fog, because it depends on how it fails.

### Updated by ticket 02's resolution (2026-08-19)

The bar is now defined, so this ticket has a concrete pass/fail test:

- Window: **2008-2017** (14/15 tickers; V excluded, IPO'd 2008).
- Must clear ALL THREE: DSR > 0.95; beats equal-weight buy-and-hold on Sharpe AND return-per-unit-of-max-drawdown; profitable net of Agent 11's costs at $1,000.
- Attempt budget: **5**, with `n_trials` incremented honestly each attempt.
- Report the benchmark's own Sharpe and max drawdown too — the 2018-2020 run never computed them, so the risk-adjusted comparison has never actually been made.
