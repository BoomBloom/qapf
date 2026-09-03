"""KT2 — Kill test: volatility-scaled momentum (Daniel & Moskowitz risk-managed momentum).

THESIS (T1.3 in docs/venture/20-synthesis.md, rank 2):
    Scaling momentum exposure inversely to its own recent realized volatility
    materially improves risk-adjusted return, because momentum's crashes are
    concentrated in high-volatility rebound periods.

WHAT THIS SCRIPT DOES:
    Runs ONE walk-forward backtest of a momentum-only signal, then applies two
    volatility-scaling schemes to the resulting daily return series as pure
    post-processing, and compares Deflated Sharpe Ratios.

    Arm 0 — unscaled momentum (the baseline).
    Arm A — academic construction: w_t = c / sigma_hat_t, uncapped. Tests
            whether the EFFECT exists at all.
    Arm B — implementable construction: w_t = clip(sigma_long / sigma_short, 0, 1).
            De-risking only, never leverage. Tests whether the effect is
            reachable in a long-only cash account, which is what we actually have.

    Arm B is the primary result. Arm A is context. If A passes and B fails, the
    effect is real but requires leverage this account does not have — which is a
    death sentence for the thesis as stated, not a partial win.

PRE-COMMITTED PASS CRITERION (fixed before the first run — do not edit after
seeing results; that is the whole point of a kill test):
    PASS  iff  Arm B Sharpe >= 1.25 x Arm 0 Sharpe  AND  Arm B DSR > Arm 0 DSR.
    Anything else = THESIS DIES, move to rank 1 (odd-lot tender arbitrage).

    The thesis claims momentum's Sharpe roughly doubles. 1.25x is a deliberately
    generous floor: if the effect cannot clear even a quarter of its advertised
    size on our data, it is not worth building on.

WHY THIS ISN'T CHEATING:
  - Every volatility estimate is lagged one bar, so the weight applied on day t
    uses only returns strictly before t. `test_no_lookahead()` proves it by
    corrupting the future and asserting past weights are unchanged.
  - Arm A's constant `c` is a pure scale factor, and Sharpe is scale-invariant,
    so its value cannot flatter the result. Arm B avoids the question entirely
    by deriving its target from a trailing window rather than a chosen constant.
  - N_TRIALS is set to the number of strategy variants actually compared. If you
    sweep lookbacks, you MUST raise it — see the guard in `main()`.

RUN IT (from the repo root, with the Python 3.12 venv active):
    source .venv/bin/activate
    python docs/venture/killtests/kt2_vol_scaled_momentum.py

Requires `reference/qlib` and Qlib's bundled US dataset at ~/.qlib/qlib_data/us_data.
The `if __name__ == "__main__":` guard is mandatory — qlib's multiprocessing
re-imports this module per worker; see .claude/references/qlib-known-issues.md.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend"))

# --- pre-committed parameters (do not tune after seeing results) -------------
DM_LOOKBACK = 126        # Daniel-Moskowitz forecast window, ~6 months
ARM_B_SHORT = 63         # ~3 months
ARM_B_LONG = 252         # ~1 year
ARM_B_CAP = 1.0          # de-risk only; no leverage available in a cash account
N_TRIALS = 3             # arms compared: unscaled, A, B
SHARPE_HURDLE = 1.25     # Arm B must clear this multiple of the baseline
TRADING_DAYS = 252

# Starts a year earlier than Agent 9's usual 2018-01-01. Arm B's 252-day window
# burns in a full year, and scoring the arms on a common sample would otherwise
# throw that year away — leaving a test window that begins in Dec 2018 and is
# dominated by COVID. Starting in early 2017 spends the burn-in on data we do not
# need to score, so the common sample still covers 2018 through the crash.
# Qlib's bundled dataset is verified complete for all 15 tickers from 2017-01-03.
TEST_START = "2017-02-01"
TEST_END = "2020-10-30"  # last valid date in Qlib's bundled calendar
DOWNLOAD_START = "2015-06-01"  # buffer for the 252-day momentum lookback before TEST_START


def annualized_sharpe(returns: pd.Series) -> float:
    r = returns.dropna()
    if len(r) < 2 or r.std(ddof=1) == 0:
        return float("nan")
    return float(r.mean() / r.std(ddof=1) * np.sqrt(TRADING_DAYS))


def max_drawdown(returns: pd.Series) -> float:
    curve = (1.0 + returns.dropna()).cumprod()
    return float((curve / curve.cummax() - 1.0).min())


def scale_weights_arm_a(returns: pd.Series, lookback: int = DM_LOOKBACK) -> pd.Series:
    """w_t = c / sigma_hat_t, where sigma_hat_t uses only returns before t.

    `c` is the full-sample standard deviation. It is a CONSTANT multiplier and
    Sharpe is scale-invariant, so using an in-sample value here cannot inflate
    the Sharpe comparison — only the time-variation of w_t can move it. Stated
    explicitly because it looks like leakage and isn't.
    """
    sigma = returns.rolling(lookback).std(ddof=1).shift(1)
    return (returns.std(ddof=1) / sigma).where(sigma > 0)


def scale_weights_arm_b(
    returns: pd.Series,
    short: int = ARM_B_SHORT,
    long: int = ARM_B_LONG,
    cap: float = ARM_B_CAP,
) -> pd.Series:
    """w_t = clip(sigma_long / sigma_short, 0, cap), both windows lagged one bar.

    Fully ex-ante and needs no chosen constant: it de-risks when short-horizon
    volatility runs hot relative to its own longer-run norm, and never exceeds
    `cap`, so it is implementable in a long-only cash account.
    """
    sigma_s = returns.rolling(short).std(ddof=1).shift(1)
    sigma_l = returns.rolling(long).std(ddof=1).shift(1)
    w = (sigma_l / sigma_s).where(sigma_s > 0)
    return w.clip(upper=cap)


def apply_weights(returns: pd.Series, weights: pd.Series) -> pd.Series:
    return (weights * returns).dropna()


def test_no_lookahead(returns: pd.Series) -> None:
    """Corrupt the second half of the return series; every weight in the first
    half must be identical. A scaling scheme that peeks would fail this."""
    midpoint = returns.index[len(returns) // 2]
    dirty = returns.copy()
    dirty.loc[dirty.index > midpoint] *= 50.0

    for name, fn in (("Arm A", scale_weights_arm_a), ("Arm B", scale_weights_arm_b)):
        clean_w = fn(returns).loc[:midpoint]
        dirty_w = fn(dirty).loc[:midpoint]
        # Arm A's constant `c` is a full-sample scalar, so corrupting the future
        # rescales every weight uniformly. Compare shapes, not levels, for A;
        # Arm B has no such constant and must match exactly.
        if name == "Arm A":
            ratio = (dirty_w / clean_w).dropna()
            # Compare the SPREAD of the ratio, not its distinct-value count:
            # floating-point rounding leaves every element differing in the last
            # ULP, so `nunique()` would report hundreds even for a constant ratio.
            spread = (ratio.max() - ratio.min()) / abs(ratio.mean())
            assert spread < 1e-9, (
                f"LOOK-AHEAD in Arm A: corrupting the future changed weight SHAPE "
                f"(relative spread {spread:.2e}), not just the uniform scale constant."
            )
        else:
            pd.testing.assert_series_equal(
                clean_w.dropna(), dirty_w.dropna(), check_exact=False, rtol=1e-12,
                obj="Arm B weights before the midpoint",
            )
    print(f"  Look-ahead test PASSED: corrupting all returns after {midpoint.date()} "
          f"left every earlier weight unchanged (Arm B exactly; Arm A up to its scale constant).")


def test_constant_weight_is_identity(returns: pd.Series) -> None:
    """Sanity: a flat weight must reproduce the unscaled Sharpe exactly.
    Catches an alignment bug that would otherwise masquerade as a result."""
    flat = pd.Series(1.0, index=returns.index)
    assert np.isclose(annualized_sharpe(apply_weights(returns, flat)),
                      annualized_sharpe(returns), atol=1e-12), \
        "A constant weight changed the Sharpe — the weight/return alignment is wrong."
    print("  Identity check PASSED: constant weight reproduces the unscaled Sharpe exactly.")


def main() -> None:
    import qlib
    import yfinance as yf

    from agents.alpha import combiner as combiner_mod
    from agents.backtest.walkforward import WalkForwardBacktester
    from agents.stats.toolkit import ProbabilityStatisticsToolkit

    assert isinstance(DM_LOOKBACK, int) and isinstance(ARM_B_SHORT, int), (
        "Lookbacks must stay single pre-committed integers. If you sweep them, "
        "every additional configuration is another trial and N_TRIALS must rise "
        "to match — otherwise the DSR silently understates overfitting risk."
    )

    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")

    universe = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "JPM", "V", "WMT", "KO", "PEP",
        "XOM", "CVX", "JNJ", "PG", "HD",
    ]
    print(f"Downloading {len(universe)} tickers, {DOWNLOAD_START} to {TEST_END}...")
    data = yf.download(universe, start=DOWNLOAD_START, end=TEST_END,
                       interval="1d", progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")
    print(f"  {len(prices)} trading days\n")

    # Isolate momentum. The thesis is about MOMENTUM's crashes specifically, so
    # testing it on Agent 7's 4-factor blend would answer a different question.
    # Patched in this script only — production weights are untouched.
    for regime in combiner_mod.REGIME_FACTOR_WEIGHTS:
        combiner_mod.REGIME_FACTOR_WEIGHTS[regime] = {"momentum": 1.0}
    print("Factor weights patched to momentum-only for this test "
          "(production REGIME_FACTOR_WEIGHTS untouched on disk).\n")

    print(f"=== Walk-forward: momentum-only, {TEST_START} to {TEST_END} ===")
    backtester = WalkForwardBacktester()
    report, daily_returns = backtester.run(
        prices, volumes, test_start=TEST_START, test_end=TEST_END, n_trials=N_TRIALS,
    )
    daily_returns = daily_returns.dropna()
    print(f"  {report.n_rebalances} rebalances, {len(daily_returns)} daily returns\n")

    print("=== Correctness gates (these run BEFORE any result is shown) ===")
    test_constant_weight_is_identity(daily_returns)
    test_no_lookahead(daily_returns)

    stats = ProbabilityStatisticsToolkit()
    arms = {
        "Arm 0 — unscaled": daily_returns,
        "Arm A — inverse-vol, uncapped": apply_weights(daily_returns, scale_weights_arm_a(daily_returns)),
        "Arm B — de-risk only, capped at 1.0": apply_weights(daily_returns, scale_weights_arm_b(daily_returns)),
    }

    # Align every arm to a COMMON sample. Each scheme burns in a different number
    # of days (Arm B's 252-day window is the longest), so scoring them on their
    # own available histories would compare the baseline over the full window
    # against Arm B over a later, shorter one — which here would mean dropping
    # most of 2018 while keeping the COVID crash. That is not a fair comparison;
    # it is a different question with a flattering answer.
    common = arms["Arm 0 — unscaled"].index
    for series in arms.values():
        common = common.intersection(series.index)
    dropped = len(daily_returns) - len(common)
    arms = {name: series.loc[common] for name, series in arms.items()}
    print(f"  Common-sample alignment: all arms scored on {len(common)} shared days "
          f"({common[0].date()} to {common[-1].date()}); {dropped} burn-in days dropped from every arm.")

    print(f"\n=== Results (DSR at n_trials={N_TRIALS}, identical for every arm) ===")
    print(f"{'Arm':<38} {'Sharpe':>8} {'DSR':>8} {'MaxDD':>9} {'Obs':>6}")
    results = {}
    for name, series in arms.items():
        sharpe = annualized_sharpe(series)
        dsr = stats.deflated_sharpe_ratio(series, n_trials=N_TRIALS).deflated_sharpe_ratio
        mdd = max_drawdown(series)
        results[name] = (sharpe, dsr)
        print(f"{name:<38} {sharpe:>8.3f} {dsr:>8.3f} {mdd:>8.2%} {len(series):>6}")

    base_sharpe, base_dsr = results["Arm 0 — unscaled"]
    b_sharpe, b_dsr = results["Arm B — de-risk only, capped at 1.0"]
    a_sharpe, _ = results["Arm A — inverse-vol, uncapped"]

    print(f"\n=== Verdict (criterion fixed before the run) ===")
    print(f"Required: Arm B Sharpe >= {SHARPE_HURDLE} x {base_sharpe:.3f} = "
          f"{SHARPE_HURDLE * base_sharpe:.3f}, and Arm B DSR > {base_dsr:.3f}")
    print(f"Actual:   Arm B Sharpe = {b_sharpe:.3f}, DSR = {b_dsr:.3f}")

    passed = b_sharpe >= SHARPE_HURDLE * base_sharpe and b_dsr > base_dsr
    if passed:
        print("\n  THESIS SURVIVES. Next: re-verify Daniel-Moskowitz's primary sources "
              "from an unrestricted network, then widen the universe and the window "
              "before it earns any architecture.")
    else:
        print("\n  THESIS DIES on this data. Record it in docs/venture/20-synthesis.md "
              "and move to rank 1 (odd-lot tender arbitrage).")
        if a_sharpe >= SHARPE_HURDLE * base_sharpe:
            print("  NOTE: Arm A cleared the hurdle but Arm B did not — the effect exists "
                  "and requires leverage this account does not have. That is still a death "
                  "sentence for the thesis as stated, not a partial win.")

    print("\nCaveats that bound this result regardless of outcome: 15 large-cap names, "
          "one 2018-2020 window, monthly rebalance. A pass here is permission to test "
          "harder, never a green light to trade.")


if __name__ == "__main__":
    main()
