"""Manual verification runner: python -m risk

Note on qlib: backend/risk/'s actual source (metrics.py, monitor.py) imports
nothing but numpy/pandas/scipy/pydantic -- no qlib, no LangGraph, matching the
isolation rule. This runner separately reuses Agent 9's real backtest
(agents.backtest) ONLY to generate a real-world return series to test against
-- that's a test-fixture dependency, not a dependency of the risk engine
itself. Needs the `if __name__ == "__main__":` guard because that reused path
touches qlib (see .claude/references/qlib-known-issues.md).
"""

import ast
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from . import metrics
from .monitor import RiskMonitor
from .schemas import RiskLimits

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def test_import_isolation():
    """The architecturally critical check: nothing under backend/risk/ may
    import backend.core or any LangGraph module. Parses the AST rather than
    grepping text, so a forbidden import can't hide behind a comment or a
    string that merely mentions "langgraph"."""
    risk_dir = Path(__file__).parent
    forbidden_prefixes = ("core", "backend.core", "langgraph")
    violations = []

    for py_file in risk_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(), filename=str(py_file))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if any(name == p or name.startswith(p + ".") for p in forbidden_prefixes):
                    violations.append(f"{py_file.name}: imports '{name}'")

    assert not violations, (
        f"CRO ISOLATION VIOLATED -- backend/risk/ must never import backend.core "
        f"or LangGraph: {violations}"
    )
    print(
        f"Import-isolation test PASSED: scanned {len(list(risk_dir.glob('*.py')))} "
        f"files under backend/risk/, none import backend.core or langgraph."
    )


def test_analytical_var():
    """Check parametric_var's FORMULA against an independently-computed
    closed-form answer, given the same inputs.

    Deliberately does NOT compare against the true population mu/sigma used to
    generate the synthetic sample -- a finite random draw's sample mean/std
    never exactly equals the population parameters it was drawn from (that gap
    is sampling noise, not a bug), so asserting those match to 1e-9 would be
    testing the wrong thing. What's actually being verified: given a sample's
    OWN mean/std, does parametric_var compute mu + z*sigma correctly.
    """
    rng = np.random.default_rng(7)
    synthetic = pd.Series(rng.normal(0.0005, 0.015, 5000))

    computed = metrics.parametric_var(synthetic, confidence=0.95)

    sample_mu, sample_sigma = synthetic.mean(), synthetic.std(ddof=1)
    z = sp_stats.norm.ppf(0.05)
    expected = -(sample_mu + z * sample_sigma)  # same formula, computed independently here

    assert abs(computed - expected) < 1e-9, (
        f"parametric_var disagrees with the closed-form formula given the same "
        f"sample statistics: {computed} vs {expected}"
    )
    print("Analytical VaR test PASSED: parametric_var's formula matches an independent closed-form computation.")


def test_fat_tail_relationship(returns: pd.Series):
    """Historical VaR should exceed parametric VaR on real (fat-tailed) data --
    verified against real KO/AAPL-style daily returns, not asserted as a fact."""
    hist = metrics.historical_var(returns, confidence=0.95)
    param = metrics.parametric_var(returns, confidence=0.95)
    kurt = float(sp_stats.kurtosis(returns.dropna(), fisher=False))

    print(
        f"Real-data kurtosis: {kurt:.2f} (normal distribution = 3.0) -- "
        f"historical VaR {hist:.4f} vs parametric VaR {param:.4f}"
    )
    assert hist > param, (
        f"Expected historical VaR ({hist:.4f}) > parametric VaR ({param:.4f}) on "
        f"fat-tailed data (kurtosis {kurt:.2f}) -- parametric should understate tail risk"
    )
    print("Fat-tail test PASSED: historical VaR exceeds parametric VaR, as fat tails predict.")


def test_against_agent9_backtest():
    """Regenerate Agent 9's real 2018-2020 backtest and cross-check: an
    INDEPENDENTLY implemented max_drawdown here should match the number Agent
    9's own report computes internally."""
    import qlib

    from agents.backtest.__main__ import DOWNLOAD_START, TEST_END, TEST_START, download_universe
    from agents.backtest.walkforward import WalkForwardBacktester

    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")
    prices, volumes = download_universe(DOWNLOAD_START, TEST_END)
    report, daily_returns = WalkForwardBacktester().run(
        prices, volumes, test_start=TEST_START, test_end=TEST_END
    )

    our_max_dd = metrics.max_drawdown(daily_returns)
    print(
        f"Agent 9 reported max drawdown: {report.max_drawdown:.4f}  |  "
        f"backend/risk/metrics.py independently computed: {our_max_dd:.4f}"
    )
    assert abs(our_max_dd - report.max_drawdown) < 1e-6, (
        f"Drawdown calculations disagree: risk/metrics.py={our_max_dd} vs "
        f"Agent 9's own report={report.max_drawdown}"
    )
    print("Cross-agent consistency test PASSED: two independent drawdown implementations agree exactly.")
    return daily_returns


def show_kill_switch_tradeoff(returns: pd.Series):
    """Illustrate what the kill switch would have done under two different
    drawdown limits against the REAL COVID crash data, so the actual limit
    choice below is made with a concrete picture, not a guess."""
    print("\n=== Kill-switch behavior under two illustrative limits (real COVID-crash data) ===")
    for dd_limit in (0.15, 0.25):
        monitor = RiskMonitor(RiskLimits(max_drawdown_pct=dd_limit, max_daily_loss_pct=0.05))
        history = monitor.assess_history(returns)
        breach_dates = [a.as_of for a in history if a.kill_switch_triggered]
        first_breach = breach_dates[0] if breach_dates else None
        print(
            f"  max_drawdown_pct={dd_limit:.0%}: "
            f"{'would have triggered on ' + first_breach if first_breach else 'never triggered'} "
            f"({len(breach_dates)} of {len(history)} days in breach)"
        )


def main():
    print("=== CRO (Agent 10) verification ===\n")
    test_import_isolation()
    test_analytical_var()

    print("\n=== Cross-checking against Agent 9's real backtest (this takes ~30-60s) ===")
    daily_returns = test_against_agent9_backtest()
    test_fat_tail_relationship(daily_returns)

    show_kill_switch_tradeoff(daily_returns)

    # --- TODO (yours to set): the actual risk limits ---
    # These two numbers are a risk-appetite decision, not a technical one --
    # see the illustration above for what each choice would actually have done
    # against the real 2018-2020 COVID-crash backtest. Pick values and this
    # will report today's live assessment against them.
    max_drawdown_pct = None  # e.g. 0.20 for "halt at 20% drawdown from peak"
    max_daily_loss_pct = None  # e.g. 0.05 for "halt on any single day worse than -5%"

    if max_drawdown_pct is None or max_daily_loss_pct is None:
        print(
            "\nSet max_drawdown_pct and max_daily_loss_pct in __main__.py (see the "
            "TODO above) to run a live assessment against your own limits."
        )
        return

    monitor = RiskMonitor(RiskLimits(max_drawdown_pct=max_drawdown_pct, max_daily_loss_pct=max_daily_loss_pct))
    assessment = monitor.assess(daily_returns)
    print(f"\n=== Assessment as of {assessment.as_of} against your limits ===")
    print(assessment.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
