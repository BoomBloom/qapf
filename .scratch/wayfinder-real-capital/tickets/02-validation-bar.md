# 02 — What exactly must the strategy prove before it touches real money?

**Type:** `wayfinder:grilling`
**Blocked by:** None — can start immediately.
**Status:** open · unclaimed

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
