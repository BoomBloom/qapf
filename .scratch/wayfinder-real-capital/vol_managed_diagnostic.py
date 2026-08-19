"""Diagnostic, NOT a ticket-02 validation attempt -- consumes no attempt
budget. Tests docs/research/viable-alpha-families.md's #1-ranked idea
(volatility-managed exposure, Moreira & Muir JF 2017) as cheap post-
processing on the SAME real daily-returns series ticket 07's attempt 1
already produced (same universe, same window, same flat weights, same
IBKR-Lite cost model) -- no new backtest run, no new data.

f^sigma_t = min(target_vol / realized_vol_t, max_leverage) * f_t

Moreira & Muir's construction (eq. 1-2), with max_leverage=1.0 -- the
long-only-and-cash-compatible variant their own paper's section III.B
explicitly tests and reports still working under. realized_vol_t is the
prior 22-trading-day (their eq. 2 window) realized daily-return volatility
of the STRATEGY'S OWN return series (portfolio-level scaling, matching
their construction and K&S's simpler w=sigma*/sigma form), not per-name.

The research document's own falsification bar: "If the Sharpe does not
improve and the max drawdown does not shrink... abandon it." Reported
here exactly as it comes out, not cherry-picked.
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
]  # same as validate_bar.py: V excluded, IPO'd 2008

DOWNLOAD_START = "2006-06-01"
TEST_START = "2008-01-01"
TEST_END = "2017-12-31"
ACCOUNT = 1_000

REALIZED_VOL_WINDOW = 22  # Moreira & Muir eq. 2
MAX_LEVERAGE = 1.0  # long-only-and-cash compatible variant (their sec III.B)

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


def apply_vol_management(daily_returns: pd.Series, target_vol: float | None = None) -> pd.Series:
    """target_vol defaults to the series' own unconditional daily vol, so the
    scaled series has (approximately) the same unconditional standard
    deviation as the original -- matching Moreira & Muir's own normalization
    ("c is chosen so the managed portfolio has the same unconditional
    standard deviation as buy-and-hold"), just applied to this strategy's
    return series instead of buy-and-hold."""
    r = daily_returns.dropna()
    if target_vol is None:
        target_vol = float(r.std(ddof=1))

    realized_vol = r.rolling(REALIZED_VOL_WINDOW).std(ddof=1).shift(1)  # t-1 info only, no look-ahead
    leverage = (target_vol / realized_vol).clip(upper=MAX_LEVERAGE).fillna(0.0)
    scaled = r * leverage
    return scaled


def main():
    from agents.backtest.walkforward import WalkForwardBacktester

    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")

    print(f"Downloading {len(UNIVERSE)} tickers, {DOWNLOAD_START} to {TEST_END} (yfinance)...")
    data = yf.download(UNIVERSE, start=DOWNLOAD_START, end=TEST_END, interval="1d",
                        progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")

    print(f"\n=== Reproducing ticket 07 attempt 1's real daily-returns series ===")
    bt = WalkForwardBacktester()
    report, daily_returns = bt.run(
        prices, volumes, test_start=TEST_START, test_end=TEST_END,
        account=ACCOUNT, n_trials=1, exchange_kwargs=IBKR_LITE_EXCHANGE_KWARGS,
    )
    print(f"  Reproduced: total_return={report.total_return:+.2%}, "
          f"sharpe={report.annualized_sharpe:.3f}, max_dd={report.max_drawdown:.2%}")
    print(f"  (Ticket 07's recorded attempt 1: +95.28%, sharpe=0.564, max_dd=-36.74% -- "
          f"small differences here are live-yfinance-data drift since that run, not a bug.)")

    print(f"\n=== Applying volatility-managed scaling (22d realized vol, max_leverage={MAX_LEVERAGE}) ===")
    scaled_returns = apply_vol_management(daily_returns)

    orig_sharpe, orig_dd = _sharpe(daily_returns), _max_drawdown(daily_returns)
    orig_total_return = float((1 + daily_returns.dropna()).prod() - 1)
    scaled_sharpe, scaled_dd = _sharpe(scaled_returns), _max_drawdown(scaled_returns)
    scaled_total_return = float((1 + scaled_returns.dropna()).prod() - 1)

    test_prices = prices.loc[TEST_START:TEST_END]
    bench_returns = test_prices.pct_change().mean(axis=1).fillna(0)
    bench_sharpe, bench_dd = _sharpe(bench_returns), _max_drawdown(bench_returns)

    print(f"\n{'':28}{'Original':>14}{'Vol-managed':>14}{'Benchmark':>14}")
    print(f"{'Total return':28}{orig_total_return:>+14.2%}{scaled_total_return:>+14.2%}{report.benchmark_return:>+14.2%}")
    print(f"{'Annualized Sharpe':28}{orig_sharpe:>14.3f}{scaled_sharpe:>14.3f}{bench_sharpe:>14.3f}")
    print(f"{'Max drawdown':28}{orig_dd:>14.2%}{scaled_dd:>14.2%}{bench_dd:>14.2%}")

    print(f"\n=== Falsification check (docs/research/viable-alpha-families.md #1) ===")
    sharpe_improved = scaled_sharpe > orig_sharpe
    dd_improved = abs(scaled_dd) < abs(orig_dd)
    print(f"  Sharpe improved: {sharpe_improved}  ({orig_sharpe:.3f} -> {scaled_sharpe:.3f})")
    print(f"  Max drawdown improved: {dd_improved}  ({orig_dd:.2%} -> {scaled_dd:.2%})")

    if sharpe_improved and dd_improved:
        print("\n  RESULT: both improved -- worth formalizing as a real ticket 07 attempt, "
              "on the PIT-corrected universe (ticket 13), not just this diagnostic series.")
    elif sharpe_improved or dd_improved:
        print("\n  RESULT: partial improvement -- one metric better, one not. Worth a closer look "
              "before committing a formal attempt, not a clean pass.")
    else:
        print("\n  RESULT: neither improved. Per the research document's own falsification bar, "
              "this idea is abandoned at this problem size -- move to #2/#3 in the shortlist instead "
              "of formalizing this as an attempt.")


if __name__ == "__main__":
    main()
