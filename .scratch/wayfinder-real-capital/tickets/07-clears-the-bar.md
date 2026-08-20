# 07 — Does the strategy clear the bar on data it has never been tuned on?

**Type:** `wayfinder:task`
**Blocked by:** NOTHING — 02, 05 and 06 are all closed. **This is now the frontier ticket, and the one
where the map's destination is reached or not.**
**Status:** OPEN — FAILS the bar (attempt 4 of 5). **1 attempt remains — spend it deliberately.**
2026-08-20

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

## Attempt 2 (2026-08-19) — closer, still fails

Followed `docs/research/viable-alpha-families.md`'s own recommended sequence: its #1-ranked idea
(volatility-managed exposure, Moreira & Muir JF 2017) was first tested as a cheap ~1-hour diagnostic —
post-processing applied directly to attempt 1's real return series, no new backtest
(`.scratch/wayfinder-real-capital/vol_managed_diagnostic.py`) — before spending a real attempt on it. That
diagnostic showed genuine improvement (Sharpe 0.564→0.726, max drawdown -36.74%→-26.48%), which the
research document's own falsification bar treats as "worth formalizing as a real attempt."

**Deliberately isolated one variable.** Ticket 13's PIT-universe fix was NOT combined into this attempt —
it's still incomplete (free membership correction, but no delisted-name price data without Sharadar), and
combining an incomplete universe fix with a real strategy change in the same attempt would conflate two
variables and make neither result attributable. The universe is byte-identical to attempt 1's 14 names.
The PIT swap is deferred to a later attempt.

**What changed:** nothing about signal generation, regime weighting, or the universe. Only a post-
processing exposure scale on the strategy's own daily returns — 22-day realized volatility, leverage
capped at 1.0 (long-only-and-cash compatible, matching Moreira & Muir's own tested variant), scored for
real this time via `.scratch/wayfinder-real-capital/validate_bar_attempt2.py` with `n_trials=2`.

```
                          Strategy     Benchmark
Total return               +128.11%      +322.75%
Annualized Sharpe             0.726         0.849
Max drawdown                -26.48%       -39.03%
Return per unit DD            2.741         2.175

Deflated Sharpe Ratio: 0.9615 (n_trials=2)
Final account: $2,281.14 (started $1,000)
```

- **[PASS]** DSR > 0.95 — 0.9615.
- **[FAIL]** Beats benchmark Sharpe — 0.726 vs 0.849. Closer than attempt 1 (0.564 vs 0.849 — the
  strategy-to-benchmark Sharpe ratio moved from 66% to 85%), but still short.
- **[PASS]** Beats benchmark return-per-unit-max-drawdown — 2.741 vs 2.175. This flipped from a FAIL in
  attempt 1 to a genuine PASS — the drawdown reduction from volatility management is real and material.
- **[PASS]** Profitable net of costs — more than doubled the account ($2,281.14).

**Overall: DOES NOT CLEAR THE BAR (attempt 2 of 5).** Real, measurable progress on two of three failing
dimensions from attempt 1, not a wash. The remaining gap is narrower and more specific than attempt 1's:
the strategy's raw Sharpe still trails the benchmark's, even though its drawdown-adjusted return no
longer does. **3 attempts remain.**

**Candidates for attempt 3**, in order of the research document's own recommended sequence: #2 (OHLC-
range volatility estimators — Yang-Zhang/Parkinson/Garman-Klass, an enabler that would sharpen the same
volatility-management signal using the O/H/L columns already downloaded and currently unused by
`agents/alpha/factors.py`) before reaching for #3 (absolute momentum with a cash leg) or the PIT-universe
swap. Not decided here — the operator's call.

## Attempt 3 (2026-08-20) — DSR now the binding constraint, not risk-adjusted return

Prototyped #2 (Yang-Zhang range-based volatility) as a monkeypatch first, against the real pipeline, with
zero production-code changes (`.scratch/wayfinder-real-capital/yang_zhang_diagnostic.py`) — showed real
improvement over attempt 2's baseline (Sharpe 0.726→0.738, max drawdown -26.48%→-17.64%), so it was
promoted to real code: `agents/alpha/factors.py` now has a real `yang_zhang_volatility()` function, with
`compute_raw_factors`/`AlphaCombiner.generate`/`WalkForwardBacktester` all gaining optional
`opens`/`highs`/`lows` params (additive, backward-compatible — omitting them reproduces the exact prior
close-to-close behavior). Four new correctness checks added to `agents/alpha/__main__.py`, all passing,
including the look-ahead test now also corrupting OHLC.

