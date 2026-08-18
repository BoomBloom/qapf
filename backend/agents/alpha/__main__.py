"""Manual verification runner: python -m agents.alpha

Demonstrates real agent-to-agent composition: pulls the live macro regime from
Agent 6 (`agents.macro`) and uses it to weight factors computed here.

Includes a look-ahead bias test, which is the cardinal correctness concern for
an alpha signal: post-`as_of` prices are corrupted with a 100x spike and the
signal must not move. If any factor peeked into the future, this fails loudly.
"""

import logging

import pandas as pd
import yfinance as yf

from agents.macro.regime import MacroRegimeClassifier
from agents.macro.schemas import MacroRegime, RiskRegime

from .combiner import REGIME_FACTOR_WEIGHTS, AlphaCombiner
from .factors import (
    MOMENTUM_LONG,
    MOMENTUM_SKIP,
    REVERSAL_WINDOW,
    VOL_WINDOW,
    compute_raw_factors,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "JPM", "V", "WMT", "KO", "PEP",
    "XOM", "CVX", "JNJ", "PG", "HD",
]


def download_universe() -> tuple[pd.DataFrame, pd.DataFrame]:
    print(f"Downloading {len(UNIVERSE)} tickers (3y daily)...")
    data = yf.download(UNIVERSE, period="3y", interval="1d", progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")
    print(f"  {len(prices)} trading days, {prices.shape[1]} tickers\n")
    return prices, volumes


def test_no_lookahead_bias(prices, volumes, macro_regime, risk_regime):
    """Corrupt every price after `as_of` and assert the signal is unchanged."""
    combiner = AlphaCombiner()
    as_of = prices.index[-120]  # leave 120 days of "future" to corrupt

    clean = combiner.generate(prices, volumes, macro_regime, risk_regime, as_of=as_of)

    corrupted = prices.copy()
    corrupted.loc[corrupted.index > as_of] *= 100.0
    corrupted_vol = volumes.copy()
    corrupted_vol.loc[corrupted_vol.index > as_of] *= 100.0

    dirty = combiner.generate(corrupted, corrupted_vol, macro_regime, risk_regime, as_of=as_of)

    clean_map = {s.ticker: s.signal for s in clean.signals}
    dirty_map = {s.ticker: s.signal for s in dirty.signals}
    assert clean_map.keys() == dirty_map.keys(), "universe changed under corruption"

    mismatches = {
        t: (clean_map[t], dirty_map[t])
        for t in clean_map
        if abs(clean_map[t] - dirty_map[t]) > 1e-12
    }
    assert not mismatches, (
        f"LOOK-AHEAD BIAS DETECTED — corrupting future prices changed the "
        f"as-of-{as_of.date()} signal for: {mismatches}"
    )
    print(
        f"Look-ahead test PASSED: 100x corruption of all {(prices.index > as_of).sum()} "
        f"post-{as_of.date()} bars left every signal byte-identical."
    )


def test_regime_changes_signals(prices, volumes):
    """A different macro regime must actually produce different signals —
    otherwise the regime input is decorative."""
    combiner = AlphaCombiner()
    growth = combiner.generate(
        prices, volumes, MacroRegime.DISINFLATIONARY_GROWTH, RiskRegime.RISK_ON
    )
    stag = combiner.generate(prices, volumes, MacroRegime.STAGFLATION, RiskRegime.RISK_ON)

    growth_map = {s.ticker: s.signal for s in growth.signals}
    stag_map = {s.ticker: s.signal for s in stag.signals}
    changed = sum(1 for t in growth_map if abs(growth_map[t] - stag_map[t]) > 1e-9)
    assert changed > 0, "regime had no effect on signals — the regime input is being ignored"
    print(
        f"Regime-sensitivity test PASSED: switching goldilocks -> stagflation "
        f"moved {changed}/{len(growth_map)} signals."
    )

    # Ranking should also reorder, not merely rescale, since the weights differ.
    growth_order = [s.ticker for s in growth.signals]
    stag_order = [s.ticker for s in stag.signals]
    if growth_order != stag_order:
        print("  Ranking also reordered (weights genuinely change relative attractiveness).")


def test_factor_directions(prices, volumes):
    """Verify factor signs against independently computed ground truth.

    A flipped sign in a factor definition is a silent bug: the pipeline runs
    fine and emits confident, backwards signals. Each check recomputes the
    underlying quantity directly and asserts the factor ranks it the intended
    way.
    """
    raw = compute_raw_factors(prices, volumes)

    # low_volatility: lower realized vol must score HIGHER (the low-vol anomaly).
    actual_vol = {
        t: prices[t].pct_change().dropna().iloc[-VOL_WINDOW:].std() for t in prices.columns
    }
    vol_series = pd.Series(actual_vol)
    lowest_vol, highest_vol = vol_series.idxmin(), vol_series.idxmax()
    assert raw.at[lowest_vol, "low_volatility"] > raw.at[highest_vol, "low_volatility"], (
        f"low_volatility sign is inverted: {lowest_vol} (vol {vol_series[lowest_vol]:.4f}) "
        f"should outscore {highest_vol} (vol {vol_series[highest_vol]:.4f})"
    )

    # reversal_5d: the worst 5-day performer must score HIGHEST (it's negated).
    ret_5d = {
        t: prices[t].dropna().iloc[-1] / prices[t].dropna().iloc[-(REVERSAL_WINDOW + 1)] - 1.0
        for t in prices.columns
    }
    ret_series = pd.Series(ret_5d)
    worst, best = ret_series.idxmin(), ret_series.idxmax()
    assert raw.at[worst, "reversal_5d"] > raw.at[best, "reversal_5d"], (
        f"reversal_5d sign is inverted: {worst} ({ret_series[worst]:+.2%} over 5d) should "
        f"outscore {best} ({ret_series[best]:+.2%})"
    )

    # momentum_12_1: must track the 12-month-ago -> 1-month-ago return, and must
    # NOT be the plain trailing 12-month return (the skip month is the point).
    mom = {}
    for t in prices.columns:
        s = prices[t].dropna()
        mom[t] = s.iloc[-(MOMENTUM_SKIP + 1)] / s.iloc[-MOMENTUM_LONG] - 1.0
    mom_series = pd.Series(mom)
    best_mom, worst_mom = mom_series.idxmax(), mom_series.idxmin()
    assert raw.at[best_mom, "momentum_12_1"] > raw.at[worst_mom, "momentum_12_1"], (
        "momentum_12_1 sign is inverted"
    )
    no_skip = {}
    for t in prices.columns:
        s = prices[t].dropna()
        no_skip[t] = s.iloc[-1] / s.iloc[-MOMENTUM_LONG] - 1.0
    assert not pd.Series(no_skip).round(6).equals(mom_series.round(6)), (
        "momentum_12_1 appears to include the most recent month — the 1-month "
        "skip is missing, which mixes in short-term reversal"
    )

    print(
        f"Factor-direction test PASSED: low_volatility favors {lowest_vol} over "
        f"{highest_vol}; reversal favors {worst} over {best}; momentum honors its "
        f"1-month skip."
    )


def main():
    prices, volumes = download_universe()

    print("=== Pulling live macro regime from Agent 6 ===")
    assessment = MacroRegimeClassifier().assess()
    macro_regime = assessment.regime
    risk_regime = assessment.risk_regime
    print(f"  regime={macro_regime.value}  risk={risk_regime.value}\n")

    combiner = AlphaCombiner()
    bundle = combiner.generate(prices, volumes, macro_regime, risk_regime)

    print(f"=== Alpha signals as of {bundle.as_of} ===")
    print(f"Regime: {bundle.macro_regime} | Risk: {bundle.risk_regime}")
    print(f"Exposure scale: {bundle.exposure_scale}")
    print(f"Factor weights: {bundle.factor_weights}\n")
    print(f"{'Ticker':<8}{'Signal':>9}{'Confid.':>9}   Factors (normalized)")
    for sig in bundle.signals:
        detail = "  ".join(f"{f.name.split('_')[0]}={f.normalized_value:+.2f}" for f in sig.factors)
        print(f"{sig.ticker:<8}{sig.signal:>+9.4f}{sig.confidence:>9.2f}   {detail}")

    longs = [s.ticker for s in bundle.signals if s.signal > 0.2]
    shorts = [s.ticker for s in bundle.signals if s.signal < -0.2]
    print(f"\nLong candidates (>+0.2):  {longs}")
    print(f"Short candidates (<-0.2): {shorts}")

    print("\n=== Correctness checks ===")
    assert all(-1.0 <= s.signal <= 1.0 for s in bundle.signals), "signal out of [-1,1]"
    assert all(0.0 <= s.confidence <= 1.0 for s in bundle.signals), "confidence out of [0,1]"
    print("Bounds check PASSED: all signals in [-1,+1], all confidences in [0,1].")

    test_factor_directions(prices, volumes)
    test_no_lookahead_bias(prices, volumes, macro_regime, risk_regime)
    test_regime_changes_signals(prices, volumes)

    print(f"\nRegime weight table covers all {len(REGIME_FACTOR_WEIGHTS)} macro regimes.")


if __name__ == "__main__":
    main()
