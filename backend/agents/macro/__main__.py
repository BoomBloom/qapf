"""Manual verification runner: python -m agents.macro

Hits live FRED (keyless CSV) and yfinance. No API keys required.
"""

import logging

from .fundamentals import FundamentalsIngestor
from .regime import MacroRegimeClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    print("=== Macro regime assessment (live FRED data) ===\n")
    assessment = MacroRegimeClassifier().assess()

    print(f"REGIME:      {assessment.regime.value}")
    print(f"Growth:      {assessment.growth_direction.value} (score {assessment.growth_score:+.3f})")
    print(f"Inflation:   {assessment.inflation_direction.value} (score {assessment.inflation_score:+.3f})")
    print(f"Risk regime: {assessment.risk_regime.value}")
    print("\nReasoning:")
    for line in assessment.reasoning:
        print(f"  - {line}")

    # Rate series are reported in percentage points; level series in percent.
    RATE_SERIES = {"unemployment_rate", "vix", "yield_curve", "fed_funds_rate"}
    print("\nInputs:")
    for snap in assessment.inputs:
        if snap.alias in RATE_SERIES:
            yoy = f"{snap.yoy_change_pp:+.2f}pp" if snap.yoy_change_pp is not None else "n/a"
        else:
            yoy = f"{snap.yoy_change_pct:+.2f}%" if snap.yoy_change_pct is not None else "n/a"
        print(
            f"  {snap.alias:<24} {snap.series_id:<10} "
            f"latest={snap.latest_value:>10.3f} ({snap.latest_date})  YoY={yoy:>9}  "
            f"n={snap.n_observations}"
        )

    # Sanity check: the quadrant label must agree with the two signed scores.
    # A mismatch would mean the mapping table and the scores disagree.
    expected_growth = "expanding" if assessment.growth_score >= 0 else "contracting"
    expected_inflation = "rising" if assessment.inflation_score >= 0 else "falling"
    assert assessment.growth_direction.value == expected_growth, "growth label/score mismatch"
    assert assessment.inflation_direction.value == expected_inflation, "inflation label/score mismatch"
    print("\nSanity check passed: regime label is consistent with growth/inflation scores.")

    # Regression check for a real bug: a positional shift(12) reports a
    # 13-month change on any monthly series with a gap (CPIAUCSL is missing
    # 2025-10-01). The date-offset YoY in the reasoning must agree with the
    # date-offset YoY in the snapshot for the same series.
    from .regime import _yoy_pct, _yoy_series  # noqa: PLC0415

    cpi_snap = next((s for s in assessment.inputs if s.alias == "cpi"), None)
    if cpi_snap is not None and cpi_snap.yoy_change_pct is not None:
        cpi_series = MacroRegimeClassifier().client.fetch_series("cpi", start_date="2015-01-01")
        from_series = float(_yoy_series(cpi_series).iloc[-1])
        from_scalar = float(_yoy_pct(cpi_series))
        assert abs(from_series - from_scalar) < 1e-6, (
            f"YoY paths disagree ({from_series:.4f} vs {from_scalar:.4f}) — the "
            f"gap-tolerance regression has come back."
        )
        print(
            f"Regression check passed: both YoY paths agree on CPI "
            f"({from_scalar:.2f}%) despite the missing 2025-10-01 observation."
        )

    # Point-in-time regression check: as_of=<today> must exactly match live
    # (as_of=None), and a historical as_of must never surface data past that
    # cutoff. Needed for Agent 9's walk-forward backtest, which asks "what was
    # the regime on this past date" for every rebalance -- if this silently
    # used today's regime for historical dates, every backtest result built on
    # top of it would be look-ahead-biased.
    import datetime as _dt

    as_of_today = MacroRegimeClassifier().assess(as_of=str(_dt.date.today()))
    assert as_of_today.regime == assessment.regime and abs(
        as_of_today.growth_score - assessment.growth_score
    ) < 1e-9, "assess(as_of=today) disagrees with assess() (live) — point-in-time path is broken"

    past = MacroRegimeClassifier().assess(as_of="2025-08-18")
    assert all(s.latest_date <= "2025-08-18" for s in past.inputs), (
        "assess(as_of=...) leaked data past the cutoff — a walk-forward backtest "
        "built on this would be look-ahead-biased"
    )
    print(
        "Point-in-time check passed: as_of=today matches live, and a historical "
        "as_of surfaces no data past its cutoff."
    )

    print("\n=== Company fundamentals (live yfinance) ===\n")
    ingestor = FundamentalsIngestor()
    for ticker in ["AAPL", "KO"]:
        snap = ingestor.fetch(ticker)
        cap = f"${snap.market_cap / 1e9:,.1f}B" if snap.market_cap else "n/a"
        pe = f"{snap.trailing_pe:.2f}" if snap.trailing_pe else "n/a"
        margin = f"{snap.profit_margin * 100:.2f}%" if snap.profit_margin else "n/a"
        print(
            f"{snap.ticker:<6} {(snap.company_name or '')[:24]:<26} "
            f"sector={snap.sector or 'n/a':<24} cap={cap:<12} PE={pe:<8} margin={margin}"
        )


if __name__ == "__main__":
    main()
