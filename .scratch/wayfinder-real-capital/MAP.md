# MAP — Is QAPF fit to trade real capital?

`wayfinder:map` · charted 2026-08-19 · local-markdown tracker (no issue tracker configured)

## Destination

**A decision on whether this system is fit to trade real capital — and if it is not yet, the specific,
pre-agreed conditions that would make it so.**

Not "finish the 16 agents" and not "make the strategy profitable". Those are candidate routes, not the
destination. The map is done when nothing remains to *decide* before someone goes and does the work.

## Notes

**Domain.** Autonomous multi-agent quant system. 12 of 16 agents built and verified against live data.
Full context in `CLAUDE.md`; agent-by-agent rationale in `README.md`.

**The staged path the operator has chosen** (locked during charting, 2026-08-19):
backtest that clears a bar -> 3 months paper trading -> 3 months with $1,000 real -> then consider
prop-firm funding. Each stage gates the next. No target date, deliberately: date-driven deployment is
how unvalidated strategies reach real money.

**Standing decisions from charting** — settled, not up for re-litigation without new evidence:

- **Validation before capital, not live-fire learning.** No real money until the strategy clears a
  statistical bar agreed in advance. The bar's exact definition is ticket 02.
- **Kill condition, binding.** If live results underperform equal-weight buy-and-hold over 6 months, the
  system stops trading and returns to research. Decided while calm, on purpose.
- **US equities first.** Not because equities are the goal, but because it is the only asset class with a
  working end-to-end pipeline, real data, and a measured baseline. Switching now discards all of it.
- **Risk limits are a design constraint from today**, not a stage-4 concern. The backtest's -36.68% max
  drawdown is unacceptable for a $1,000 account the operator cares about, independent of any prop firm.
- **A kill-switch halt requires re-validation to resume, not human override alone** (ticket 01). Treats a
  live drawdown breach as evidence the strategy may be broken, not just a bad stretch.
- **$1,000 is the fixed real-capital stage-3 target.** The strategy must be redesigned to mechanically fit
  it (fewer/cheaper names, lower rebalance frequency) — the account size itself does not move (ticket 01).

**Skills every session should consult:** `qapf-prime` before touching any agent code.
Qlib gotchas in `.claude/references/qlib-known-issues.md`.

**The uncomfortable fact this map exists to confront:** the machinery works; the strategy does not.
+27.54% against a +50.98% benchmark, Deflated Sharpe 0.414 — not distinguishable from luck. Agent 14
further found the strategy earns Sharpe +1.16 in the regime where Agent 7 goes defensive and -0.32 in
the regime where it bets hardest on momentum, suggesting the hand-set priors may be inverted.

## Decisions so far

<!-- index of closed tickets: one line each, gist + link. Empty at charting. -->

- [02 — What must the strategy prove before real money?](tickets/02-validation-bar.md) — **2008-2017**
  is the validation window (untouched, includes the GFC); post-2020 reserved as a one-look final holdout.
  The bar is **three conditions, all required**: DSR > 0.95, beats equal-weight buy-and-hold
  risk-adjusted, and profitable net of costs at $1,000. **Five attempts**, with `n_trials` incremented
  honestly; exhausting the budget means the approach failed. Shortened the critical path — ticket 07 no
  longer waits on ticket 03.
- [01 — What risk limits bind this system?](tickets/01-risk-limits.md) — **`max_drawdown_pct=0.20`,
  `max_daily_loss_pct=0.06`**, set live in `backend/risk/__main__.py`. Halting requires **re-validation
  against ticket 02's bar** before resuming, not just human discretion (feeds ticket 12). Account size
  stays $1,000 — the strategy shrinks to fit it, not the reverse (feeds ticket 07 attempt 2).
- [10 — Survivorship bias](tickets/10-universe-survivorship-bias.md) — **Fix it properly**, not
  accept-and-document or reduce: build the real point-in-time universe (Qlib's free PIT builder + $9/mo
  Sharadar for delisted names). Does NOT consume a ticket 02 attempt (infrastructure fix, not a strategy
  variant). Must land **before** ticket 07's attempt 2, bundled with ticket 01's fewer/cheaper-names
  redesign since both touch universe composition. Build work spun out as ticket 13, **half done**: real
  point-in-time S&P 500 membership built and verified for free (Lehman Brothers/Fannie Mae/Freddie
  Mac/Wachovia's actual 2008 removals correctly captured — the vendored builder was actually broken
  against the live Wikipedia page, fixed by reading a historical revision instead). Delisted PRICE data
  still needs the operator to personally sign up for Sharadar ($9/mo) — cannot be done on their behalf.
