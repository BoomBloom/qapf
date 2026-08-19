"""Walk-forward backtest: Agent 6 (regime) -> Agent 7 (signal) -> Qlib's
verified backtest engine -> Agent 4 (Deflated Sharpe Ratio), using only
point-in-time-available data at every rebalance.

Runs over a historical window ending 2020-10-30, for a specific, verified
reason rather than an arbitrary choice: Qlib's free bundled dataset — the only
price source confirmed compatible with Qlib's execution engine, per
.claude/references/qlib-known-issues.md — has a calendar that stops at
2020-11-10. Mixing in fresh yfinance prices via `Exchange(extra_quote=...)`
for the same tickers Qlib already covers risks duplicate-index conflicts in
its internal quote store; using Qlib's own bundled prices for execution avoids
that entirely, and this project already verified (2026-08-18) that all 15
universe tickers have complete, gap-free coverage in that dataset from
2017-01-03 through 2020-10-30. A backtest is inherently a historical exercise,
and this window happens to span the COVID crash — a genuinely useful stress
period for a regime-conditional strategy, not a limitation to apologize for.
"""

import logging

import numpy as np
import pandas as pd
from qlib.backtest import backtest as qlib_backtest
from qlib.backtest import executor as qlib_executor
from qlib.contrib.strategy import TopkDropoutStrategy

from agents.alpha.combiner import AlphaCombiner
from agents.macro.regime import MacroRegimeClassifier
from agents.stats.toolkit import ProbabilityStatisticsToolkit

from .schemas import BacktestReport, RebalanceRecord

logger = logging.getLogger(__name__)

EXCHANGE_KWARGS = {
    "freq": "day",
    "limit_threshold": 0.095,
    "deal_price": "close",
    "open_cost": 0.0005,
    "close_cost": 0.0015,
    "min_cost": 5,
}


