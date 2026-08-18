"""Agent 2 — Portfolio Manager & Allocation.

Turns Agent 7's cross-section of alpha signals into actual position sizes,
replacing Agent 9's `TopkDropoutStrategy` placeholder (buy top 5, drop bottom
2, equal weight) with real portfolio construction.

Extends Qlib rather than reimplementing it, per the roster's "Extend Qlib"
call: `PortfolioOptimizer` supplies gmv/mvo/rp/inv and
`model/riskmodel/ShrinkCovEstimator` supplies Ledoit-Wolf shrinkage. Qlib is
imported directly here rather than via a `backend/services/` wrapper, matching
Agent 9's actual precedent (see CLAUDE.md, "Where new code goes").

TWO DELIBERATE DECISIONS, both flagged in ticket 05 as needing a real choice:

1. LONG-ONLY. Qlib's `PortfolioOptimizer` hard-codes `Bounds(0.0, 1.0)` — no
   shorting — while Agent 7 emits signals across [-1, +1] and routinely
   produces short candidates. Rather than silently dropping the shorts or
   silently extending the bounds, this allocator is explicitly long-only:
   negative-signal names receive zero weight and their capital stays in cash.
   Rationale: shorting needs borrow availability, margin, and its own risk
   treatment — none of which exist in this system yet (Agent 16, Treasury &
   Funding, is deliberately deferred). Agent 9's backtest is long-only too, so
   this keeps the two consistent. Reversible: extending to long/short means
   changing the bounds and adding a margin model, not restructuring this.

2. SIGNALS ARE SCORES, NOT EXPECTED RETURNS. A rank-normalized signal in
   [-1, +1] is not a return forecast, and mean-variance optimization formally
   wants the latter. Qlib's optimizer partially absorbs this: with
   `scale_return=True` (its default) it rescales `r` to the average asset
   volatility before optimizing, which is exactly the "I have a score, not a
   forecast" case. That makes this defensible for now but not rigorous —
   ticket 06 (Black-Litterman) is what makes the inputs principled.
"""

import logging

import numpy as np
import pandas as pd
from qlib.contrib.strategy.optimizer.optimizer import PortfolioOptimizer
from qlib.model.riskmodel.shrink import ShrinkCovEstimator

from agents.alpha.schemas import SignalBundle
from agents.macro.schemas import MacroRegime, RiskRegime

from .schemas import PortfolioAllocation, PositionWeight

logger = logging.getLogger(__name__)

# Regime -> optimizer method. Mirrors the premise Agent 7 already encodes in its
# factor weights: lean into return-seeking when growth expands, get defensive
# when it contracts. Hand-set priors, deliberately auditable rather than fitted
# (Agent 14's job is to attack them).
REGIME_OPTIMIZER: dict[MacroRegime, str] = {
    MacroRegime.INFLATIONARY_EXPANSION: PortfolioOptimizer.OPT_MVO,
    MacroRegime.DISINFLATIONARY_GROWTH: PortfolioOptimizer.OPT_MVO,
    MacroRegime.STAGFLATION: PortfolioOptimizer.OPT_RP,
    MacroRegime.DEFLATIONARY_CONTRACTION: PortfolioOptimizer.OPT_GMV,
}

# Gross exposure by risk regime — how much capital is deployed at all. Distinct
# from Agent 7's signal scaling: that shrinks conviction, this shrinks capital.
RISK_GROSS_EXPOSURE: dict[RiskRegime, float] = {
    RiskRegime.RISK_ON: 1.0,
    RiskRegime.NEUTRAL: 0.8,
    RiskRegime.RISK_OFF: 0.5,
}

MIN_SIGNAL_FOR_INCLUSION = 0.0  # long-only: only positive-signal names are held


def _cap_and_redistribute(weights: pd.Series, cap: float, max_iters: int = 100) -> pd.Series:
    """Enforce a per-position cap while preserving the total.

    Clipping then renormalizing does NOT work and silently undoes the cap: if
    one name holds everything, clipping leaves it as the only nonzero weight,
    and dividing by the new sum returns it straight to 1.0. (This was a real
    bug here — a 35% cap produced an 80% position.) Instead, water-fill: cap
    the offenders, hand their excess to the names still under the cap, and
    repeat until nothing exceeds it.

    If every name is at the cap the total can't be preserved (n * cap < 1); the
    weights are returned at the cap and the caller reports the lower gross
    exposure honestly rather than inflating positions past the limit.
    """
    w = weights.clip(lower=0.0).astype(float).copy()
    if w.sum() <= 0:
        return w

    for _ in range(max_iters):
        over = w > cap + 1e-12
        if not over.any():
            break
        excess = float((w[over] - cap).sum())
        w[over] = cap
        room = (cap - w) > 1e-12
        room &= ~over
        if not room.any() or w[room].sum() <= 0:
            break  # nowhere left to put it; total will fall short, reported as cash
        w[room] += excess * (w[room] / w[room].sum())

    return w.clip(upper=cap)


