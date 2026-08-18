# 04 — Agent 14: Model Risk & Independent Validation

**What to build:** An independent challenge to the backtest result — answering "could this model be
systematically wrong in ways a backtest can't reveal?" rather than Agent 9's "did this backtest perform
well?" Those are different questions, and in a real institution they're deliberately answered by
different teams so the people who built the model aren't the only ones grading it.

Concretely, this means testing the strategy for failure modes that a single good-looking backtest hides:
regime-shift blindness (validated in one regime, silently assumed to hold in an unseen one), performance
decay over time (does the edge shrink across sub-periods, or is it front-loaded into one lucky stretch?),
and out-of-distribution inputs (what happens when a factor value lands far outside anything in the
training window?).

There is a live example to work against: Agent 9's real 2018-2020 walk-forward result underperformed its
own equal-weight benchmark (+27.54% vs +50.98%) with a Deflated Sharpe of 0.414 — not significant. This
agent should be able to say something more useful about *why* than "the number was low." Note also that
Agent 7's regime-conditional factor weights are hand-set priors, never fitted — a specific, checkable
hypothesis this agent is well placed to attack.

Agent 9's `WalkForwardBacktester.run()` now returns `(report, daily_returns)`, so the raw return series
is available without re-deriving it.

**Blocked by:** None — can start immediately (Agent 9 is built).

**Status:** ready-for-agent

- [ ] Reports strategy performance split by macro regime, not just in aggregate — Agent 6 already labels
      every historical date with a regime.
- [ ] Tests for decay: does performance differ materially across sub-periods of the backtest window?
- [ ] Flags out-of-distribution factor inputs rather than silently extrapolating through them.
- [ ] Reaches a verdict on Agent 7's hand-set regime weights specifically: is there evidence they add
      value over a naive equal-weighting of the same factors?
- [ ] Structurally independent of Agent 9 — its own module, its own reasoning, not a wrapper that
      re-reports Agent 9's numbers.
- [ ] Reports an unflattering conclusion plainly if that's what the data says, matching how Agent 9's own
      underperformance was recorded rather than buried.
