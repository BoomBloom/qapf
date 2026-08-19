# 01 — What drawdown and daily-loss limits bind this system?

**Type:** `wayfinder:grilling`
**Blocked by:** None — can start immediately.
**Status:** open · unclaimed

## Question

What drawdown and daily-loss limits bind this system?

Agent 10 (the CRO) is built and enforces limits, but `max_drawdown_pct` and `max_daily_loss_pct` are
deliberately unset — they encode risk appetite, which is the operator's decision, not the system's.
This has been open since the CRO was built and now blocks everything downstream: a strategy cannot be
validated against a bar that does not exist.

Concrete anchors from the real backtest: a 25% drawdown limit would have halted trading on 2020-02-27,
the actual day the COVID crash began. A 15% limit would have halted in Q4 2018, during ordinary
volatility. The strategy's own measured max drawdown was -36.68%, which would have breached both.

The decision is not only "what number" but "what happens at the number" — halt and wait for a human, or
halt and require re-validation before restarting?
