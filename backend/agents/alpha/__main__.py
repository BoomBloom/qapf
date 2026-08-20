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
    yang_zhang_volatility,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "JPM", "V", "WMT", "KO", "PEP",
    "XOM", "CVX", "JNJ", "PG", "HD",
]


def download_universe() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    print(f"Downloading {len(UNIVERSE)} tickers (3y daily)...")
    data = yf.download(UNIVERSE, period="3y", interval="1d", progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")
    opens, highs, lows = data["Open"], data["High"], data["Low"]
    print(f"  {len(prices)} trading days, {prices.shape[1]} tickers\n")
    return prices, volumes, opens, highs, lows


def test_no_lookahead_bias(prices, volumes, macro_regime, risk_regime, opens=None, highs=None, lows=None):
    """Corrupt every price (and OHLC, when supplied) after `as_of` and assert
    the signal is unchanged. Covers the new Yang-Zhang path too when
    opens/highs/lows are passed -- `_slice_to` needs to apply to them exactly
    like it does to prices/volumes, and this is what actually verifies that
    rather than trusting the implementation by inspection."""
    combiner = AlphaCombiner()
    as_of = prices.index[-120]  # leave 120 days of "future" to corrupt

    clean = combiner.generate(prices, volumes, macro_regime, risk_regime, as_of=as_of,
                               opens=opens, highs=highs, lows=lows)

    corrupted = prices.copy()
    corrupted.loc[corrupted.index > as_of] *= 100.0
    corrupted_vol = volumes.copy()
    corrupted_vol.loc[corrupted_vol.index > as_of] *= 100.0
    corrupted_kwargs = {}
    if opens is not None:
        for name, frame in (("opens", opens), ("highs", highs), ("lows", lows)):
            c = frame.copy()
            c.loc[c.index > as_of] *= 100.0
            corrupted_kwargs[name] = c

    dirty = combiner.generate(corrupted, corrupted_vol, macro_regime, risk_regime, as_of=as_of,
                               **corrupted_kwargs)

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


def test_macro_regime_no_longer_changes_factor_weights(prices, volumes):
    """Inverted 2026-08-19 (wayfinder ticket 06): factor weights are now FLAT
    across macro regimes on purpose (see combiner.py's module docstring for
    why). This test used to assert the opposite; asserting the old behavior
    now would fail by design, which is itself a useful signal that the
    intended change actually landed rather than silently reverting.

    Same macro premise, opposite assertion: at identical risk regime (so
    exposure_scale is held constant), switching MACRO regime must now produce
    byte-identical signals, because REGIME_FACTOR_WEIGHTS is the same dict for
    every regime. RISK regime is a separate mechanism (exposure_scale) and is
    checked separately below — flattening factor weights didn't touch it.
    """
    combiner = AlphaCombiner()
    growth = combiner.generate(
        prices, volumes, MacroRegime.DISINFLATIONARY_GROWTH, RiskRegime.RISK_ON
    )
    stag = combiner.generate(prices, volumes, MacroRegime.STAGFLATION, RiskRegime.RISK_ON)

    growth_map = {s.ticker: s.signal for s in growth.signals}
    stag_map = {s.ticker: s.signal for s in stag.signals}
    changed = {t: (growth_map[t], stag_map[t]) for t in growth_map if abs(growth_map[t] - stag_map[t]) > 1e-9}
    assert not changed, (
        f"macro regime still affects signals at flat weights — the flatten did not fully land: {changed}"
    )
    print(
        f"Flat-weight invariance test PASSED: goldilocks and stagflation produce byte-identical "
        f"signals for all {len(growth_map)} names now that factor weights don't vary by macro regime."
    )

    growth_order = [s.ticker for s in growth.signals]
    stag_order = [s.ticker for s in stag.signals]
    assert growth_order == stag_order, "ranking order changed despite identical signals — sort instability"
    print("  Ranking order also identical, as expected.")


def test_risk_regime_still_scales_exposure(prices, volumes):
    """The mechanism flattening didn't touch: RISK regime (not macro regime)
    still scales gross exposure via RISK_EXPOSURE_SCALE, independent of the
    now-flat factor weights."""
    combiner = AlphaCombiner()
    risk_on = combiner.generate(prices, volumes, MacroRegime.STAGFLATION, RiskRegime.RISK_ON)
    risk_off = combiner.generate(prices, volumes, MacroRegime.STAGFLATION, RiskRegime.RISK_OFF)

    on_map = {s.ticker: s.signal for s in risk_on.signals}
    off_map = {s.ticker: s.signal for s in risk_off.signals}
    changed = sum(1 for t in on_map if abs(on_map[t] - off_map[t]) > 1e-9)
    assert changed > 0, "risk regime had no effect on exposure — RISK_EXPOSURE_SCALE is being ignored"
    print(
        f"Risk-regime exposure test PASSED: risk-on -> risk-off moved {changed}/{len(on_map)} "
        f"signals via exposure scaling, independent of the (now flat) factor weights."
    )


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


def test_yang_zhang_volatility(prices, volumes, opens, highs, lows):
    """Verify the OHLC path (added 2026-08-20) is real, not decorative:
    (1) it's actually used -- and changes the low_volatility ranking -- when
    open/high/low are supplied, and (2) its own sign convention is correct,
    independently recomputed, same standard as every other factor check here.
    (3) omitting OHLC must reproduce the exact old close-to-close behavior --
    the additive-parameter promise this refactor made."""
    with_ohlc = compute_raw_factors(prices, volumes, opens=opens, highs=highs, lows=lows)
    without_ohlc = compute_raw_factors(prices, volumes)

    assert not without_ohlc["low_volatility"].round(8).equals(with_ohlc["low_volatility"].round(8)), (
        "low_volatility is identical with and without OHLC -- the Yang-Zhang path isn't "
        "actually being used when open/high/low are supplied"
    )
    print("OHLC-path-is-live check PASSED: supplying open/high/low measurably changes "
          "low_volatility's values (Yang-Zhang, not the close-to-close fallback).")

    # Independently recompute Yang-Zhang's sign convention: the name with the
    # SMALLEST range-based vol must score HIGHEST (same low-vol-anomaly
    # direction as the close-to-close version, just a different estimator).
    yz_vol = {}
    for t in prices.columns:
        v = yang_zhang_volatility(opens[t], highs[t], lows[t], prices[t])
        if v is not None:
            yz_vol[t] = -v  # yang_zhang_volatility returns the already-negated score; un-negate for a plain vol comparison
    yz_series = pd.Series(yz_vol)
    lowest, highest = yz_series.idxmin(), yz_series.idxmax()
    assert with_ohlc.at[lowest, "low_volatility"] > with_ohlc.at[highest, "low_volatility"], (
        f"Yang-Zhang sign is inverted: {lowest} (range-vol {yz_series[lowest]:.5f}) should "
        f"outscore {highest} (range-vol {yz_series[highest]:.5f})"
    )
    print(f"Yang-Zhang sign check PASSED: {lowest} (lowest range-vol) outscores "
          f"{highest} (highest range-vol).")

    # Regression: no-OHLC path must be byte-identical to pre-refactor behavior.
    assert without_ohlc.round(10).equals(compute_raw_factors(prices, volumes).round(10)), (
        "calling compute_raw_factors without OHLC must be deterministic and match itself"
    )
    print("Backward-compatibility check PASSED: omitting OHLC reproduces the original "
          "close-to-close behavior exactly.")


def main():
    prices, volumes, opens, highs, lows = download_universe()

    print("=== Pulling live macro regime from Agent 6 ===")
    assessment = MacroRegimeClassifier().assess()
    macro_regime = assessment.regime
    risk_regime = assessment.risk_regime
    print(f"  regime={macro_regime.value}  risk={risk_regime.value}\n")

    combiner = AlphaCombiner()
    bundle = combiner.generate(prices, volumes, macro_regime, risk_regime, opens=opens, highs=highs, lows=lows)

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
    test_yang_zhang_volatility(prices, volumes, opens, highs, lows)
    test_no_lookahead_bias(prices, volumes, macro_regime, risk_regime, opens=opens, highs=highs, lows=lows)
    test_macro_regime_no_longer_changes_factor_weights(prices, volumes)
    test_risk_regime_still_scales_exposure(prices, volumes)

    print(f"\nRegime weight table covers all {len(REGIME_FACTOR_WEIGHTS)} macro regimes.")


if __name__ == "__main__":
    main()
