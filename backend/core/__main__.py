"""Manual verification runner: python -m core

Two things need proving, both against real data, not mocks:

1. The full pipeline (macro -> alpha -> portfolio -> risk_gate -> execution ->
   compliance -> cio_synthesis) runs end to end and produces a real CIO memo,
   in the honest "no trading history yet" state every operator starts in.
2. Wayfinder ticket 12's actual requirement: a real return series known to
   breach the CRO's limit halts the pipeline and emits ZERO orders, while a
   calm sub-window of the same real data still produces orders normally.
   Reuses Agent 9's real 2018-2020 backtest (which spans the COVID crash) as
   the return-history fixture -- the same "test fixture, not a risk-engine
   dependency" pattern backend/risk/__main__.py already established, not a
   new one invented here.

Needs the `if __name__ == "__main__":` guard -- both LLM calls and the reused
qlib backtest touch things that don't tolerate macOS's spawn-based
multiprocessing re-importing this module (see .claude/references/
qlib-known-issues.md).
"""

import logging

import pandas as pd
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "JPM", "V", "WMT", "KO", "PEP",
    "XOM", "CVX", "JNJ", "PG", "HD",
]


def download_universe() -> tuple[pd.DataFrame, pd.DataFrame]:
    print(f"Downloading {len(UNIVERSE)} tickers (3y daily, yfinance)...")
    data = yf.download(UNIVERSE, period="3y", interval="1d", progress=False, auto_adjust=True)
    prices = data["Close"].dropna(how="all")
    volumes = data["Volume"].dropna(how="all")
    print(f"  {len(prices)} trading days, {prices.shape[1]} tickers\n")
    return prices, volumes


def test_live_pipeline_risk_blind(prices, volumes):
    """Today's honest state: no paper/live trading has happened yet, so there
    is no real return history for the CRO to assess. Confirms the pipeline
    completes anyway (risk-blind, not halted -- those are different things)
    and every node fires, including the one real LLM call."""
    from .state_graph import QAPFOrchestrator

    orch = QAPFOrchestrator()
    result = orch.run(
        universe=UNIVERSE, prices=prices, volumes=volumes, portfolio_value=1_000_000,
    )
    assert not result.halted, "must not halt with no returns history -- risk-blind is not the same as failed"
    assert result.macro_assessment is not None
    assert result.signal_bundle is not None
    assert result.allocation is not None
    assert result.execution_plan is not None, "risk-blind run must still reach execution"
    assert result.compliance_report is not None
    assert result.cio_memo, "CIO synthesis must produce real text"

    print("=== Risk-blind live pipeline PASSED ===")
    print(f"Regime: {result.macro_assessment.regime.value} | "
          f"Allocation: {result.allocation.n_positions} positions, "
          f"{result.allocation.gross_exposure:.0%} gross")
    print(f"Execution: {result.execution_plan.n_orders} orders, {result.execution_plan.cost_bps:.1f}bp")
    print(f"Compliance: clean={result.compliance_report.clean}")
    print(f"\n--- CIO memo ---\n{result.cio_memo}\n")
    return result


def test_kill_switch_enforcement():
    """Ticket 12's real requirement. Reuses Agent 9's actual 2018-2020
    backtest returns (spans the COVID crash) rather than synthesizing a fake
    breach -- `assess_history` finds the FIRST real date the 20%/6% limits
    from ticket 01 would have fired, then:
      - truncating the returns series through that date must halt the
        pipeline and emit zero orders (fails closed).
      - truncating to strictly before that date (guaranteed calm, since it's
        the FIRST breach by construction) must NOT halt and must still
        produce orders.
    """
    import qlib

    from agents.backtest.__main__ import DOWNLOAD_START, TEST_END, TEST_START
    from agents.backtest.__main__ import download_universe as bt_download_universe
    from agents.backtest.walkforward import WalkForwardBacktester
    from risk.monitor import RiskMonitor
    from risk.schemas import RiskLimits

    from .state_graph import LIVE_RISK_LIMITS, QAPFOrchestrator

    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")
    prices, volumes = bt_download_universe(DOWNLOAD_START, TEST_END)
    report, daily_returns = WalkForwardBacktester().run(prices, volumes, test_start=TEST_START, test_end=TEST_END)
    print(f"Agent 9 backtest max drawdown: {report.max_drawdown:.2%} "
          f"(limit: {LIVE_RISK_LIMITS.max_drawdown_pct:.0%})")

    history = RiskMonitor(RiskLimits(
        max_drawdown_pct=LIVE_RISK_LIMITS.max_drawdown_pct,
        max_daily_loss_pct=LIVE_RISK_LIMITS.max_daily_loss_pct,
    )).assess_history(daily_returns)
    breach_dates = [a.as_of for a in history if a.kill_switch_triggered]
    assert breach_dates, (
        f"expected at least one real breach date given max drawdown "
        f"{report.max_drawdown:.2%} against a {LIVE_RISK_LIMITS.max_drawdown_pct:.0%} limit"
    )
    first_breach = pd.Timestamp(breach_dates[0])
    print(f"First real breach date: {first_breach.date()} "
          f"({len(breach_dates)}/{len(history)} days in breach over the full window)")

    orch = QAPFOrchestrator()

    breaching_returns = daily_returns.loc[:first_breach]
    breach_result = orch.run(
        universe=list(prices.columns), prices=prices, volumes=volumes,
        portfolio_value=1_000_000, daily_returns=breaching_returns,
    )
    assert breach_result.halted, "expected the pipeline to halt at the first real breach date"
    assert breach_result.execution_plan is None, "a halted run must emit ZERO orders -- fails closed"
    assert breach_result.compliance_report is None, "compliance must not run on a halted pipeline"
    assert breach_result.cio_memo, "CIO memo must still explain the halt"
    print("Kill-switch enforcement PASSED: breaching returns halted the pipeline, zero orders emitted.")

    calm_returns = daily_returns.loc[daily_returns.index < first_breach]
    assert not calm_returns.empty, "no calm data exists before the first breach -- test fixture too short"
    calm_result = orch.run(
        universe=list(prices.columns), prices=prices, volumes=volumes,
        portfolio_value=1_000_000, daily_returns=calm_returns,
    )
    assert not calm_result.halted, "calm (pre-breach) data must not halt the pipeline"
    assert calm_result.execution_plan is not None, "a calm run must still reach execution and emit orders"
    print(f"Calm-window control PASSED: {len(calm_returns)} pre-breach days -> "
          f"no halt, {calm_result.execution_plan.n_orders} orders generated.")


def main():
    print("=== Agent 1 (Lead Orchestrator) verification ===\n")
    prices, volumes = download_universe()
    test_live_pipeline_risk_blind(prices, volumes)

    print("\n=== Cross-checking kill-switch enforcement against Agent 9's real backtest ===")
    test_kill_switch_enforcement()


if __name__ == "__main__":
    main()
