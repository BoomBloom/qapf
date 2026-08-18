"""Manual verification runner: python -m agents.backtest

Chains FOUR agents end to end: Agent 6 (macro regime) -> Agent 7 (alpha
signal) -> Qlib's verified backtest engine (Agent 9) -> Agent 4 (Deflated
Sharpe Ratio). Uses real yfinance data for signal generation and Qlib's own
bundled dataset for trade execution — see walkforward.py's module docstring
for why those are two different (both real) data sources.

Must guard qlib usage with `if __name__ == "__main__":` -- see
.claude/references/qlib-known-issues.md. Qlib's internal multiprocessing
re-imports this module in each worker under macOS's spawn method; without the
guard, that looks exactly like a 15-minute hang (this cost real time once).
"""

import logging

import pandas as pd
import qlib
import yfinance as yf

from .walkforward import WalkForwardBacktester

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "JPM", "V", "WMT", "KO", "PEP",
    "XOM", "CVX", "JNJ", "PG", "HD",
]

# Verified 2026-08-18: all 15 tickers have complete (965/965), gap-free
# coverage in Qlib's bundled US dataset over exactly this range.
DOWNLOAD_START = "2016-06-01"  # buffer before TEST_START for the 252-day momentum lookback
TEST_START = "2018-01-01"
TEST_END = "2020-10-30"  # last valid date in Qlib's free sample dataset's calendar


def download_universe(start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    print(f"Downloading {len(UNIVERSE)} tickers, {start} to {end} (yfinance)...")
    data = yf.download(UNIVERSE, start=start, end=end, interval="1d", progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")
    print(f"  {len(prices)} trading days\n")
    return prices, volumes


def test_no_lookahead_bias(prices, volumes):
    """The composition-level look-ahead test: Agents 6 and 7 are already
    individually verified point-in-time-safe, but the NEW glue code here
    (rebalance-date selection, forward-filling) could reintroduce the bug by,
    e.g., accidentally using the full price index instead of the as-of slice
    somewhere. Corrupt prices after the midpoint of the test window and check
    that every EARLIER rebalance's signal is unchanged.
    """
    bt = WalkForwardBacktester()
    rebalance_dates = bt._snap_to_trading_days(
        pd.date_range(TEST_START, TEST_END, freq="MS"), prices.index
    )
    midpoint = rebalance_dates[len(rebalance_dates) // 2]
    cache = bt.macro.fetch_all_series()

    clean_signal, clean_log = bt.build_signal_series(
        prices, volumes, rebalance_dates, pd.Timestamp(TEST_START), pd.Timestamp(TEST_END), cache
    )

    corrupted_prices = prices.copy()
    corrupted_volumes = volumes.copy()
    corrupted_prices.loc[corrupted_prices.index > midpoint] *= 100.0
    corrupted_volumes.loc[corrupted_volumes.index > midpoint] *= 100.0

    dirty_signal, dirty_log = bt.build_signal_series(
        corrupted_prices, corrupted_volumes, rebalance_dates,
        pd.Timestamp(TEST_START), pd.Timestamp(TEST_END), cache,
    )

    pre_midpoint_dates = [d for d in rebalance_dates if d <= midpoint]
    mismatches = []
    for rec_clean, rec_dirty in zip(clean_log, dirty_log):
        if pd.Timestamp(rec_clean.date) > midpoint:
            continue
        if rec_clean.longs != rec_dirty.longs or rec_clean.shorts != rec_dirty.shorts:
            mismatches.append(rec_clean.date)

    assert not mismatches, (
        f"LOOK-AHEAD BIAS in the walk-forward composition — corrupting prices "
        f"after {midpoint.date()} changed rebalances at/before it: {mismatches}"
    )
    print(
        f"Look-ahead test PASSED: corrupting all data after {midpoint.date()} "
        f"(the midpoint of {len(rebalance_dates)} rebalances) left all "
        f"{len(pre_midpoint_dates)} earlier rebalances' long/short lists identical."
    )


def main():
    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")
    prices, volumes = download_universe(DOWNLOAD_START, TEST_END)

    test_no_lookahead_bias(prices, volumes)

    print(f"\n=== Walk-forward backtest: {TEST_START} to {TEST_END} (monthly rebalance) ===")
    print("Chaining: Agent 6 (regime) -> Agent 7 (signal) -> Qlib backtest -> Agent 4 (DSR)\n")

    backtester = WalkForwardBacktester()
    report, _daily_returns = backtester.run(prices, volumes, test_start=TEST_START, test_end=TEST_END)

    print(f"Rebalances: {report.n_rebalances}")
    print(f"Universe:   {report.universe}\n")
    print("Regime path:")
    seen_regimes = set()
    for rec in report.rebalance_log:
        seen_regimes.add(rec.regime)
        print(f"  {rec.date}  {rec.regime:<28} {rec.risk_regime:<10} long={rec.longs}  short={rec.shorts}")

    print(f"\nDistinct regimes visited: {sorted(seen_regimes)}")
    assert len(seen_regimes) >= 2, (
        "Only one regime appeared across the whole test window (2018-2020, "
        "spans the COVID crash) -- the regime classifier is probably stuck."
    )
    print("Regime-variation check PASSED: the classifier moved across the COVID crash, not stuck.")

    print(f"\n=== Results ===")
    print(f"Initial account:    ${report.initial_account:,.2f}")
    print(f"Final account:      ${report.final_account:,.2f}")
    print(f"Total return:       {report.total_return:+.2%}")
    print(f"Benchmark return:   {report.benchmark_return:+.2%}  (equal-weight buy-and-hold, same universe)")
    print(f"Annualized Sharpe:  {report.annualized_sharpe:.3f}")
    print(f"Max drawdown:       {report.max_drawdown:.2%}")
    print(
        f"Deflated Sharpe:    {report.deflated_sharpe_ratio:.3f} "
        f"(assuming {report.deflated_sharpe_n_trials} trials — Agent 7's 4 hand-set factors)"
    )
    if report.deflated_sharpe_ratio > 0.95:
        print("  -> statistically significant at the 95% level even after deflating for multiple testing.")
    else:
        print("  -> NOT statistically significant after deflating for multiple testing.")
        print("     A good-looking Sharpe alone would have overstated confidence in this result.")

    print("\n=== Correctness checks ===")
    assert report.max_drawdown <= 0, "max drawdown should be <= 0 by construction"
    assert -1.0 <= report.total_return < 50.0, f"total_return {report.total_return} looks implausible"
    print("Bounds check PASSED: drawdown <= 0, total return in a plausible range.")


if __name__ == "__main__":
    main()
