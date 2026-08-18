"""Manual verification runner: python -m agents.modelrisk

Runs the real Agent 9 backtest, then independently challenges its result.

Needs the `if __name__ == "__main__":` guard because it reaches Agent 9, which
touches qlib (see .claude/references/qlib-known-issues.md).
"""

import logging

import numpy as np
import pandas as pd
import qlib

from .validator import ModelRiskValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def test_detects_planted_decay():
    """Construct a series whose edge is known to die, and assert the validator
    says so. A detector that never fires on real data proves nothing unless it
    is also shown to fire when the fault is definitely present."""
    idx = pd.date_range("2020-01-01", periods=300, freq="B")
    rng = np.random.default_rng(11)
    good = rng.normal(0.004, 0.01, 150)   # strong positive edge
    dead = rng.normal(-0.004, 0.01, 150)  # edge reversed
    series = pd.Series(np.concatenate([good, dead]), index=idx)

    report = ModelRiskValidator().validate(series)
    decay = [f for f in report.findings if f.category == "decay"]
    assert decay, "planted decay was NOT detected — the decay check is not working"
    assert "NOT TRUSTWORTHY" in report.verdict, f"expected a critical verdict, got: {report.verdict}"
    print(f"Planted-decay test PASSED: detected {len(decay)} decay finding(s) on a series "
          f"whose edge reverses halfway through.")


def test_detects_planted_concentration():
    """Near-flat returns plus five enormous days — concentration far beyond
    what a same-mean/same-vol random series produces, so it must clear the
    statistical null, not just a naive threshold."""
    idx = pd.date_range("2020-01-01", periods=250, freq="B")
    rng = np.random.default_rng(3)
    vals = rng.normal(0.0, 0.001, 250)  # tiny noise, no drift
    vals[[10, 50, 120, 180, 240]] = 0.15  # five days dwarfing everything else
    report = ModelRiskValidator().validate(pd.Series(vals, index=idx))
    # Expects 'warning', not 'critical': concentration is deliberately not a
    # damning verdict, because real returns are fat-tailed and would exceed a
    # Gaussian null almost always (see validator.py's rationale).
    flagged = [
        f for f in report.findings if f.category == "concentration" and f.severity == "warning"
    ]
    assert flagged, (
        f"planted return-concentration was NOT flagged; "
        f"top-5 share was {report.top_5_days_pct_of_return:.1%}"
    )
    print(f"Planted-concentration test PASSED: top 5 days carry "
          f"{report.top_5_days_pct_of_return:.0%} of returns, flagged against the random null.")


def test_clean_series_is_not_flagged():
    """A steady, well-behaved series must NOT trigger critical findings —
    otherwise the validator just condemns everything and carries no signal."""
    idx = pd.date_range("2020-01-01", periods=300, freq="B")
    rng = np.random.default_rng(5)
    steady = pd.Series(rng.normal(0.0006, 0.008, 300), index=idx)
    report = ModelRiskValidator().validate(steady)
    criticals = [f for f in report.findings if f.severity == "critical"]
    assert not criticals, f"clean series wrongly flagged as critical: {[f.finding for f in criticals]}"
    print(f"False-positive test PASSED: a steady series draws no critical findings "
          f"(verdict: {report.verdict.split('—')[0].strip()}).")


def main():
    print("=== Agent 14 — Model Risk & Independent Validation ===\n")
    print("Self-tests against planted faults (the detector must fire when the fault IS present):")
    test_detects_planted_decay()
    test_detects_planted_concentration()
    test_clean_series_is_not_flagged()

    print("\n=== Now challenging Agent 9's REAL backtest ===")
    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")

    from agents.backtest.__main__ import DOWNLOAD_START, TEST_END, TEST_START, download_universe
    from agents.backtest.walkforward import WalkForwardBacktester

    prices, volumes = download_universe(DOWNLOAD_START, TEST_END)
    bt = WalkForwardBacktester()
    report9, daily_returns = bt.run(prices, volumes, test_start=TEST_START, test_end=TEST_END)

    # Agent 6 labels every rebalance date with the regime that was live then;
    # forward-fill gives every trading day a regime for coverage analysis.
    regime_by_date = {
        pd.Timestamp(rec.date): rec.regime for rec in report9.rebalance_log
    }

    report = ModelRiskValidator().validate(daily_returns, regime_by_date=regime_by_date)

    print(f"\nAgent 9 reported: {report9.total_return:+.2%} total, "
          f"Sharpe {report9.annualized_sharpe:.3f}, DSR {report9.deflated_sharpe_ratio:.3f}")
    print(f"Agent 14 independent view over {report.n_observations} days:\n")

    print("Sub-period stability:")
    for sp in report.sub_periods:
        print(f"  {sp.label} {sp.start}..{sp.end}  return={sp.total_return:+7.2%}  "
              f"Sharpe={sp.annualized_sharpe:+.2f}  maxDD={sp.max_drawdown:.2%}")
    print(f"  Sharpe dispersion across periods: {report.sharpe_dispersion:.3f}")

    if report.regime_performance:
        print("\nPerformance by macro regime:")
        for rp in report.regime_performance:
            print(f"  {rp.regime:<28} {rp.n_days:>4}d  return={rp.total_return:+7.2%}  "
                  f"Sharpe={rp.annualized_sharpe:+.2f}")
    if report.regimes_never_tested:
        print(f"  NEVER TESTED: {', '.join(report.regimes_never_tested)}")

    print(f"\nReturn concentration: top 5 days = {report.top_5_days_pct_of_return:.1%} of summed "
          f"returns; without them the result is {report.return_without_top_5_days:+.2%}")

    print("\nFindings:")
    for f in report.findings:
        print(f"  [{f.severity.upper():<8}] ({f.category}) {f.finding}")

    print(f"\nVERDICT: {report.verdict}")


if __name__ == "__main__":
    main()
