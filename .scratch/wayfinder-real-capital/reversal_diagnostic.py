"""Diagnostic, NOT a ticket-02 attempt: does dropping the 5-day reversal
factor from the monthly-rebalanced blend help, before folding it into the
final formal attempt?

Raised by an external review (Gemini, 2026-08-20, see
external-opinion-gemini-2026-08-20.md): reversal is a fast-decaying signal
held for a full month between rebalances -- ~15 of 20 trading days trade on
a stale, decayed version of the signal, plausibly fighting the slower
12-1 momentum factor in the same blend. Concrete and checkable, so checking
it rather than either dismissing or adopting on the external opinion alone.

Tests on the current standing production baseline (Yang-Zhang low_volatility
+ volatility-managed exposure) -- the SAME monkeypatch pattern already used
for the Yang-Zhang and pure-low-vol diagnostics, zero production code
touched here.
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
REALIZED_VOL_WINDOW = 22
MAX_LEVERAGE = 1.0

IBKR_LITE_EXCHANGE_KWARGS = {
    "freq": "day", "limit_threshold": 0.095, "deal_price": "close",
    "open_cost": 0.0005, "close_cost": 0.0015, "min_cost": 0,
}

NO_REVERSAL_WEIGHTS = {
    "momentum_12_1": 1 / 3,
    "reversal_5d": 0.0,
    "low_volatility": 1 / 3,
    "volume_trend": 1 / 3,
}


def _sharpe(returns, trading_days=252):
    r = returns.dropna()
    if len(r) < 2 or r.std(ddof=1) == 0:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(trading_days))


def _max_drawdown(returns):
    equity = (1 + returns.dropna()).cumprod()
    return float(((equity - equity.cummax()) / equity.cummax()).min())


def apply_vol_management(daily_returns):
    r = daily_returns.dropna()
    target_vol = float(r.std(ddof=1))
    realized_vol = r.rolling(REALIZED_VOL_WINDOW).std(ddof=1).shift(1)
    leverage = (target_vol / realized_vol).clip(upper=MAX_LEVERAGE).fillna(0.0)
    return r * leverage


def main():
    from agents.alpha import combiner as combiner_module
    from agents.backtest.walkforward import WalkForwardBacktester

    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")

    print(f"Downloading {len(UNIVERSE)} tickers, {DOWNLOAD_START} to {TEST_END} (yfinance, full OHLCV)...")
    data = yf.download(UNIVERSE, start=DOWNLOAD_START, end=TEST_END, interval="1d",
                        progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")
    opens, highs, lows = data["Open"], data["High"], data["Low"]

    print("\n=== Baseline: current standing (4-factor blend incl. reversal_5d) ===")
    bt_base = WalkForwardBacktester()
    _, base_returns = bt_base.run(
        prices, volumes, test_start=TEST_START, test_end=TEST_END,
        account=ACCOUNT, n_trials=1, exchange_kwargs=IBKR_LITE_EXCHANGE_KWARGS,
        opens=opens, highs=highs, lows=lows,
    )
    base_scaled = apply_vol_management(base_returns)
    print(f"  Baseline: Sharpe={_sharpe(base_scaled):.3f}  MaxDD={_max_drawdown(base_scaled):.2%}")

    print("\n=== Monkeypatching: drop reversal_5d, redistribute weight evenly ===")
    original_weights = {k: dict(v) for k, v in combiner_module.REGIME_FACTOR_WEIGHTS.items()}
    for regime in combiner_module.REGIME_FACTOR_WEIGHTS:
        combiner_module.REGIME_FACTOR_WEIGHTS[regime] = dict(NO_REVERSAL_WEIGHTS)
    try:
        bt_nr = WalkForwardBacktester()
        _, nr_returns = bt_nr.run(
            prices, volumes, test_start=TEST_START, test_end=TEST_END,
            account=ACCOUNT, n_trials=1, exchange_kwargs=IBKR_LITE_EXCHANGE_KWARGS,
            opens=opens, highs=highs, lows=lows,
        )
    finally:
        for regime, weights in original_weights.items():
            combiner_module.REGIME_FACTOR_WEIGHTS[regime] = weights

    nr_scaled = apply_vol_management(nr_returns)
    print(f"  No-reversal: Sharpe={_sharpe(nr_scaled):.3f}  MaxDD={_max_drawdown(nr_scaled):.2%}")

    test_prices = prices.loc[TEST_START:TEST_END]
    bench_returns = test_prices.pct_change().mean(axis=1).fillna(0)
    print(f"  Benchmark: Sharpe={_sharpe(bench_returns):.3f}  MaxDD={_max_drawdown(bench_returns):.2%}")

    print("\n=== Comparison ===")
    print(f"{'':22}{'Sharpe':>10}{'Max DD':>10}")
    print(f"{'Baseline (w/ reversal)':22}{_sharpe(base_scaled):>10.3f}{_max_drawdown(base_scaled):>10.2%}")
    print(f"{'No reversal':22}{_sharpe(nr_scaled):>10.3f}{_max_drawdown(nr_scaled):>10.2%}")
    print(f"{'Benchmark':22}{_sharpe(bench_returns):>10.3f}{_max_drawdown(bench_returns):>10.2%}")

    sharpe_improved = _sharpe(nr_scaled) > _sharpe(base_scaled)
    print(f"\nSharpe improved by dropping reversal_5d: {sharpe_improved}")
    if sharpe_improved:
        print("WORTH folding into the final formal attempt alongside the absolute-momentum overlay.")
    else:
        print("NOT worth it -- Gemini's specific mechanism claim didn't hold up on this data.")


if __name__ == "__main__":
    main()
