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

## Not yet specified

In scope, but not yet sharp enough to ticket. Graduates as the frontier advances.

- **What happens if the strategy cannot clear the bar.** The most likely outcome, honestly. Searching for
  new alpha is a different effort with a different shape, and cannot be specified until we know *how* it
  failed — statistically insignificant is a different problem from significant-but-unprofitable-after-costs.
- **How paper-trading results get compared against the backtest.** Needs the paper stage to exist first.
  The interesting question is what divergence between paper and backtest would count as disqualifying
  rather than as noise.
- **Live monitoring once real money is on.** Agent 10 halts on limits, but nothing currently tells a human
  that it halted. Shape depends on the broker chosen.
- **Whether the backtest window is long enough to conclude anything.** Three years spanning COVID is thin
  for a regime-conditional strategy — it sees each regime only once. Sharpens once ticket 03 establishes
  what data is actually obtainable.
- **Tax and reporting treatment** of systematic trading in the operator's jurisdiction.

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
