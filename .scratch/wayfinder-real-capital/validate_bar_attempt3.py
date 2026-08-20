"""Ticket 07 — attempt 3 of 5.

Builds on attempt 2's baseline (volatility-managed exposure, now the
standing improvement) rather than testing in isolation again -- the same
iterative pattern ticket 06's flattened weights became the standing
baseline before attempt 1 ever ran. This attempt's ONE new variable: Agent
7's low_volatility factor now uses the Yang-Zhang range-based estimator
(`agents/alpha/factors.py`, landed 2026-08-20) instead of close-to-close
std -- real production code now, not a monkeypatch, after the prototype
(`yang_zhang_diagnostic.py`) validated it helps on this exact data
(Sharpe 0.726->0.738, max drawdown -26.48%->-17.64%, holding the vol-managed
exposure layer fixed).

Universe UNCHANGED from attempts 1-2 (still the original 14 hand-picked
names) -- the PIT-universe swap (ticket 13) remains deliberately deferred,
same reasoning as attempt 2: combining an incomplete universe fix with a
real strategy change would conflate two variables.
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
ATTEMPT_N_TRIALS = 3

REALIZED_VOL_WINDOW = 22
MAX_LEVERAGE = 1.0

IBKR_LITE_EXCHANGE_KWARGS = {
    "freq": "day", "limit_threshold": 0.095, "deal_price": "close",
    "open_cost": 0.0005, "close_cost": 0.0015, "min_cost": 0,
}


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
    from agents.backtest.walkforward import WalkForwardBacktester
    from agents.stats.toolkit import ProbabilityStatisticsToolkit

    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")

    print(f"Downloading {len(UNIVERSE)} tickers, {DOWNLOAD_START} to {TEST_END} (yfinance, full OHLCV)...")
    data = yf.download(UNIVERSE, start=DOWNLOAD_START, end=TEST_END, interval="1d",
                        progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")
    opens, highs, lows = data["Open"], data["High"], data["Low"]

    print(f"\n=== Running walk-forward backtest with Yang-Zhang low_volatility (attempt 3/5) ===")
    bt = WalkForwardBacktester()
    _, daily_returns = bt.run(
        prices, volumes, test_start=TEST_START, test_end=TEST_END,
        account=ACCOUNT, n_trials=ATTEMPT_N_TRIALS, exchange_kwargs=IBKR_LITE_EXCHANGE_KWARGS,
        opens=opens, highs=highs, lows=lows,
    )

    print(f"\n=== Applying volatility-managed scaling (standing baseline since attempt 2) ===")
    scaled = apply_vol_management(daily_returns)

    strat_sharpe = _sharpe(scaled)
    strat_max_dd = _max_drawdown(scaled)
    strat_return_per_dd = strat_sharpe / abs(strat_max_dd) if strat_max_dd != 0 else float("nan")
    total_return = float((1 + scaled).prod() - 1)
    final_account = ACCOUNT * (1 + total_return)

    test_prices = prices.loc[TEST_START:TEST_END]
    benchmark_returns = test_prices.pct_change().mean(axis=1).fillna(0)
    bench_sharpe = _sharpe(benchmark_returns)
    bench_max_dd = _max_drawdown(benchmark_returns)
    bench_return_per_dd = bench_sharpe / abs(bench_max_dd) if bench_max_dd != 0 else float("nan")
    bench_total_return = float((1 + benchmark_returns).prod() - 1)

    dsr_result = ProbabilityStatisticsToolkit().deflated_sharpe_ratio(scaled, n_trials=ATTEMPT_N_TRIALS)

    print(f"\n=== Results: {TEST_START} to {TEST_END} (Yang-Zhang + vol-managed) ===\n")
    print(f"{'':24}{'Strategy':>14}{'Benchmark':>14}")
    print(f"{'Total return':24}{total_return:>+14.2%}{bench_total_return:>+14.2%}")
    print(f"{'Annualized Sharpe':24}{strat_sharpe:>14.3f}{bench_sharpe:>14.3f}")
    print(f"{'Max drawdown':24}{strat_max_dd:>14.2%}{bench_max_dd:>14.2%}")
    print(f"{'Return per unit DD':24}{strat_return_per_dd:>14.3f}{bench_return_per_dd:>14.3f}")
    print(f"\nDeflated Sharpe Ratio: {dsr_result.deflated_sharpe_ratio:.4f} (n_trials={ATTEMPT_N_TRIALS})")
    print(f"Final account: ${final_account:,.2f} (started ${ACCOUNT:,})")

    print("\n=== Bar check (all three required) ===")
    c1 = dsr_result.deflated_sharpe_ratio > 0.95
    c2_sharpe = strat_sharpe > bench_sharpe
    c2_dd = strat_return_per_dd > bench_return_per_dd
    c2 = c2_sharpe and c2_dd
    c3 = final_account > ACCOUNT

    print(f"  [{'PASS' if c1 else 'FAIL'}] DSR > 0.95:                        {dsr_result.deflated_sharpe_ratio:.4f}")
    print(f"  [{'PASS' if c2_sharpe else 'FAIL'}] Beats benchmark Sharpe:            {strat_sharpe:.3f} vs {bench_sharpe:.3f}")
    print(f"  [{'PASS' if c2_dd else 'FAIL'}] Beats benchmark return/max-DD:      {strat_return_per_dd:.3f} vs {bench_return_per_dd:.3f}")
    print(f"  [{'PASS' if c3 else 'FAIL'}] Profitable net of costs at $1,000:  ${final_account:,.2f} vs ${ACCOUNT:,} start")

    overall = c1 and c2 and c3
    print(f"\n{'CLEARS THE BAR' if overall else 'DOES NOT CLEAR THE BAR'} (attempt 3 of 5)")

    return {
        "dsr": dsr_result.deflated_sharpe_ratio, "dsr_pass": c1,
        "strat_sharpe": strat_sharpe, "bench_sharpe": bench_sharpe, "sharpe_pass": c2_sharpe,
        "strat_dd": strat_max_dd, "bench_dd": bench_max_dd,
        "strat_return_per_dd": strat_return_per_dd, "bench_return_per_dd": bench_return_per_dd,
        "dd_pass": c2_dd,
        "final_account": final_account, "cost_pass": c3,
        "overall_pass": overall,
        "total_return": total_return, "benchmark_return": bench_total_return,
    }


if __name__ == "__main__":
    main()
