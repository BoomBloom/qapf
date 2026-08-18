"""Manual verification runner: python -m agents.execution

Chains Agent 6 -> 7 -> 2 -> 11 on real market data, then checks the cost model
behaves the way microstructure theory says it must — rather than assuming a
plausible-looking number is right.
"""

import logging

import pandas as pd
import yfinance as yf

from agents.alpha.combiner import AlphaCombiner
from agents.macro.regime import MacroRegimeClassifier
from agents.portfolio.allocator import PortfolioAllocator

from .planner import ExecutionPlanner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

UNIVERSE = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "JPM", "V", "WMT",
            "KO", "PEP", "XOM", "CVX", "JNJ", "PG", "HD"]
PORTFOLIO_VALUE = 1_000_000


def test_larger_orders_cost_more_per_share(alloc, prices, volumes):
    """Square-root impact means a bigger order costs MORE IN TOTAL but LESS
    PER SHARE at the margin. Verify the total-cost direction, which is the
    property that matters for sizing."""
    planner = ExecutionPlanner(algo="twap")
    small = planner.plan(alloc, prices, volumes, portfolio_value=1_000_000)
    large = planner.plan(alloc, prices, volumes, portfolio_value=100_000_000)

    assert large.total_cost > small.total_cost, "a 100x larger portfolio should cost more to trade"
    assert large.cost_bps > small.cost_bps, (
        f"cost in bps should RISE with size under square-root impact "
        f"({large.cost_bps:.1f}bp vs {small.cost_bps:.1f}bp) — otherwise impact isn't size-dependent"
    )
    print(f"Size test PASSED: $1M portfolio costs {small.cost_bps:.2f}bp; $100M costs "
          f"{large.cost_bps:.2f}bp — impact scales with size, as the square-root law requires.")


def test_scheduling_beats_immediate(alloc, prices, volumes):
    """Splitting an order across the day must cost less than firing it all at
    once — if it doesn't, the scheduling logic is doing nothing."""
    immediate = ExecutionPlanner(algo="immediate").plan(
        alloc, prices, volumes, portfolio_value=100_000_000)
    twap = ExecutionPlanner(algo="twap").plan(
        alloc, prices, volumes, portfolio_value=100_000_000)
    vwap = ExecutionPlanner(algo="vwap").plan(
        alloc, prices, volumes, portfolio_value=100_000_000)

    assert twap.total_cost < immediate.total_cost, (
        f"TWAP ({twap.total_cost:,.0f}) should cost less than immediate "
        f"({immediate.total_cost:,.0f})"
    )
    saving = 1 - twap.total_cost / immediate.total_cost
    print(f"Scheduling test PASSED: immediate {immediate.cost_bps:.1f}bp -> TWAP "
          f"{twap.cost_bps:.1f}bp ({saving:.0%} saved) -> VWAP {vwap.cost_bps:.1f}bp.")
    if vwap.total_cost < twap.total_cost:
        print("  VWAP also beats TWAP by trading more when volume is heaviest.")


def test_orders_are_deltas_not_targets(alloc, prices, volumes):
    """Executing target weights instead of deltas would re-buy the entire
    portfolio every rebalance. Verify that already-held positions generate no
    order."""
    planner = ExecutionPlanner()
    held = {p.ticker: p.weight for p in alloc.positions}
    plan = planner.plan(alloc, prices, volumes, PORTFOLIO_VALUE, current_weights=held)
    assert plan.n_orders == 0, (
        f"already holding the target portfolio should produce 0 orders, got {plan.n_orders} "
        f"— the planner is trading targets rather than deltas"
    )
    print("Delta test PASSED: holding the target portfolio produces zero orders.")


def test_liquidity_matters(prices, volumes):
    """The same dollar order in a thinly traded name must cost more than in a
    liquid one. Compares the two extremes of the real universe."""
    planner = ExecutionPlanner(algo="twap")
    avg_vol_notional = (volumes.iloc[-20:].mean() * prices.iloc[-1])
    liquid, thin = avg_vol_notional.idxmax(), avg_vol_notional.idxmin()

    from agents.portfolio.schemas import PortfolioAllocation, PositionWeight

    def one_name_plan(tkr):
        a = PortfolioAllocation(
            as_of="2026-01-01", macro_regime="x", risk_regime="y", optimizer_method="mvo",
            covariance_estimator="test", gross_exposure=0.1, cash_weight=0.9, n_positions=1,
            positions=[PositionWeight(ticker=tkr, weight=0.1, signal=0.5)], reasoning=[],
        )
        return planner.plan(a, prices, volumes, portfolio_value=50_000_000)

    lp, tp = one_name_plan(liquid), one_name_plan(thin)
    assert tp.cost_bps > lp.cost_bps, (
        f"the thin name ({thin}, {tp.cost_bps:.1f}bp) should cost more than the liquid one "
        f"({liquid}, {lp.cost_bps:.1f}bp)"
    )
    print(f"Liquidity test PASSED: same $5M order costs {lp.cost_bps:.1f}bp in {liquid} "
          f"(most liquid) vs {tp.cost_bps:.1f}bp in {thin} (least liquid).")


def main():
    print(f"Downloading {len(UNIVERSE)} tickers (3y daily)...")
    data = yf.download(UNIVERSE, period="3y", interval="1d", progress=False, auto_adjust=True)
    prices, volumes = data["Close"].dropna(how="all"), data["Volume"].dropna(how="all")
    print(f"  {len(prices)} trading days\n")

    assessment = MacroRegimeClassifier().assess()
    bundle = AlphaCombiner().generate(prices, volumes, assessment.regime, assessment.risk_regime)
    alloc = PortfolioAllocator().allocate(bundle, prices, assessment.regime, assessment.risk_regime)
    print(f"Agent 2 target portfolio: {alloc.n_positions} positions, "
          f"{alloc.gross_exposure:.0%} gross\n")

    plan = ExecutionPlanner(algo="vwap").plan(alloc, prices, volumes, PORTFOLIO_VALUE)

    print(f"=== Execution plan ({plan.algo.upper()}) on a ${PORTFOLIO_VALUE:,} portfolio ===")
    print(f"Orders: {plan.n_orders} | Gross notional: ${plan.gross_notional:,.0f} "
          f"| Turnover: {plan.turnover:.1%}")
    print(f"Cost: ${plan.total_cost:,.0f} ({plan.cost_bps:.2f}bp) = "
          f"${plan.total_spread_cost:,.0f} spread + ${plan.total_impact_cost:,.0f} impact\n")
    print(f"{'Ticker':<8}{'Side':<6}{'Notional':>12}{'Shares':>10}{'Δweight':>10}")
    for o in plan.orders:
        print(f"{o.ticker:<8}{o.side:<6}{o.notional:>12,.0f}{o.shares:>10,.0f}{o.delta_weight:>+10.2%}")
    print("\nReasoning:")
    for line in plan.reasoning:
        print(f"  - {line}")

    print("\n=== Correctness checks ===")
    test_orders_are_deltas_not_targets(alloc, prices, volumes)
    test_larger_orders_cost_more_per_share(alloc, prices, volumes)
    test_scheduling_beats_immediate(alloc, prices, volumes)
    test_liquidity_matters(prices, volumes)


if __name__ == "__main__":
    main()
