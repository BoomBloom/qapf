"""Prototype, NOT a ticket-02 attempt: does swapping the low_volatility
factor's close-to-close std for a Yang-Zhang range-based estimator help,
before investing in the real plumbing change?

docs/research/viable-alpha-families.md's #2 (an "enabler," not a strategy)
argues a range-based estimator is a strictly better input to the
low_volatility factor, using the O/H/L columns agents/alpha/factors.py
downloads and then discards. Testing that claim honestly requires either
(a) permanently threading open/high/low through factors.py, combiner.py, and
walkforward.py's signal-generation path, or (b) monkeypatching the ONE factor
function the real pipeline calls, so the entire rest of the real pipeline
(regime classification, combination, cross-sectional normalization, monthly
rebalancing, IBKR-Lite costs, and attempt 2's already-validated
volatility-managed exposure scaling) runs completely unmodified. This script
does (b) -- if it helps, (a) is worth building for real; if not, the
plumbing change was never worth doing.

MONKEYPATCH MECHANICS: agents.alpha.factors.compute_raw_factors() looks up
FACTOR_FUNCTIONS (a module-level dict) fresh on every call, not a captured
reference -- so reassigning FACTOR_FUNCTIONS["low_volatility"] before running
the real WalkForwardBacktester changes what every downstream caller uses,
with zero changes to committed code. The replacement function receives only
a single close-price Series per call (matching FACTOR_FUNCTIONS's "price"
source contract) -- `series.name` recovers which ticker it is (pandas
preserves column name through `df[ticker].dropna()`), used to look up this
script's separately-downloaded OPEN/HIGH/LOW frames, reindexed to
`series.index` so the point-in-time slice compute_raw_factors already applied
to the close series is respected exactly, not re-derived.

YANG-ZHANG ESTIMATOR (Yang & Zhang 2000, unbiased in the continuous limit,
independent of drift, handles opening jumps):
  o_i  = ln(O_i / C_{i-1})              overnight return
  c_i  = ln(C_i / O_i)                  open-to-close return
  rs_i = ln(H_i/C_i)*ln(H_i/O_i) + ln(L_i/C_i)*ln(L_i/O_i)   Rogers-Satchell term
  k    = 0.34 / (1.34 + (n+1)/(n-1))
  sigma_YZ^2 = Var(o) + k*Var(c) + (1-k)*mean(rs)
Kept on the SAME daily (non-annualized) scale as the original
`returns.std(ddof=1)` it replaces, for a fair, direct comparison.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import qlib
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "JPM", "WMT", "KO", "PEP",
    "XOM", "CVX", "JNJ", "PG", "HD",
]
DOWNLOAD_START = "2006-06-01"
TEST_START = "2008-01-01"
TEST_END = "2017-12-31"
ACCOUNT = 1_000

VOL_WINDOW = 60  # matches factors.py's existing VOL_WINDOW, for a fair swap
REALIZED_VOL_WINDOW = 22
MAX_LEVERAGE = 1.0

IBKR_LITE_EXCHANGE_KWARGS = {
    "freq": "day", "limit_threshold": 0.095, "deal_price": "close",
    "open_cost": 0.0005, "close_cost": 0.0015, "min_cost": 0,
}

# Populated in main() after download; the monkeypatch closure below captures
# these names, not values, so they must exist at module scope before the
# closure is called (Python resolves free variables at call time).
OPEN = HIGH = LOW = None


def _yang_zhang_vol(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> float | None:
    df = pd.DataFrame({"o": open_, "h": high, "l": low, "c": close}).dropna()
    if len(df) < VOL_WINDOW + 1:
        return None
    df = df.iloc[-(VOL_WINDOW + 1):]
    prev_c = df["c"].shift(1)
    df = df.iloc[1:]
    prev_c = prev_c.iloc[1:]

    if (df[["o", "h", "l", "c"]] <= 0).any().any() or (prev_c <= 0).any():
        return None  # non-positive price -- can't take a log; bail rather than emit garbage

    o_i = np.log(df["o"] / prev_c)
    c_i = np.log(df["c"] / df["o"])
    rs_i = np.log(df["h"] / df["c"]) * np.log(df["h"] / df["o"]) + np.log(df["l"] / df["c"]) * np.log(df["l"] / df["o"])

    n = len(df)
    if n < 2:
        return None
    var_o = float(o_i.var(ddof=1))
    var_c = float(c_i.var(ddof=1))
    mean_rs = float(rs_i.mean())
    k = 0.34 / (1.34 + (n + 1) / (n - 1))
    sigma_sq = var_o + k * var_c + (1 - k) * mean_rs
    if sigma_sq < 0 or not np.isfinite(sigma_sq):
        return None  # can happen with small/adversarial samples; a real vol can't be negative
    return float(np.sqrt(sigma_sq))


def yz_low_volatility(price_series: pd.Series) -> float | None:
    """Drop-in replacement for factors.low_volatility, same [-vol] sign
    convention (low realized vol -> higher score), same window, different
    estimator. `price_series.name` is the ticker -- see module docstring."""
    ticker = price_series.name
    if ticker not in OPEN.columns:
        return None
    idx = price_series.dropna().index
    o = OPEN[ticker].reindex(idx)
    h = HIGH[ticker].reindex(idx)
    l = LOW[ticker].reindex(idx)
    c = price_series.reindex(idx)
    vol = _yang_zhang_vol(o, h, l, c)
    return -vol if vol is not None else None


def _sharpe(returns: pd.Series, trading_days: int = 252) -> float:
    r = returns.dropna()
    if len(r) < 2 or r.std(ddof=1) == 0:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(trading_days))


def _max_drawdown(returns: pd.Series) -> float:
    equity = (1 + returns.dropna()).cumprod()
    return float(((equity - equity.cummax()) / equity.cummax()).min())


def apply_vol_management(daily_returns: pd.Series) -> pd.Series:
    r = daily_returns.dropna()
    target_vol = float(r.std(ddof=1))
    realized_vol = r.rolling(REALIZED_VOL_WINDOW).std(ddof=1).shift(1)
    leverage = (target_vol / realized_vol).clip(upper=MAX_LEVERAGE).fillna(0.0)
    return r * leverage


def main():
    global OPEN, HIGH, LOW

    from agents.backtest.walkforward import WalkForwardBacktester

    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")

    print(f"Downloading {len(UNIVERSE)} tickers, {DOWNLOAD_START} to {TEST_END} (yfinance, full OHLCV)...")
    data = yf.download(UNIVERSE, start=DOWNLOAD_START, end=TEST_END, interval="1d",
                        progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")
    OPEN, HIGH, LOW = data["Open"], data["High"], data["Low"]

    print("\n=== Baseline: reproducing attempt 2 (close-to-close low_volatility) ===")
    bt_baseline = WalkForwardBacktester()
    _, baseline_returns = bt_baseline.run(
        prices, volumes, test_start=TEST_START, test_end=TEST_END,
        account=ACCOUNT, n_trials=1, exchange_kwargs=IBKR_LITE_EXCHANGE_KWARGS,
    )
    baseline_scaled = apply_vol_management(baseline_returns)
    print(f"  Baseline (vol-managed): Sharpe={_sharpe(baseline_scaled):.3f}  "
          f"MaxDD={_max_drawdown(baseline_scaled):.2%}")

    print("\n=== Monkeypatching low_volatility -> Yang-Zhang, re-running the SAME pipeline ===")
    from agents.alpha import factors as factors_module
    original_entry = factors_module.FACTOR_FUNCTIONS["low_volatility"]
    factors_module.FACTOR_FUNCTIONS["low_volatility"] = ("price", yz_low_volatility)
    try:
        bt_yz = WalkForwardBacktester()
        _, yz_returns = bt_yz.run(
            prices, volumes, test_start=TEST_START, test_end=TEST_END,
            account=ACCOUNT, n_trials=1, exchange_kwargs=IBKR_LITE_EXCHANGE_KWARGS,
        )
    finally:
        factors_module.FACTOR_FUNCTIONS["low_volatility"] = original_entry  # never leave the monkeypatch live

    yz_scaled = apply_vol_management(yz_returns)
    print(f"  Yang-Zhang (vol-managed): Sharpe={_sharpe(yz_scaled):.3f}  "
          f"MaxDD={_max_drawdown(yz_scaled):.2%}")

    test_prices = prices.loc[TEST_START:TEST_END]
    bench_returns = test_prices.pct_change().mean(axis=1).fillna(0)
    print(f"  Benchmark: Sharpe={_sharpe(bench_returns):.3f}  MaxDD={_max_drawdown(bench_returns):.2%}")

    print("\n=== Comparison ===")
    print(f"{'':30}{'Sharpe':>10}{'Max DD':>10}")
    print(f"{'Baseline (close-to-close)':30}{_sharpe(baseline_scaled):>10.3f}{_max_drawdown(baseline_scaled):>10.2%}")
    print(f"{'Yang-Zhang':30}{_sharpe(yz_scaled):>10.3f}{_max_drawdown(yz_scaled):>10.2%}")
    print(f"{'Benchmark':30}{_sharpe(bench_returns):>10.3f}{_max_drawdown(bench_returns):>10.2%}")

    sharpe_improved = _sharpe(yz_scaled) > _sharpe(baseline_scaled)
    dd_improved = abs(_max_drawdown(yz_scaled)) < abs(_max_drawdown(baseline_scaled))
    print(f"\nSharpe improved vs. baseline: {sharpe_improved}")
    print(f"Max drawdown improved vs. baseline: {dd_improved}")
    if sharpe_improved or dd_improved:
        print("\nWORTH promoting to real plumbing (factors.py/combiner.py/walkforward.py) "
              "and running as a formal ticket 07 attempt.")
    else:
        print("\nNOT worth the plumbing investment -- per the research doc's own falsification "
              "standard, this specific enabler didn't move the needle on this data.")


if __name__ == "__main__":
    main()