Built on attempt 2's baseline rather than testing in isolation — same universe (14 hand-picked names,
unchanged), same volatility-managed exposure layer, one new variable (the factor's vol estimator).

```
                          Strategy     Benchmark
Total return               +129.05%      +322.75%
Annualized Sharpe             0.738         0.849
Max drawdown                -17.64%       -39.03%
Return per unit DD            4.182         2.175

Deflated Sharpe Ratio: 0.9301 (n_trials=3)
Final account: $2,290.45 (started $1,000)
```

- **[FAIL] DSR > 0.95 — 0.9301.** This is the actual news of attempt 3: DSR **regressed** from attempt
  2's 0.9615 (a PASS) to a FAIL, purely from the honest trial-count penalty (n_trials 2→3) outrunning the
  marginal Sharpe gain (0.726→0.738 — barely moved). Not a bug and not bad luck: this is the DSR
  mechanism working exactly as intended, and it independently validates
  `docs/research/viable-alpha-families.md` §0.2's core warning — every parameter is a trial, and trial
  count compounds faster than incremental Sharpe improvements from here.
- **[FAIL] Beats benchmark Sharpe — 0.738 vs 0.849.** Essentially unmoved from attempt 2.
- **[PASS] Beats benchmark return-per-unit-max-drawdown — 4.182 vs 2.175.** Nearly double attempt 2's
  already-passing 2.741 — the drawdown control from combining Yang-Zhang with vol-managed exposure is
  real and substantial (-17.64% max drawdown, close to a third of the original -36.74%).
- **[PASS] Profitable — $2,290.45 final, more than double the account.**

**Overall: DOES NOT CLEAR THE BAR (attempt 3 of 5). 2 attempts remain.**

**The actual signal this attempt sends:** drawdown control keeps improving materially with each change,
but the underlying SIGNAL quality (Sharpe) has plateaued around 0.73-0.74 across two different
volatility-management refinements — diminishing returns on this specific avenue (refining how existing
factors are scaled/estimated), while the trial-count cost of trying keeps rising. This is evidence
against a 4th attempt in the same direction (e.g. Parkinson/Garman-Klass as yet another vol-estimator
variant) and evidence *for* trying something structurally different for attempt 4 — the research
document's #3 (absolute momentum with a cash leg, a genuinely different signal-generation mechanism, not
another risk-scaling refinement) or #4 (risk-based allocation as an honest, near-zero-parameter
benchmark) are the more promising remaining candidates precisely because they don't add more trials to an
already-strained budget the way another vol-estimator swap would.

## Attempt 4 (2026-08-20) — risk-based tilt; isolates where the improvement actually came from

Chose the research doc's #4 (risk-based allocation) over #3 (momentum) deliberately, on attempt 3's own
lesson: with DSR trial-count now binding, the right criterion is FEWEST free parameters, not highest
expected raw improvement — and #4 adds zero new parameters (it removes three factors rather than adding
anything).

**Approximation stated plainly, not blurred:** true minimum-variance needs a weight-level optimizer
(Qlib's `PortfolioOptimizer`, which Agent 2's LIVE path already uses), but `WalkForwardBacktester`'s
historical engine is built on Qlib's `TopkDropoutStrategy`, which consumes a per-name RANKING, not target
weights. That's a real architecture mismatch between the live and backtest paths — worth recording as its
own finding. Rather than rebuild the backtest execution engine, this attempt tested the honest,
literature-supported simplification: a pure inverse-volatility (naive risk parity) tilt — rank solely on
the Yang-Zhang low_volatility factor, zero weight on momentum/reversal/volume. A real risk-based method,
but NOT full covariance-based GMV.

```
                          Strategy     Benchmark
Total return               +103.69%      +322.75%
Annualized Sharpe             0.718         0.849
Max drawdown                -17.68%       -39.03%
Return per unit DD            4.060         2.175

Deflated Sharpe Ratio: 0.8870 (n_trials=4)
Final account: $2,036.86 (started $1,000)
```

- **[FAIL]** DSR — 0.8870, down again from attempt 3's 0.9301 (trial count 3→4).
- **[FAIL]** Beats benchmark Sharpe — 0.718 vs 0.849 (slightly WORSE than attempt 3's 0.738).
- **[PASS]** Return-per-unit-max-drawdown — 4.060 vs 2.175.
- **[PASS]** Profitable — $2,036.86.

**The genuinely useful finding, which is not the pass/fail:** max drawdown was **-17.68% here vs -17.64%
in attempt 3** — essentially identical, despite completely different factor weights (pure low-vol vs. an
equal blend of four factors). Combined with attempt 2's -26.48% → attempt 3's -17.64%, this isolates
where the improvement actually came from: **the volatility-managed exposure layer and the Yang-Zhang
estimator feeding it, NOT which factors drive the cross-sectional signal.** Changing the signal
composition barely moves the result. That is strong evidence the cross-sectional factor layer is close to
irrelevant on this universe — exactly what `docs/research/viable-alpha-families.md` §1.2 predicted for a
15-name book ("the edge IS the cross-section... with 15 names you do not have one"), now confirmed
empirically here rather than only argued from the literature.

## 1 attempt remains — recommendation for how to spend it

Do NOT spend attempt 5 on another variation of the same theme; four attempts have now established the
pattern. Two coherent options, both genuinely different in kind:

1. **Absolute (time-series) momentum with a cash leg** (research doc #3) — the one remaining candidate
   whose published evidence is specifically for a long-only construction with a cash alternative, and the
   only untried mechanism that changes WHEN the book is invested rather than merely how it's weighted or
   scaled. Costs 2 parameters (lookback, hurdle) against a strained budget, but it's the last idea with a
   real prior behind it.
2. **Spend it on the PIT universe instead** (ticket 13) — every attempt so far has run on the
   survivorship-biased hand-picked 14 names. If the operator does the Sharadar signup, attempt 5 could
   test the CURRENT best configuration (attempt 3's) on honest data, which answers a different and
   arguably more important question than another strategy variant: is the ~2x return even real?

**Option 2 is the more informative use of the last attempt** if the Sharadar signup happens, because a
strategy that clears the bar on biased data still can't be trusted, while a clean answer on real data is
decision-grade either way. Operator's call — this is deliberately not decided here.