class WalkForwardBacktester:
    def __init__(self):
        self.macro = MacroRegimeClassifier()
        self.combiner = AlphaCombiner()
        self.stats = ProbabilityStatisticsToolkit()

    def _snap_to_trading_days(self, dates, trading_days: pd.DatetimeIndex) -> list[pd.Timestamp]:
        """Move each target date forward to the next actual trading day."""
        snapped = []
        for d in dates:
            candidates = trading_days[trading_days >= d]
            if len(candidates) > 0:
                snapped.append(candidates[0])
        return sorted(set(snapped))

    def build_signal_series(
        self,
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        rebalance_dates: list[pd.Timestamp],
        test_start: pd.Timestamp,
        test_end: pd.Timestamp,
        macro_series_cache: dict[str, pd.Series],
    ) -> tuple[pd.Series, list[RebalanceRecord]]:
        """At each rebalance date, compute the regime (Agent 6) and signal
        (Agent 7) using ONLY data at or before that date, then hold that
        signal constant until the next rebalance -- exactly what "monthly
        rebalancing" means in live trading. `prices`/`volumes` may include
        history before `test_start` (needed for momentum's lookback); only
        `[test_start, test_end]` is used for the day-by-day signal series.
        """
        bundles = []
        rebalance_log: list[RebalanceRecord] = []
        for rdate in rebalance_dates:
            assessment = self.macro.assess(as_of=rdate, series_cache=macro_series_cache)
            bundle = self.combiner.generate(
                prices, volumes, assessment.regime, assessment.risk_regime, as_of=rdate
            )
            bundles.append((rdate, bundle))
            rebalance_log.append(
                RebalanceRecord(
                    date=str(rdate.date()),
                    regime=assessment.regime.value,
                    risk_regime=assessment.risk_regime.value,
                    longs=[s.ticker for s in bundle.signals if s.signal > 0.2],
                    shorts=[s.ticker for s in bundle.signals if s.signal < -0.2],
                )
            )

        test_days = prices.loc[test_start:test_end].index
        signal_dict: dict[tuple[str, pd.Timestamp], float] = {}
        for day in test_days:
            applicable = [b for b in bundles if b[0] <= day]
            if not applicable:
                continue
            _, bundle = applicable[-1]
            for sig in bundle.signals:
                signal_dict[(sig.ticker, day)] = sig.signal

        signal = pd.Series(signal_dict, dtype=float)
        signal.index = pd.MultiIndex.from_tuples(signal.index, names=["instrument", "datetime"])
        return signal, rebalance_log

    def run(
        self,
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        test_start: str,
        test_end: str,
        rebalance_freq: str = "MS",
        topk: int = 5,
        n_drop: int = 2,
        account: float = 1_000_000,
        n_trials: int = 4,
    ) -> tuple[BacktestReport, pd.Series]:
        """`n_trials=4` reflects the 4 hand-set factors Agent 7 combines; it is
        a stated assumption, not a measured count of strategies actually
        tried, and is surfaced in the report rather than hidden inside a
        single opaque Sharpe number.

        Returns `(report, daily_returns)` -- the report is the summary, but
        the raw daily-returns series is real signal other agents need too
        (Agent 10's CRO cross-checks its own drawdown math against it; Agent
        14's Model Risk will want the same series). Returning it here avoids
        every future consumer re-deriving it by duplicating this method's
        Qlib wiring."""
        test_start_ts, test_end_ts = pd.Timestamp(test_start), pd.Timestamp(test_end)

        candidate_dates = pd.date_range(test_start_ts, test_end_ts, freq=rebalance_freq)
        rebalance_dates = self._snap_to_trading_days(candidate_dates, prices.index)
        if not rebalance_dates or rebalance_dates[0] > test_start_ts:
            first_day = prices.loc[test_start_ts:].index[0]
            rebalance_dates = [first_day] + rebalance_dates

        # Fetch each FRED series once; every rebalance's assess() call slices
        # this same cache rather than re-hitting FRED (~7 series x N rebalances
        # of redundant network calls otherwise).
        #
        # start_date is derived from test_start, NOT fetch_all_series()'s own
        # 2015-01-01 default. That default silently has zero observations
        # before 2015, so any test_start earlier than that (e.g. the 2008-2017
        # validation window) previously failed with "No macro series could be
        # fetched" -- correct-looking code, silently wrong for a valid input
        # it had never been run against. A 3-year buffer covers regime.py's
        # YoY calculations comfortably without hardcoding an arbitrary early
        # constant.
        macro_start = str((test_start_ts - pd.DateOffset(years=3)).date())
        macro_series_cache = self.macro.fetch_all_series(start_date=macro_start)

        signal, rebalance_log = self.build_signal_series(
            prices, volumes, rebalance_dates, test_start_ts, test_end_ts, macro_series_cache
        )

        strategy = TopkDropoutStrategy(signal=signal, topk=topk, n_drop=n_drop)

        # Benchmark: equal-weight buy-and-hold of the same universe, computed
        # in plain pandas. Qlib's own benchmark calc evaluates
        # "$close/Ref($close,1)-1" internally, which silently returns empty
        # under the current numpy/pandas stack (qlib-known-issues.md) --
        # passing a pre-built Series bypasses that broken path entirely.
        test_prices = prices.loc[test_start_ts:test_end_ts]
        benchmark_returns = test_prices.pct_change().mean(axis=1).fillna(0)

        report_dict, _indicator_dict = qlib_backtest(
            start_time=test_start,
            end_time=test_end,
            strategy=strategy,
            executor=qlib_executor.SimulatorExecutor(time_per_step="day", generate_portfolio_metrics=True),
            account=account,
            benchmark=benchmark_returns,
            exchange_kwargs=EXCHANGE_KWARGS,
        )
        report_df, _positions = report_dict["1day"]

        daily_returns = report_df["return"]
        equity = (1 + daily_returns).cumprod()
        running_max = equity.cummax()
        drawdown = (equity - running_max) / running_max
        max_drawdown = float(drawdown.min())

        ann_sharpe = (
            float(daily_returns.mean() / daily_returns.std(ddof=1) * np.sqrt(252))
            if daily_returns.std(ddof=1) > 0
            else 0.0
        )
        dsr_result = self.stats.deflated_sharpe_ratio(daily_returns, n_trials=n_trials)

        report = BacktestReport(
            universe=list(prices.columns),
            start=test_start,
            end=test_end,
            n_rebalances=len(rebalance_dates),
            initial_account=account,
            final_account=float(report_df["account"].iloc[-1]),
            total_return=float(report_df["account"].iloc[-1] / account - 1),
            benchmark_return=float((1 + report_df["bench"]).prod() - 1),
            annualized_sharpe=ann_sharpe,
            max_drawdown=max_drawdown,
            deflated_sharpe_ratio=dsr_result.deflated_sharpe_ratio,
            deflated_sharpe_n_trials=n_trials,
            rebalance_log=rebalance_log,
        )
        return report, daily_returns
