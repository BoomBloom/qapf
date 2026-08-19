# 01 — What drawdown and daily-loss limits bind this system?

**Type:** `wayfinder:grilling`
**Blocked by:** None — can start immediately.
**Status:** CLOSED — grilled and decided, 2026-08-19

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

## Resolution (grilled 2026-08-19)

Three decisions, all confirmed by the operator against the recommendation:

1. **`max_drawdown_pct = 0.20`, `max_daily_loss_pct = 0.06`** — set directly in
   [`backend/risk/__main__.py`](../../../backend/risk/__main__.py), replacing the `None`/`None` TODO that
   had blocked any live assessment since the CRO was built. Verified in isolation: a synthetic drawdown
   breach correctly reports `kill_switch_triggered: true` with `breaches: ["max_drawdown"]`.
2. **Halt behavior: re-validation required, not just human discretion.** When the kill switch trips,
   trading stays halted until the strategy is re-run through the ticket 02 validation bar on fresh data —
   a drawdown breach is treated as evidence the strategy may no longer work, not merely a bad stretch a
   human can wave through. This is now the policy ticket 12's enforcement wiring should implement, not
   just "stop and ask" — see ticket 12's update.
3. **Account size: keep the $1,000 stage-3 target; shrink the strategy to fit, not the other way round.**
   The 9-of-15-names-unbuyable and Carver's ~$2,500/instrument minimum findings are real, but the operator
   chose not to redesign the account size around them — position count / rebalance frequency should adapt
   to $1,000 instead. Logged in the map's fog as a concrete input for whatever ticket 07's attempt 2
   becomes (fewer, cheaper names and/or lower rebalance frequency is now a stated design constraint on
   that redesign, not just a nice-to-have).

**Known follow-on, found while verifying this change, not caused by it:** `python -m risk`'s
`test_fat_tail_relationship` failed on today's live data (historical VaR 0.0253 vs parametric VaR 0.0256,
kurtosis 14.80) — a pre-existing, likely-too-strict assertion, unrelated to the threshold values set here.
Flagged as a separate background task, not part of this ticket's scope.
