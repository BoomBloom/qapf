# 07 — Does the strategy clear the bar on data it has never been tuned on?

**Type:** `wayfinder:task`
**Blocked by:** NOTHING — 02, 05 and 06 are all closed. **This is now the frontier ticket, and the one
where the map's destination is reached or not.**
**Status:** CLOSED — FAILS the bar (attempt 1 of 5), 2026-08-19

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

## Resolution (2026-08-19)

### Attempt 1 was run twice — the first run was invalidated by a real bug, not a strategy failure

First run used Qlib's generic `EXCHANGE_KWARGS` (`min_cost=5`, a flat $5-per-trade minimum). At $1,000
starting capital with monthly rebalancing across ~7 position changes/month over 121 months, that flat
minimum alone consumed 85% of the account before the strategy became too poor to trade at all — total
cost reached $850. The result (`-92.24%` total return alongside only `-32.74%` max drawdown) was
internally inconsistent for the same equity curve, which is what caught it: I diagnosed the `account`
vs `return` column divergence directly rather than reporting an implausible number. Verified via
WebSearch that IBKR Lite — the operator's actual target broker (ticket 09 candidate) — charges **$0**
commission on US stock trades, no account minimum. Fixed by parameterizing
`WalkForwardBacktester.run()` with an `exchange_kwargs` override
([walkforward.py](../../../backend/agents/backtest/walkforward.py)) and passing IBKR Lite's real cost
structure (`min_cost=0`) instead of Qlib's generic default. Committed as `d6dd481`. This also caught and
fixed an unrelated real bug in the same file: the FRED macro-series fetch had no `start_date`, silently
defaulting to 2015-01-01 and breaking on any `test_start` before that (this window starts 2008).

### The real, corrected result

```
                          Strategy     Benchmark
Total return               +95.28%      +322.75%
Annualized Sharpe             0.564        0.849
Max drawdown                -36.74%      -39.03%
Return per unit DD            1.536        2.175

Deflated Sharpe Ratio: 0.9636 (n_trials=1)
Final account: $1,952.78 (started $1,000)
```

- **[PASS]** DSR > 0.95 — 0.9636. The signal is statistically real, not noise from over-fitting a
  4-factor combination.
- **[FAIL]** Beats benchmark Sharpe — 0.564 vs 0.849.
- **[FAIL]** Beats benchmark return-per-unit-max-drawdown — 1.536 vs 2.175.
- **[PASS]** Profitable net of costs at $1,000 — nearly doubled the account ($1,952.78).

**Overall: DOES NOT CLEAR THE BAR.** Internally consistent this time (total return and max drawdown are
mutually plausible for the same equity curve, unlike the first run) — this is a trustworthy attempt-1
result, not another artifact.

### What this actually means

The strategy is profitable and its edge is statistically real (DSR clears the 0.95 bar comfortably), but
**simply buying and holding the same 14 large-cap names equally weighted beats it on both risk-adjusted
measures** over 2008-2017. The 4-factor combination (momentum-12-1, 5-day reversal, low-vol, volume-trend,
now flat-weighted per ticket 06) isn't adding value over the market it's picking from — it's under-using
information already in a naive buy-and-hold of the same names. This is a legitimate, informative failure:
it says the current factor set / signal construction is the binding constraint, not the regime-weighting
scheme (already fixed in ticket 06) or the cost model (fixed above).

**4 attempts remain** in ticket 02's 5-attempt budget. `docs/research/viable-alpha-families.md` (Kakushadze
& Serur-sourced, ranked shortlist: volatility-managed exposure, OHLC range-vol estimators, absolute/
time-series momentum with cash leg, risk-based allocation as benchmark, meta-labelling) is the natural
input for what attempt 2 changes — not yet read in full or turned into a concrete attempt-2 plan. That's
the next fog to resolve, not a new ticket by itself: whether attempt 2 gets its own ticket or is scoped
directly is undecided.

Standing caveats (survivorship bias, daily-close drawdown) apply to this result exactly as anticipated —
noted, not yet corrected; they would only make a real failure look worse, not better, so they don't change
the verdict here.
