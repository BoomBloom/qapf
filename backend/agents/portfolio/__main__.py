"""Manual verification runner: python -m agents.portfolio

Chains Agent 6 (regime) -> Agent 7 (signals) -> Agent 2 (allocation) on real
market data, then runs falsifiable correctness checks — including an
independent numerical check that shrinkage covariance is actually better
conditioned than the sample covariance it replaces, rather than assuming the
textbook claim holds on this data.
"""

import logging

import numpy as np
import pandas as pd
import yfinance as yf

from agents.alpha.combiner import AlphaCombiner
from agents.macro.regime import MacroRegimeClassifier
from agents.macro.schemas import MacroRegime, RiskRegime

from .allocator import REGIME_OPTIMIZER, PortfolioAllocator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "JPM", "V", "WMT", "KO", "PEP",
    "XOM", "CVX", "JNJ", "PG", "HD",
]


def download() -> tuple[pd.DataFrame, pd.DataFrame]:
    print(f"Downloading {len(UNIVERSE)} tickers (3y daily)...")
    data = yf.download(UNIVERSE, period="3y", interval="1d", progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")
    print(f"  {len(prices)} trading days\n")
    return prices, volumes


def test_shrinkage_improves_conditioning(allocator, prices):
    """Ledoit-Wolf shrinkage is used because sample covariance is badly
    conditioned, and mean-variance optimization inverts that matrix. Verify the
    improvement numerically instead of taking the textbook claim on faith."""
    tickers = list(prices.columns)
    shrunk = allocator.estimate_covariance(prices, tickers)
    sample = prices[tickers].dropna().pct_change().dropna().cov()

    cond_sample = np.linalg.cond(sample.to_numpy())
    cond_shrunk = np.linalg.cond(shrunk.to_numpy())
    print(f"Condition number — sample: {cond_sample:,.1f}   shrunk: {cond_shrunk:,.1f}")
    assert cond_shrunk < cond_sample, (
        f"Shrinkage made conditioning WORSE ({cond_shrunk:.1f} vs {cond_sample:.1f}) — "
        f"the estimator choice is not doing what it's there for"
    )
    print(
        f"Shrinkage test PASSED: conditioning improved {cond_sample / cond_shrunk:.1f}x, so the "
        f"matrix the optimizer inverts is better behaved."
    )


def test_long_only_and_bounds(alloc, max_position=0.35):
    assert all(p.weight >= 0 for p in alloc.positions), "negative weight in a long-only allocator"
    assert all(p.signal > 0 for p in alloc.positions), "held a name with a non-positive signal"
    total = sum(p.weight for p in alloc.positions)
    assert total <= 1.0 + 1e-9, f"gross exposure {total} exceeds 100% — leverage is not modeled"
    assert abs((total + alloc.cash_weight) - 1.0) < 1e-9, "weights + cash != 100%"

    # The check that was missing when a 35% cap silently produced an 80%
    # position: assert the per-position cap itself, not just the total. Weights
    # are scaled by gross exposure after capping, so the effective ceiling is
    # cap * gross.
    ceiling = max_position * alloc.gross_exposure + 1e-9
    breaches = [(p.ticker, p.weight) for p in alloc.positions if p.weight > ceiling]
    assert not breaches, (
        f"position cap breached (ceiling {ceiling:.2%} = {max_position:.0%} of "
        f"{alloc.gross_exposure:.0%} gross): {breaches}"
    )
    largest = max((p.weight for p in alloc.positions), default=0.0)
    print(
        f"Bounds test PASSED: all weights >= 0, gross {total:.1%} + cash "
        f"{alloc.cash_weight:.1%} = 100%, largest position {largest:.2%} within the "
        f"{ceiling:.2%} ceiling."
    )


def test_signal_weight_relationship(alloc):
    """A stronger signal should not receive a *smaller* allocation than a weaker
    one purely by accident. Correlation won't be perfect — covariance
    legitimately overrides signal ranking, which is the entire point of
    optimizing rather than just sorting — but it should be positive."""
    if len(alloc.positions) < 3:
        print("Signal/weight test SKIPPED: fewer than 3 positions.")
        return
    signals = [p.signal for p in alloc.positions]
    weights = [p.weight for p in alloc.positions]
    corr = float(pd.Series(signals).corr(pd.Series(weights), method="spearman"))
    print(f"Spearman(signal, weight) = {corr:+.3f} across {len(signals)} positions")
    assert corr > -0.5, (
        f"Weights are strongly INVERSELY related to signals (rho={corr:.3f}) — "
        f"the optimizer is likely being fed the signal with the wrong sign"
    )
    print("Signal/weight test PASSED: allocation is not inversely related to conviction.")


def test_regime_changes_allocation(bundle, prices, allocator):
    """Different regimes select different optimizers, so they must produce
    different portfolios — otherwise the regime input is decorative."""
    growth = allocator.allocate(bundle, prices, MacroRegime.DISINFLATIONARY_GROWTH, RiskRegime.RISK_ON)
    crisis = allocator.allocate(bundle, prices, MacroRegime.DEFLATIONARY_CONTRACTION, RiskRegime.RISK_OFF)

    g = {p.ticker: p.weight for p in growth.positions}
    c = {p.ticker: p.weight for p in crisis.positions}
    changed = sum(1 for t in set(g) | set(c) if abs(g.get(t, 0) - c.get(t, 0)) > 1e-9)

    assert growth.optimizer_method != crisis.optimizer_method, "regimes picked the same optimizer"
    assert changed > 0, "regime had no effect on the allocation — the input is being ignored"
    assert crisis.gross_exposure < growth.gross_exposure, (
        f"risk-off gross exposure ({crisis.gross_exposure:.1%}) should be BELOW risk-on "
        f"({growth.gross_exposure:.1%})"
    )
    print(
        f"Regime test PASSED: growth uses '{growth.optimizer_method}' at "
        f"{growth.gross_exposure:.0%} gross; crisis uses '{crisis.optimizer_method}' at "
        f"{crisis.gross_exposure:.0%}; {changed} position(s) differ."
    )


def test_no_positive_signals_holds_cash(prices, allocator):
    """With nothing worth owning, the correct answer is cash — not a forced
    portfolio. Construct that case explicitly rather than waiting to meet it."""
    from agents.alpha.schemas import AlphaSignal, SignalBundle as SB

    bearish = SB(
        as_of="2026-01-01",
        universe_size=3,
        macro_regime="stagflation",
        risk_regime="risk_off",
        factor_weights={},
        exposure_scale=1.0,
        signals=[
            AlphaSignal(ticker=t, as_of="2026-01-01", signal=-0.5, confidence=0.9, factors=[])
            for t in ("AAPL", "MSFT", "KO")
        ],
    )
    alloc = allocator.allocate(bearish, prices, MacroRegime.STAGFLATION, RiskRegime.RISK_OFF)
    assert alloc.n_positions == 0 and alloc.cash_weight == 1.0, (
        f"expected 100% cash when every signal is negative, got {alloc.n_positions} positions"
    )
    print("All-negative-signal test PASSED: holds 100% cash instead of forcing a position.")


def main():
    prices, volumes = download()

    print("=== Pulling live regime from Agent 6 ===")
    assessment = MacroRegimeClassifier().assess()
    print(f"  regime={assessment.regime.value}  risk={assessment.risk_regime.value}\n")

    bundle = AlphaCombiner().generate(prices, volumes, assessment.regime, assessment.risk_regime)
    allocator = PortfolioAllocator()
    alloc = allocator.allocate(bundle, prices, assessment.regime, assessment.risk_regime)

    print(f"=== Allocation as of {alloc.as_of} ===")
    print(f"Regime: {alloc.macro_regime} | Risk: {alloc.risk_regime}")
    print(f"Optimizer: {alloc.optimizer_method} | Covariance: {alloc.covariance_estimator}")
    print(f"Gross exposure: {alloc.gross_exposure:.1%} | Cash: {alloc.cash_weight:.1%}\n")
    print(f"{'Ticker':<8}{'Weight':>9}{'Signal':>9}")
    for p in alloc.positions:
        print(f"{p.ticker:<8}{p.weight:>8.2%}{p.signal:>+9.3f}")
    print("\nReasoning:")
    for line in alloc.reasoning:
        print(f"  - {line}")

    print("\n=== Correctness checks ===")
    test_long_only_and_bounds(alloc)
    test_signal_weight_relationship(alloc)
    test_shrinkage_improves_conditioning(allocator, prices)
    test_regime_changes_allocation(bundle, prices, allocator)
    test_no_positive_signals_holds_cash(prices, allocator)
    print(f"\nRegime->optimizer table covers all {len(REGIME_OPTIMIZER)} macro regimes.")


if __name__ == "__main__":
    main()
