"""Manual verification runner: python -m agents.operations"""

import logging

import pandas as pd
import yfinance as yf

from agents.alpha.combiner import AlphaCombiner
from agents.execution.planner import ExecutionPlanner
from agents.macro.regime import MacroRegimeClassifier
from agents.portfolio.allocator import PortfolioAllocator

from .reconciler import OperationsReconciler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

UNIVERSE = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "JPM", "V", "WMT",
            "KO", "PEP", "XOM", "CVX", "JNJ", "PG", "HD"]
PORTFOLIO_VALUE = 1_000_000


def test_attribution_is_an_identity():
    """alpha + execution + drift must equal total PnL exactly. This is
    arithmetic, not an estimate — if it doesn't close, a PnL source is
    unaccounted for and every attribution number is suspect."""
    rec = OperationsReconciler()
    report = rec.reconcile(
        target_weights={"AAPL": 0.5, "MSFT": 0.5},
        actual_weights={"AAPL": 0.45, "MSFT": 0.52},
        period_returns={"AAPL": 0.02, "MSFT": -0.01},
        execution_cost=500.0,
        portfolio_value=1_000_000,
        as_of="2026-08-19",
    )
    assert abs(report.attribution_residual) < 1e-6, (
        f"attribution does not close: residual ${report.attribution_residual:,.2f} — "
        f"a PnL source is unaccounted for"
    )
    print(f"Attribution-identity test PASSED: alpha ${report.alpha_pnl:,.0f} + execution "
          f"${report.execution_cost:,.0f} + drift ${report.drift_pnl:,.0f} = total "
          f"${report.total_pnl:,.0f} (residual ${report.attribution_residual:.6f}).")


def test_distinguishes_explained_from_unexplained_drift():
    """Drift caused by a known constraint is the system working; unexplained
    drift is a bug. Conflating them makes the report useless."""
    rec = OperationsReconciler(drift_tolerance=0.005)
    report = rec.reconcile(
        target_weights={"AAPL": 0.30, "KO": 0.30, "PG": 0.30},
        actual_weights={"AAPL": 0.10, "KO": 0.302, "PG": 0.15},  # AAPL constrained, PG is not
        period_returns={"AAPL": 0.0, "KO": 0.0, "PG": 0.0},
        execution_cost=0.0,
        portfolio_value=1_000_000,
        as_of="2026-08-19",
        constrained_tickers={"AAPL"},
    )
    by_ticker = {p.ticker: p.drift_reason for p in report.positions}
    assert "expected" in by_ticker["AAPL"], "constrained drift wrongly flagged as unexplained"
    assert "UNEXPLAINED" in by_ticker["PG"], "unexplained drift was NOT flagged"
    assert "tolerance" in by_ticker["KO"], "tiny drift should be within tolerance"
    print("Drift-classification test PASSED: constrained drift accepted, small drift tolerated, "
          "unexplained drift flagged.")


def test_flags_costs_exceeding_alpha():
    """A strategy whose trading costs exceed its gross alpha is unprofitable —
    that must be stated, not left for the reader to infer."""
    rec = OperationsReconciler()
    report = rec.reconcile(
        target_weights={"AAPL": 1.0},
        actual_weights={"AAPL": 1.0},
        period_returns={"AAPL": 0.0001},   # tiny gain
        execution_cost=5_000.0,            # large cost
        portfolio_value=1_000_000,
        as_of="2026-08-19",
    )
    assert any("exceeds gross alpha" in f for f in report.findings), (
        f"did not flag costs exceeding alpha: {report.findings}"
    )
    print("Cost-vs-alpha test PASSED: flagged that execution cost exceeds gross alpha.")


def main():
    print("=== Agent 12 — Operations & Settlement ===\n")
    print("Correctness checks:")
    test_attribution_is_an_identity()
    test_distinguishes_explained_from_unexplained_drift()
    test_flags_costs_exceeding_alpha()

    print("\n=== Live reconciliation on the real pipeline ===")
    data = yf.download(UNIVERSE, period="3y", interval="1d", progress=False, auto_adjust=True)
    prices, volumes = data["Close"].dropna(how="all"), data["Volume"].dropna(how="all")

    assessment = MacroRegimeClassifier().assess()
    bundle = AlphaCombiner().generate(prices, volumes, assessment.regime, assessment.risk_regime)
    alloc = PortfolioAllocator().allocate(bundle, prices, assessment.regime, assessment.risk_regime)
    plan = ExecutionPlanner(algo="vwap").plan(alloc, prices, volumes, PORTFOLIO_VALUE)

    targets = {p.ticker: p.weight for p in alloc.positions}
    # Simulate realistic fills: whole-share rounding leaves small residuals.
    actual = {}
    for o in plan.orders:
        filled_shares = float(int(o.shares))  # can't buy fractional shares
        actual[o.ticker] = filled_shares * o.reference_price / PORTFOLIO_VALUE
    period_returns = prices.pct_change().iloc[-1].to_dict()

    report = OperationsReconciler().reconcile(
        target_weights=targets,
        actual_weights=actual,
        period_returns=period_returns,
        execution_cost=plan.total_cost,
        portfolio_value=PORTFOLIO_VALUE,
        as_of=alloc.as_of,
    )

    print(f"\nPortfolio ${report.portfolio_value:,.0f} | positions {report.n_positions} | "
          f"total |drift| {report.total_drift_abs:.3%} | max {report.max_single_drift:.3%}")
    print(f"\n{'Ticker':<8}{'Target':>9}{'Actual':>9}{'Drift':>9}  Reason")
    for p in report.positions:
        print(f"{p.ticker:<8}{p.target_weight:>9.2%}{p.actual_weight:>9.2%}{p.drift:>+9.3%}  "
              f"{p.drift_reason}")

    print(f"\nPnL attribution:")
    print(f"  alpha (intended portfolio) : ${report.alpha_pnl:>12,.2f}")
    print(f"  execution cost             : ${report.execution_cost:>12,.2f}")
    print(f"  drift (actual vs intended) : ${report.drift_pnl:>12,.2f}")
    print(f"  {'-' * 44}")
    print(f"  total                      : ${report.total_pnl:>12,.2f}")
    print(f"  residual (must be ~0)      : ${report.attribution_residual:>12,.6f}")

    print("\nFindings:")
    for f in report.findings:
        print(f"  - {f}")

    assert abs(report.attribution_residual) < 1e-6, "live attribution failed to close"
    print("\nLive attribution closes exactly.")


if __name__ == "__main__":
    main()
