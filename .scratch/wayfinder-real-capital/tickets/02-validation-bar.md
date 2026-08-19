# 02 — What exactly must the strategy prove before it touches real money?

**Type:** `wayfinder:grilling`
**Blocked by:** None — can start immediately.
**Status:** CLOSED 2026-08-19 · resolved with the operator

## Question

What exactly must the strategy prove before it touches real money?

Settled in charting: validation comes before capital. Not settled: the precise bar.

The proposal on the table is Deflated Sharpe Ratio > 0.95 on a walk-forward window the strategy has
never been tuned against. That needs pinning down before it means anything:

- Which window is the untouched one, and how do we guarantee it stays untouched? Every parameter chosen
  so far has seen 2018-2020.
- Is DSR alone sufficient, or must the strategy also beat equal-weight buy-and-hold net of costs? The
  current strategy is statistically insignificant AND underperforms its benchmark — those are two
  separate failures and the bar should say whether both must be cleared.
- How many attempts are permitted before the bar itself is compromised? Every re-test on the same data
  is another trial, which is precisely what the Deflated Sharpe Ratio corrects for. Ten attempts at a
  0.95 DSR is not the same evidence as one.

The bar must be written down before the next attempt, not after seeing its result.

---

## Resolution (2026-08-19)

### The validation window: 2008-2017

Established as fact while resolving this: an untouched window already exists in the Qlib bundle the
project already has. Nothing in this project has ever looked at pre-2018 data.

| Window | Coverage | Length |
|---|---|---|
| 2012-2017 | 15/15 tickers complete | 6 years |
| **2008-2017 (chosen)** | 14/15 (V IPO'd 2008) | 10 years, includes the GFC |
| 2004-2017 | 13/15 (GOOGL IPO'd 2004) | 14 years |

**2008-2017 is the validation window.** It buys a genuine crisis regime the strategy has never seen —
and since the strategy explicitly claims to condition on macro regimes, a real contraction is the test
that matters most. Dropping Visa costs little.

**Post-2020 data (ticket 03) is reserved as a FINAL holdout, to be looked at exactly once, ever.**

Consequence for the map: **ticket 07 is no longer blocked by ticket 03.** The critical path shortens to
05 -> 06 -> 07, and ticket 03 changes character — it now serves the final holdout, not the validation.

### The bar: three conditions, all required

1. **Deflated Sharpe Ratio > 0.95** — is the result distinguishable from luck?
2. **Beats equal-weight buy-and-hold on a RISK-ADJUSTED basis** — Sharpe, and return per unit of max
   drawdown. Deliberately not raw return: the strategy holds 80% gross with 20% cash, so it
   *mechanically* loses a raw-return race in a bull market. The 2018-2020 gap (+27.54% vs +50.98%) is
   partly cash drag rather than stock-selection failure, and a bar that cannot tell those apart is a bad
   bar.
3. **Profitable net of Agent 11's execution-cost estimates at the $1,000 account size** — not at $1M,
   where fixed costs and whole-share rounding vanish.

Three distinct failure modes. Passing one says nothing about the others.

### The attempt budget: five

Every re-test on the same window is another trial, which is precisely what the Deflated Sharpe Ratio
corrects for. Ten attempts at 0.95 is far weaker evidence than one.

**Five attempts.** `n_trials` in Agent 4's DSR call must be incremented honestly with each attempt — it
currently sits at 4 (one per factor) and must grow as variants are tried. **Exhausting the budget without
clearing is itself a result**: it means this approach does not work on this universe, and the honest
response is to return to research rather than keep tuning. Agreed in advance, on purpose.

### Caveat that no amount of holdout discipline fixes

The 15-ticker universe was hand-picked in 2026 with knowledge of which companies became winners. Testing
it over 2008-2017 partly measures "what if you had known NVDA and AAPL would win." This inflates results
on ANY window and is not solved by holdout discipline — only a point-in-time universe would solve it.
Surfaced here and ticketed separately (ticket 10).
