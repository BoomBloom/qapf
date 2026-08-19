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

---

## New evidence (2026-08-19) — `docs/research/position-sizing-and-risk-limits.md` (601 lines, cited)

Research dispatched against primary sources (Vince, Carver, Chan, prop-firm anchors) plus the actual
code. Still open — the threshold choice remains the operator's — but now well-informed rather than
guessed.

**Recommendation:** `max_drawdown_pct = 0.20`, `max_daily_loss_pct = 0.06`. Reasoned from the existing
15%/25% anchors (closer to 25%, since the literature's fractional-sizing philosophy treats the 15%
ordinary-volatility false-halt as the worse failure mode than a slightly later stop) and from the
prop-firm 3-5% daily range, adjusted upward for the CRO's stricter close-to-close (non-intraday) mechanic.

**A gap independent of any threshold choice, found by reading the actual code:** `kill_switch_triggered`
is computed and reported by `backend/risk/monitor.py` but **nothing in the codebase currently consumes
it to block an order.** The CRO reports; it does not yet enforce. Ticketed separately as 12 — a real
capital decision cannot responsibly depend on a risk check with no execution-blocking effect, and this
is fixable without waiting for Agent 1 (which is out of scope for this map).

**A second, independently-derived confirmation of the mechanical problem found while resolving ticket
07:** at $1,000 equal-weighted across 15 names ($66.67/name), real August-2026 prices ($87-$493/share)
mean **9 of 15 names cannot be bought as a single whole share.** Carver's own stated minimum is
**$2,500 per instrument** for a small account — 6-8x what this system allocates per name. This and
ticket 07's finding (fixed per-trade commissions consuming 85% of a $1,000 account via monthly
rebalancing) are the same underlying problem seen from two angles: **the current strategy's position
count and rebalance frequency are mechanically mismatched with a $1,000 account, independent of whether
the alpha itself is any good.**

Literature disagreement noted rather than papered over: Carver argues for continuous volatility-targeted
de-risking over a binary halt; the hard-halt design is kept anyway as a deliberate simplicity/
enforceability trade-off for a solo operator, not because the literature prefers it.
