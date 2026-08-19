"""Ticket 07 — does the strategy clear the validation bar on the 2008-2017 holdout?

Kept in .scratch/wayfinder-real-capital/ (not backend/agents/) because this is a
wayfinding validation exercise, reusable across attempts 1-5 of ticket 02's
budget with different factor configs, not permanent agent code -- backend/
agents/backtest/'s own __main__.py stays pinned to its documented 2018-2020
demonstration window (CLAUDE.md), untouched by this.

Bar (ticket 02, all three required):
  1. DSR > 0.95
  2. Beats equal-weight buy-and-hold on Sharpe AND return-per-unit-of-max-drawdown
  3. Profitable net of costs at $1,000 (first-pass: Qlib's own account=1000
     simulation, which naturally applies whole-share rounding and its built-in
     commission model; ticket 08 does the deeper Agent-11-cost-model dive)

Universe: 14 tickers, V excluded (IPO'd 2008, no pre-2008 history).
Window: 2008-01-01 to 2017-12-31, the untouched holdout established in ticket 02.
Attempt: 1 of 5 (n_trials=1 -- first-ever look at this window, per ticket 07).

Needs the __main__ guard: touches qlib (see .claude/references/qlib-known-issues.md).
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
]  # V excluded -- IPO'd March 2008, no history for the 252-day momentum lookback

DOWNLOAD_START = "2006-06-01"  # buffer before TEST_START for the 252-day momentum lookback
TEST_START = "2008-01-01"
TEST_END = "2017-12-31"
ACCOUNT = 1_000  # the actual target account size, not $1M
ATTEMPT_N_TRIALS = 1  # first-ever look at this window

# IBKR Lite's REAL commission structure (verified via web search 2026-08-19,
# interactivebrokers.com/compare-lite-pro): $0 commission on US stock trades,
# no account minimum. Qlib's own EXCHANGE_KWARGS default (min_cost=5, a flat
# $5-per-trade minimum) is what actually killed the first run of this ticket --
# with monthly rebalancing across ~7 position changes over 121 months, that
# flat minimum alone consumed 85% of a $1,000 account before the strategy got
# too poor to trade at all. That is a broker-assumption artifact, not a
# strategy failure, and not what the operator's actual target broker charges.
#
# The percentage-based open_cost/close_cost (spread proxy) are NOT the
# problem -- they scale with trade size and stayed unchanged. Only min_cost
# is corrected, from Qlib's generic default to IBKR Lite's verified $0.
IBKR_LITE_EXCHANGE_KWARGS = {
    "freq": "day",
    "limit_threshold": 0.095,
    "deal_price": "close",
    "open_cost": 0.0005,
    "close_cost": 0.0015,
    "min_cost": 0,  # IBKR Lite: $0 flat commission, verified -- was 5 (Qlib's generic default)
}


def _sharpe(returns: pd.Series, trading_days: int = 252) -> float:
    r = returns.dropna()
    if len(r) < 2 or r.std(ddof=1) == 0:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(trading_days))


def _max_drawdown(returns: pd.Series) -> float:
    equity = (1 + returns.dropna()).cumprod()
    return float(((equity - equity.cummax()) / equity.cummax()).min())


def main():
    from agents.alpha.combiner import AlphaCombiner
    from agents.backtest.walkforward import WalkForwardBacktester
    from agents.macro.regime import MacroRegimeClassifier

    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")

    print(f"Downloading {len(UNIVERSE)} tickers, {DOWNLOAD_START} to {TEST_END} (yfinance)...")
    data = yf.download(UNIVERSE, start=DOWNLOAD_START, end=TEST_END, interval="1d",
                        progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")
    print(f"  {len(prices)} trading days, coverage check:")
    for t in UNIVERSE:
        n_valid = prices[t].loc[TEST_START:TEST_END].notna().sum() if t in prices.columns else 0
        n_total = len(prices.loc[TEST_START:TEST_END])
        flag = "" if n_valid == n_total else "  <-- INCOMPLETE"
        print(f"    {t:6} {n_valid}/{n_total}{flag}")

    print(f"\n=== Running walk-forward backtest: {TEST_START} to {TEST_END} (attempt 1/5) ===")
    bt = WalkForwardBacktester()
    report, daily_returns = bt.run(
        prices, volumes, test_start=TEST_START, test_end=TEST_END,
        account=ACCOUNT, n_trials=ATTEMPT_N_TRIALS,
        exchange_kwargs=IBKR_LITE_EXCHANGE_KWARGS,
    )

    # Benchmark's own Sharpe and max drawdown -- never computed in the 2018-2020
    # run, so the risk-adjusted comparison the bar actually demands has never
    # been made until now. Recomputed here rather than threading a 3rd return
    # value through walkforward.py, since it's the identical trivial formula
    # walkforward.py itself uses internally (equal-weight mean of pct_change).
    test_prices = prices.loc[TEST_START:TEST_END]
    benchmark_returns = test_prices.pct_change().mean(axis=1).fillna(0)
    bench_sharpe = _sharpe(benchmark_returns)
    bench_max_dd = _max_drawdown(benchmark_returns)

    strat_max_dd = report.max_drawdown
    strat_sharpe = report.annualized_sharpe
    strat_return_per_dd = strat_sharpe / abs(strat_max_dd) if strat_max_dd != 0 else float("nan")
    bench_return_per_dd = bench_sharpe / abs(bench_max_dd) if bench_max_dd != 0 else float("nan")

    print(f"\n=== Results: {TEST_START} to {TEST_END}, {report.n_rebalances} rebalances, "
          f"${ACCOUNT:,} account ===\n")
    print(f"{'':24}{'Strategy':>14}{'Benchmark':>14}")
    print(f"{'Total return':24}{report.total_return:>+14.2%}{report.benchmark_return:>+14.2%}")
    print(f"{'Annualized Sharpe':24}{strat_sharpe:>14.3f}{bench_sharpe:>14.3f}")
    print(f"{'Max drawdown':24}{strat_max_dd:>14.2%}{bench_max_dd:>14.2%}")
    print(f"{'Return per unit DD':24}{strat_return_per_dd:>14.3f}{bench_return_per_dd:>14.3f}")
    print(f"\nDeflated Sharpe Ratio: {report.deflated_sharpe_ratio:.4f} "
          f"(n_trials={report.deflated_sharpe_n_trials})")
    print(f"Final account: ${report.final_account:,.2f} (started ${ACCOUNT:,})")

    print("\n=== Bar check (all three required) ===")
    c1 = report.deflated_sharpe_ratio > 0.95
    c2_sharpe = strat_sharpe > bench_sharpe
    c2_dd = strat_return_per_dd > bench_return_per_dd
    c2 = c2_sharpe and c2_dd
    c3 = report.final_account > ACCOUNT  # first-pass: Qlib's own cost-inclusive account P&L at $1,000

    print(f"  [{'PASS' if c1 else 'FAIL'}] DSR > 0.95:                        "
          f"{report.deflated_sharpe_ratio:.4f}")
    print(f"  [{'PASS' if c2_sharpe else 'FAIL'}] Beats benchmark Sharpe:            "
          f"{strat_sharpe:.3f} vs {bench_sharpe:.3f}")
    print(f"  [{'PASS' if c2_dd else 'FAIL'}] Beats benchmark return/max-DD:      "
          f"{strat_return_per_dd:.3f} vs {bench_return_per_dd:.3f}")
    print(f"  [{'PASS' if c3 else 'FAIL'}] Profitable net of costs at $1,000:  "
          f"${report.final_account:,.2f} vs ${ACCOUNT:,} start")

    overall = c1 and c2 and c3
    print(f"\n{'CLEARS THE BAR' if overall else 'DOES NOT CLEAR THE BAR'} "
          f"(attempt 1 of 5)")

    print("\n=== Standing caveats (regardless of outcome) ===")
    print("  - Universe is survivorship-biased: 14 names hand-picked in 2026 with knowledge")
    print("    of which became winners (ticket 10). Inflates results on any window.")
    print("  - Drawdown measured on daily closes, not intraday equity (ticket 11).")
    print("    True intraday drawdown is worse than reported here.")
    print("  - Condition 3 is a first-pass check via Qlib's own account simulation,")
    print("    not yet Agent 11's full square-root-impact/TWAP cost model (ticket 08).")

    return {
        "dsr": report.deflated_sharpe_ratio, "dsr_pass": c1,
        "strat_sharpe": strat_sharpe, "bench_sharpe": bench_sharpe, "sharpe_pass": c2_sharpe,
        "strat_dd": strat_max_dd, "bench_dd": bench_max_dd,
        "strat_return_per_dd": strat_return_per_dd, "bench_return_per_dd": bench_return_per_dd,
        "dd_pass": c2_dd,
        "final_account": report.final_account, "cost_pass": c3,
        "overall_pass": overall,
        "total_return": report.total_return, "benchmark_return": report.benchmark_return,
        "n_rebalances": report.n_rebalances,
    }


if __name__ == "__main__":
    main()