class PortfolioAllocator:
    def __init__(self, shrinkage: str = "lw"):
        """`shrinkage='lw'` = Ledoit-Wolf. Sample covariance is badly
        conditioned when the number of assets approaches the number of
        observations, and inverting a badly conditioned matrix is exactly what
        mean-variance optimization does — so shrinkage is the standard fix, not
        a refinement. `__main__.py` verifies the conditioning improvement
        numerically rather than asserting it."""
        self.cov_estimator = ShrinkCovEstimator(alpha=shrinkage)
        self.shrinkage = shrinkage

    def estimate_covariance(self, prices: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
        """Shrinkage covariance of daily returns for `tickers`."""
        px = prices[tickers].dropna()
        cov = self.cov_estimator.predict(px, is_price=True)
        if isinstance(cov, np.ndarray):
            cov = pd.DataFrame(cov, index=tickers, columns=tickers)
        return cov

    def allocate(
        self,
        bundle: SignalBundle,
        prices: pd.DataFrame,
        macro_regime: MacroRegime,
        risk_regime: RiskRegime,
        max_position: float = 0.35,
    ) -> PortfolioAllocation:
        """Produce target weights from a signal bundle.

        `max_position` caps any single name so one extreme signal can't become
        the whole portfolio — a concentration guard the optimizer's own
        constraints don't provide.
        """
        reasoning: list[str] = []

        candidates = [s for s in bundle.signals if s.signal > MIN_SIGNAL_FOR_INCLUSION]
        excluded = len(bundle.signals) - len(candidates)
        if excluded:
            reasoning.append(
                f"{excluded} name(s) with non-positive signals excluded — this allocator is "
                f"long-only (see module docstring); their capital stays in cash."
            )

        method = REGIME_OPTIMIZER[macro_regime]
        gross = RISK_GROSS_EXPOSURE[risk_regime]
        reasoning.append(f"Regime {macro_regime.value} -> optimizer '{method}'.")
        reasoning.append(f"Risk regime {risk_regime.value} -> gross exposure {gross:.0%}.")

        if not candidates:
            reasoning.append("No positive signals — holding 100% cash rather than forcing a position.")
            return PortfolioAllocation(
                as_of=bundle.as_of,
                macro_regime=macro_regime.value,
                risk_regime=risk_regime.value,
                optimizer_method=method,
                covariance_estimator=f"shrink({self.shrinkage})",
                gross_exposure=0.0,
                cash_weight=1.0,
                n_positions=0,
                positions=[],
                reasoning=reasoning,
            )

        tickers = [s.ticker for s in candidates]
        available = [t for t in tickers if t in prices.columns]
        if len(available) < len(tickers):
            missing = set(tickers) - set(available)
            reasoning.append(f"Dropped {sorted(missing)} — no price history to estimate covariance.")
            candidates = [s for s in candidates if s.ticker in available]
            tickers = available

        if len(tickers) == 1:
            # A single name has no cross-sectional covariance structure to
            # optimize over; the optimizer would be meaningless here.
            reasoning.append("Only one candidate — allocating the full gross exposure to it.")
            weights = pd.Series([1.0], index=tickers)
        else:
            cov = self.estimate_covariance(prices, tickers)
            optimizer = PortfolioOptimizer(method=method)
            signal_scores = pd.Series({s.ticker: s.signal for s in candidates})[tickers]
            # `r` is only consumed by MVO; gmv/rp ignore it (and warn if passed).
            r = signal_scores.to_numpy() if method == PortfolioOptimizer.OPT_MVO else None
            weights = optimizer(S=cov, r=r)
            if isinstance(weights, np.ndarray):
                weights = pd.Series(weights, index=tickers)

        n_over = int((weights > max_position + 1e-9).sum())
        weights = _cap_and_redistribute(weights, max_position)
        if n_over:
            reasoning.append(
                f"Capped {n_over} position(s) at {max_position:.0%} and redistributed the excess "
                f"to uncapped names, to limit single-name concentration."
            )
        weights = weights * gross

        signal_by_ticker = {s.ticker: s.signal for s in candidates}
        positions = [
            PositionWeight(ticker=t, weight=float(w), signal=float(signal_by_ticker[t]))
            for t, w in weights.items()
            if w > 1e-6
        ]
        positions.sort(key=lambda p: p.weight, reverse=True)

        deployed = float(sum(p.weight for p in positions))
        return PortfolioAllocation(
            as_of=bundle.as_of,
            macro_regime=macro_regime.value,
            risk_regime=risk_regime.value,
            optimizer_method=method,
            covariance_estimator=f"shrink({self.shrinkage})",
            gross_exposure=deployed,
            cash_weight=float(1.0 - deployed),
            n_positions=len(positions),
            positions=positions,
            reasoning=reasoning,
        )
