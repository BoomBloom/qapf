# 05 — Agent 2: Portfolio Manager — core allocation

**What to build:** Turn Agent 7's per-ticker signals into actual position sizes. Right now the only thing
converting signals into a portfolio is Agent 9's `TopkDropoutStrategy` — buy the top 5, drop the bottom 2,
equal weight — which is a stand-in, not portfolio construction. This ticket makes allocation a real
decision: given a cross-section of signals and an estimated covariance matrix, how much of each name do
we actually hold?

Qlib already provides the machinery, so this is an extension, not a build-from-scratch: `PortfolioOptimizer`
implements global minimum variance, mean-variance, risk parity, and inverse volatility, and
`qlib/model/riskmodel/` provides covariance estimators including Ledoit-Wolf shrinkage. The work is
wiring Agent 7's signals in as the expected-return vector, choosing a covariance estimator, and deciding
which optimizer method applies — plausibly varying by regime, since Agent 6 already labels regimes and a
defensive posture in a contraction is exactly what risk parity is for.

Note a real constraint discovered while reading the source: Qlib's `PortfolioOptimizer` assumes full
investment and **no shorting** (`bounds = Bounds(0.0, 1.0)`). Agent 7 emits signals across `[-1, +1]` and
routinely produces short candidates. That mismatch has to be resolved deliberately — long-only, or extend
the optimizer's bounds — not papered over.

Black-Litterman is deliberately split into ticket 06 so this one stays demoable on its own.

**Blocked by:** None — can start immediately (Agent 7 is built).

**Status:** ready-for-agent

- [ ] Consumes Agent 7's `SignalBundle` and produces position weights that sum to a defined gross
      exposure.
- [ ] Uses a Qlib covariance estimator rather than a naive sample covariance, and the choice is justified.
- [ ] The long-only-vs-shorting question above is explicitly resolved and the resolution is documented.
- [ ] Verified against real data: weights are sane (no single name dominating by accident), and the
      optimizer's own convergence warnings are surfaced rather than swallowed.
- [ ] Agent 9's backtest can optionally run using these weights instead of `TopkDropoutStrategy`, so the
      two allocation approaches are comparable on the same window.
- [ ] Re-read `.claude/references/qlib-known-issues.md` first; confirm (don't assume) that
      `PortfolioOptimizer` is unaffected by the expression-engine bug, since it takes caller-supplied
      arrays rather than evaluating Qlib expressions.