- [07 — Does the strategy clear the bar?](tickets/07-clears-the-bar.md) — **FAILS, attempt 4 of 5. Only
  1 attempt remains.** Trajectory (DSR / Sharpe / return-per-maxDD / max drawdown):
  attempt 1 flat weights 0.9636✓ / 0.564✗ / 1.536✗ / -36.74%;
  attempt 2 + vol-managed exposure 0.9615✓ / 0.726✗ / 2.741✓ / -26.48%;
  attempt 3 + Yang-Zhang range-vol 0.9301✗ / 0.738✗ / 4.182✓ / -17.64%;
  attempt 4 pure low-vol tilt 0.8870✗ / 0.718✗ / 4.060✓ / -17.68%.
  **Two things are now established empirically, not just argued.** (a) DSR became the binding constraint
  and keeps falling as trial count rises faster than Sharpe improves — `viable-alpha-families.md` §0.2's
  trial-count warning, confirmed. (b) Attempt 4's drawdown (-17.68%) is essentially identical to attempt
  3's (-17.64%) despite completely different factor weights, which **isolates the improvement to the
  volatility-management layer, not the cross-sectional factor signal** — confirming §1.2's prediction
  that a 15-name universe is too small for a cross-sectional edge to exist at all. Deliberately still NOT
  combined with ticket 13's PIT-universe fix (incomplete without Sharadar; would conflate variables).
  **Recommendation for the last attempt: spend it on the PIT universe (ticket 13), not another strategy
  variant** — a strategy clearing the bar on survivorship-biased data still couldn't be trusted, so a
  clean answer on honest data is decision-grade either way. Operator's call, not decided.
- [09 — Broker and platform](tickets/09-broker-and-platform.md) — **Interactive Brokers**, connected via
  its own API (TWS/Client Portal), not through TradingView. IBKR turned out to already have a native
  TradingView charting/manual-order panel — the operator's "IBKR or a TradingView broker" framing was a
  false choice — but automation still needs IBKR's own API since Agent 11 already computes real orders
  in Python. Account/API-credential setup is still the operator's own action.
- [11 — Intraday equity tracking](tickets/11-intraday-equity-tracking.md) — **Alpaca (free) for live
  risk monitoring, Alpha Vantage free tier (accepting a ~2-month backfill) for the historical 2008-2017
  re-score** — operator ruled out the $199/mo paid path as too expensive. Neither wired in yet.

## Not yet specified

In scope, but not yet sharp enough to ticket. Graduates as the frontier advances.

- **What attempt 2 (of 5) changes.** Ticket 07's attempt 1 failed cleanly: the signal is statistically real
  (DSR 0.9636) and profitable, but doesn't beat naive buy-and-hold risk-adjusted — a different, more
  specific problem than "insignificant" or "unprofitable after costs" would have been. Points at the
  factor set itself as the lever, not costs or regime-weighting (both already ruled out this session).
  `docs/research/viable-alpha-families.md` has a ranked shortlist (volatility-managed exposure, OHLC
  range-vol estimators, absolute/time-series momentum with a cash leg, risk-based allocation as benchmark,
  meta-labelling) not yet read in full or turned into a concrete attempt-2 plan — the next thing to sharpen
  into a ticket.
- **How paper-trading results get compared against the backtest.** Needs the paper stage to exist first.
  The interesting question is what divergence between paper and backtest would count as disqualifying
  rather than as noise.
- **Live monitoring once real money is on.** Agent 10 halts on limits, but nothing currently tells a human
  that it halted. Shape depends on the broker chosen.
- **Whether the backtest window is long enough to conclude anything.** Three years spanning COVID is thin
  for a regime-conditional strategy — it sees each regime only once. Sharpens once ticket 03 establishes
  what data is actually obtainable.
- **Tax and reporting treatment** of systematic trading in the operator's jurisdiction.
- **Whether the FX ambition should become the funded route.** Ticket 04 showed prop funding fits FX/futures
  on MT5 and not cash equities. That makes the second map (FX/gold) the one that could actually be funded,
  which may change its priority relative to this one. Not sharp enough to ticket until this map's
  destination is reached.

## Out of scope

Ruled beyond this destination. Never graduates; returns only as a fresh effort.

- **FX, gold, and commodities.** Explicitly the operator's next ambition, and explicitly a *second map*.
  These are not four data feeds on one system: Agent 7's factors are cross-sectional (rank 15 comparable
  stocks), which is meaningless for a single instrument like gold and structurally different for FX pairs
  where carry and trend dominate. Closer to four Agent 7s and four Agent 2s sharing the asset-agnostic
  infrastructure beneath. Reuses everything this map proves — which is the argument for finishing this
  one first.
- **Prop-firm funding (FTMO and alternatives).** Stage 4 of the operator's own path, deferred until real
  evidence exists. Research ticket 04 still runs, because its answer could invalidate the destination —
  if no firm permits automated equity trading, the funding route needs rethinking — but *pursuing*
  funding is not part of reaching this destination.
- **Agents 1 (Orchestrator) and 8 (Code Generation).** Both are now unblocked — the Anthropic key is
  funded and one decision costs ~$0.68 — but neither helps answer whether the system is fit for real
  capital. Finishing the roster is not on the critical path to real money. Scoping act, not a judgement
  on their value.
- **Agents 5 (Quantum) and 16 (Treasury).** Already deferred by policy before this map existed.
