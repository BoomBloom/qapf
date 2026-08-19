# 07 — Does the strategy clear the bar on data it has never been tuned on?

**Type:** `wayfinder:task`
**Blocked by:** NOTHING — 02, 05 and 06 are all closed. **This is now the frontier ticket, and the one
where the map's destination is reached or not.**
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

### Fully specified as of ticket 06's resolution (2026-08-19)

Everything this ticket needs is now settled:

1. **Flatten** `REGIME_FACTOR_WEIGHTS` to 0.25 x 4, identical across regimes (ticket 06). Invert Agent 7's
   regime-sensitivity test, which currently asserts the opposite.
2. **Run on 2008-2017**, 14 of 15 tickers (V excluded — IPO'd 2008).
3. **Report all three bar conditions** (ticket 02): DSR > 0.95; beats equal-weight buy-and-hold on Sharpe
   AND on return-per-unit-of-max-drawdown; profitable net of Agent 11's costs at $1,000.
4. **Also report the benchmark's own Sharpe and max drawdown** — never computed in the 2018-2020 run, so
   the risk-adjusted comparison the bar demands has never actually been made.
5. **Log this as attempt 1 of 5** and set Agent 4's `n_trials` accordingly.
6. Note the caveats that stand regardless of outcome: the universe is survivorship-biased (ticket 10) and
   drawdown is measured on daily closes rather than intraday equity (ticket 11), so any drawdown figure is
   optimistic.
