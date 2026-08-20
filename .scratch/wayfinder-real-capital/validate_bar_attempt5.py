"""Ticket 07 — attempt 5 of 5 (final attempt in ticket 02's budget).

The last genuinely different, evidence-backed idea from
docs/research/viable-alpha-families.md's shortlist: #3, absolute (time-
series) momentum with a cash leg. Chosen deliberately over a fourth risk-
scaling variant -- attempts 3 and 4 already showed that family has
plateaued (Sharpe stuck at 0.72-0.74 across two different refinements)
while DSR keeps falling purely from the honest trial-count cost. Antonacci's
own published numbers for exactly this long-only-plus-cash-leg construction
(Sharpe 1.07 vs 0.50 benchmark, max drawdown -10.92% vs -26.77%) are the
strongest real evidence in the shortlist for a genuine, not marginal, jump --
which is what's needed to clear n_trials=5's larger DSR penalty.

IMPLEMENTATION, STATED PLAINLY: the backtest engine (Qlib's
TopkDropoutStrategy) always holds ~topk names every period by construction --
it has no native "go to cash when nothing qualifies" behavior, the same
architecture gap attempt 4's docstring already flagged. Rather than rebuild
the execution engine for the last attempt, this uses K&S section 4.1.2's own
stated construction directly: "buy only if the market index is above its
100-200 day moving average, otherwise hold... cash." Applied as a post-
processing overlay on the return series -- same honest, low-risk pattern
attempt 2's volatility-managed exposure already used and that this project
has verified works cleanly. 200 trading days is K&S's own canonical choice,
not tuned against this data -- one new free parameter, not selected by
grid search.

Builds on the full current production baseline (Yang-Zhang low_volatility,
landed in attempt 3; volatility-managed exposure, landed in attempt 2) --
this is the fifth and final variable added to that standing baseline, not a
fresh start.
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
ATTEMPT_N_TRIALS = 5

REALIZED_VOL_WINDOW = 22
MAX_LEVERAGE = 1.0
TREND_MA_WINDOW = 200  # K&S 4.1.2's own canonical 100-200 day choice

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


def apply_absolute_momentum_overlay(scaled_returns: pd.Series, market_index: pd.Series) -> pd.Series:
    """K&S 4.1.2: invested when the market index is above its 200-day MA,
    cash otherwise. `market_index` must cover a real history BEFORE
    scaled_returns.index[0] so the MA isn't truncated at the test start --
    the same buffer discipline MOMENTUM_LONG already relies on elsewhere in
    this project. The MA and the invested/cash decision are both shifted by
    one day (`.shift(1)`) so today's decision only ever uses yesterday's
    close -- no look-ahead."""
    ma = market_index.rolling(TREND_MA_WINDOW).mean()
    invested = (market_index > ma).shift(1).reindex(scaled_returns.index).fillna(False)
    return scaled_returns.where(invested, 0.0)


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

    print(f"\n=== Running walk-forward backtest (Yang-Zhang + vol-managed baseline, attempt 5/5) ===")
    bt = WalkForwardBacktester()
    _, daily_returns = bt.run(
        prices, volumes, test_start=TEST_START, test_end=TEST_END,
        account=ACCOUNT, n_trials=ATTEMPT_N_TRIALS, exchange_kwargs=IBKR_LITE_EXCHANGE_KWARGS,
        opens=opens, highs=highs, lows=lows,
    )
    vol_managed = apply_vol_management(daily_returns)

    print(f"\n=== Applying absolute-momentum overlay ({TREND_MA_WINDOW}d market MA filter) ===")
    # Full-history equal-weight index (DOWNLOAD_START onward) so the 200-day
    # MA is real, not truncated, at TEST_START -- same buffer discipline as
    # every other lookback in this project.
    full_benchmark_returns = prices.pct_change().mean(axis=1).fillna(0)
    market_index = (1 + full_benchmark_returns).cumprod()
    scaled = apply_absolute_momentum_overlay(vol_managed, market_index)

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

    pct_days_in_cash = float((scaled.loc[TEST_START:TEST_END] == 0).mean())

    print(f"\n=== Results: {TEST_START} to {TEST_END} (absolute momentum overlay) ===\n")
    print(f"{'':24}{'Strategy':>14}{'Benchmark':>14}")
    print(f"{'Total return':24}{total_return:>+14.2%}{bench_total_return:>+14.2%}")
    print(f"{'Annualized Sharpe':24}{strat_sharpe:>14.3f}{bench_sharpe:>14.3f}")
    print(f"{'Max drawdown':24}{strat_max_dd:>14.2%}{bench_max_dd:>14.2%}")
    print(f"{'Return per unit DD':24}{strat_return_per_dd:>14.3f}{bench_return_per_dd:>14.3f}")
    print(f"\nDays in cash (trend filter off): {pct_days_in_cash:.1%}")
    print(f"Deflated Sharpe Ratio: {dsr_result.deflated_sharpe_ratio:.4f} (n_trials={ATTEMPT_N_TRIALS})")
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
    print(f"\n{'CLEARS THE BAR' if overall else 'DOES NOT CLEAR THE BAR'} (attempt 5 of 5 -- FINAL)")

    return {
        "dsr": dsr_result.deflated_sharpe_ratio, "dsr_pass": c1,
        "strat_sharpe": strat_sharpe, "bench_sharpe": bench_sharpe, "sharpe_pass": c2_sharpe,
        "strat_dd": strat_max_dd, "bench_dd": bench_max_dd,
        "strat_return_per_dd": strat_return_per_dd, "bench_return_per_dd": bench_return_per_dd,
        "dd_pass": c2_dd,
        "final_account": final_account, "cost_pass": c3,
        "overall_pass": overall,
        "total_return": total_return, "benchmark_return": bench_total_return,
        "pct_days_in_cash": pct_days_in_cash,
    }


if __name__ == "__main__":
    main()
