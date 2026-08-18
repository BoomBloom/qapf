"""Generate the dashboard's data snapshot by running the real pipeline.

Writes frontend/data/snapshot.json. Every number in the UI comes from here, so
the dashboard shows what the agents actually computed — no mock values, per
CLAUDE.md's no-placeholder-data rule.

Run: cd backend && python -m dashboard.export
Needs the __main__ guard because it reaches Agent 9, which touches qlib.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

UNIVERSE = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "JPM", "V", "WMT",
            "KO", "PEP", "XOM", "CVX", "JNJ", "PG", "HD"]
SECTORS = {
    "AAPL": "tech", "MSFT": "tech", "GOOGL": "tech", "AMZN": "tech", "NVDA": "tech",
    "JPM": "financials", "V": "financials",
    "WMT": "staples", "KO": "staples", "PEP": "staples", "PG": "staples",
    "XOM": "energy", "CVX": "energy", "JNJ": "healthcare", "HD": "discretionary",
}
PORTFOLIO_VALUE = 1_000_000
OUT = Path(__file__).resolve().parents[2] / "frontend" / "data" / "snapshot.json"

# Declared, not inferred — the dashboard should state plainly what is built,
# what is blocked, and what is deliberately deferred.
ROSTER = [
    (1, "Lead Orchestrator", "blocked", "Needs a funded LLM provider"),
    (2, "Portfolio Manager", "live", "Qlib optimizer + shrinkage covariance"),
    (3, "Academic Research", "live", "arXiv + GitHub ingestion"),
    (4, "Probability & Statistics", "live", "ADF/KPSS, cointegration, Deflated Sharpe"),
    (5, "Quantum & Optimization", "deferred", "No measured problem classical methods fail"),
    (6, "Fundamental & Macro", "live", "Keyless FRED regime classification"),
    (7, "Alpha Mining", "live", "Regime-conditional factor signals"),
    (8, "Quant Software Engineering", "blocked", "Needs a funded LLM provider"),
    (9, "Backtesting & Validation", "live", "Walk-forward on Qlib's engine"),
    (10, "Chief Risk Officer", "live", "VaR/CVaR + kill switch, isolation enforced"),
    (11, "Execution & Microstructure", "live", "TWAP/VWAP + square-root impact"),
    (12, "Operations & Settlement", "live", "Reconciliation + PnL attribution"),
    (13, "Compliance & Surveillance", "live", "Conduct rules + audit trail"),
    (14, "Model Risk & Validation", "live", "Independently challenges Agent 9"),
    (15, "Data Infrastructure", "live", "Feed staleness, gaps, schema drift"),
    (16, "Treasury & Funding", "deferred", "No margin or multi-currency exposure yet"),
]


def build_snapshot() -> dict:
    import qlib

    from agents.alpha.combiner import REGIME_FACTOR_WEIGHTS, AlphaCombiner
    from agents.backtest.walkforward import WalkForwardBacktester
    from agents.compliance.surveillance import ComplianceSurveillance
    from agents.datainfra.monitor import DataHealthMonitor, check_gaps, check_staleness
    from agents.execution.planner import ExecutionPlanner
    from agents.macro.fred_client import FredClient
    from agents.macro.regime import MacroRegimeClassifier
    from agents.modelrisk.validator import ModelRiskValidator
    from agents.operations.reconciler import OperationsReconciler
    from agents.portfolio.allocator import PortfolioAllocator
    from risk.metrics import historical_cvar, historical_var, max_drawdown, parametric_var

    logger.info("Downloading market data...")
    data = yf.download(UNIVERSE, period="3y", interval="1d", progress=False, auto_adjust=True)
    prices, volumes = data["Close"].dropna(how="all"), data["Volume"].dropna(how="all")

    # --- Agent 6: macro regime ------------------------------------------
    logger.info("Agent 6: macro regime")
    macro = MacroRegimeClassifier()
    assessment = macro.assess()

    # --- Agent 7: alpha signals -----------------------------------------
    logger.info("Agent 7: alpha signals")
    bundle = AlphaCombiner().generate(prices, volumes, assessment.regime, assessment.risk_regime)

    # --- Agent 2: allocation --------------------------------------------
    logger.info("Agent 2: allocation")
    alloc = PortfolioAllocator().allocate(bundle, prices, assessment.regime, assessment.risk_regime)

    # --- Agent 11: execution --------------------------------------------
    logger.info("Agent 11: execution plan")
    plan = ExecutionPlanner(algo="vwap").plan(alloc, prices, volumes, PORTFOLIO_VALUE)

    # --- Agent 12: reconciliation ---------------------------------------
    logger.info("Agent 12: reconciliation")
    targets = {p.ticker: p.weight for p in alloc.positions}
    actual = {o.ticker: float(int(o.shares)) * o.reference_price / PORTFOLIO_VALUE
              for o in plan.orders}
    recon = OperationsReconciler().reconcile(
        target_weights=targets, actual_weights=actual,
        period_returns=prices.pct_change().iloc[-1].to_dict(),
        execution_cost=plan.total_cost, portfolio_value=PORTFOLIO_VALUE, as_of=alloc.as_of,
    )

    # --- Agent 13: compliance -------------------------------------------
    logger.info("Agent 13: compliance")
    orders_df = pd.DataFrame([
        {"date": alloc.as_of, "ticker": o.ticker, "side": o.side, "notional": o.notional}
        for o in plan.orders
    ])
    compliance = ComplianceSurveillance().review(
        orders_df, targets, sectors=SECTORS, as_of=alloc.as_of)

    # --- Agent 9 + 14 + 10: backtest, model risk, risk metrics ----------
    logger.info("Agent 9: walk-forward backtest (this is the slow step)")
    qlib.init(provider_uri="~/.qlib/qlib_data/us_data", region="us")
    from agents.backtest.__main__ import DOWNLOAD_START, TEST_END, TEST_START, download_universe
    bt_prices, bt_volumes = download_universe(DOWNLOAD_START, TEST_END)
    bt_report, daily_returns = WalkForwardBacktester().run(
        bt_prices, bt_volumes, test_start=TEST_START, test_end=TEST_END)

    logger.info("Agent 14: model risk")
    regime_by_date = {pd.Timestamp(r.date): r.regime for r in bt_report.rebalance_log}
    mr = ModelRiskValidator().validate(daily_returns, regime_by_date=regime_by_date)

    logger.info("Agent 10: risk metrics")
    equity = (1 + daily_returns).cumprod()

    # --- Agent 15: data health ------------------------------------------
    logger.info("Agent 15: data health")
    feeds = []
    client = FredClient()
    for alias, cadence in [("cpi", "monthly_economic"), ("core_cpi", "monthly_economic"),
                           ("yield_curve", "daily_economic"), ("vix", "daily_economic")]:
        try:
            s = client.fetch_series(alias, start_date="2015-01-01")
            feeds.append(check_staleness(alias, "FRED", s.index, cadence))
            feeds.append(check_gaps(alias, "FRED", s.index, cadence))
        except Exception as e:
            logger.warning("%s: %s", alias, e)
    feeds.append(check_staleness("yfinance_prices", "yfinance", prices.index, "daily_market"))
    health = DataHealthMonitor().summarize(feeds)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "portfolio_value": PORTFOLIO_VALUE,
        "roster": [
            {"n": n, "name": name, "status": st, "note": note} for n, name, st, note in ROSTER
        ],
        "macro": {
            "as_of": assessment.as_of,
            "regime": assessment.regime.value,
            "risk_regime": assessment.risk_regime.value,
            "growth_score": assessment.growth_score,
            "inflation_score": assessment.inflation_score,
            "reasoning": assessment.reasoning,
            "inputs": [
                {"alias": s.alias, "series_id": s.series_id, "latest": s.latest_value,
                 "date": s.latest_date, "yoy_pct": s.yoy_change_pct, "yoy_pp": s.yoy_change_pp}
                for s in assessment.inputs
            ],
        },
        "alpha": {
            "as_of": bundle.as_of,
            "factor_weights": bundle.factor_weights,
            "exposure_scale": bundle.exposure_scale,
            "signals": [
                {"ticker": s.ticker, "signal": s.signal, "confidence": s.confidence,
                 "factors": [{"name": f.name, "value": f.normalized_value} for f in s.factors]}
                for s in bundle.signals
            ],
        },
        "portfolio": {
            "as_of": alloc.as_of,
            "optimizer": alloc.optimizer_method,
            "covariance": alloc.covariance_estimator,
            "gross_exposure": alloc.gross_exposure,
            "cash_weight": alloc.cash_weight,
            "reasoning": alloc.reasoning,
            "positions": [
                {"ticker": p.ticker, "weight": p.weight, "signal": p.signal}
                for p in alloc.positions
            ],
        },
        "execution": {
            "algo": plan.algo,
            "n_orders": plan.n_orders,
            "gross_notional": plan.gross_notional,
            "turnover": plan.turnover,
            "cost_bps": plan.cost_bps,
            "spread_cost": plan.total_spread_cost,
            "impact_cost": plan.total_impact_cost,
            "orders": [
                {"ticker": o.ticker, "side": o.side, "notional": o.notional,
                 "shares": o.shares, "delta": o.delta_weight}
                for o in plan.orders
            ],
        },
        "operations": {
            "total_drift_abs": recon.total_drift_abs,
            "max_single_drift": recon.max_single_drift,
            "alpha_pnl": recon.alpha_pnl,
            "execution_cost": recon.execution_cost,
            "drift_pnl": recon.drift_pnl,
            "total_pnl": recon.total_pnl,
            "residual": recon.attribution_residual,
            "findings": recon.findings,
        },
        "compliance": {
            "orders_reviewed": compliance.orders_reviewed,
            "rules": compliance.rules_checked,
            "violations": compliance.violations,
            "warnings": compliance.warnings,
            "clean": compliance.clean,
            "alerts": [{"severity": a.severity, "rule": a.rule, "detail": a.detail}
                       for a in compliance.alerts],
            "audit_trail": compliance.audit_trail,
        },
        "backtest": {
            "start": bt_report.start,
            "end": bt_report.end,
            "n_rebalances": bt_report.n_rebalances,
            "total_return": bt_report.total_return,
            "benchmark_return": bt_report.benchmark_return,
            "sharpe": bt_report.annualized_sharpe,
            "max_drawdown": bt_report.max_drawdown,
            "dsr": bt_report.deflated_sharpe_ratio,
            "dsr_trials": bt_report.deflated_sharpe_n_trials,
            "equity_curve": [
                {"date": str(d.date()), "value": float(v)}
                for d, v in equity.resample("W").last().dropna().items()
            ],
        },
        "risk": {
            "historical_var": historical_var(daily_returns),
            "historical_cvar": historical_cvar(daily_returns),
            "parametric_var": parametric_var(daily_returns),
            "max_drawdown": max_drawdown(daily_returns),
            "kill_switch_armed": False,
            "limits_set": False,
        },
        "modelrisk": {
            "verdict": mr.verdict,
            "headline_sharpe": mr.headline_sharpe,
            "sharpe_dispersion": mr.sharpe_dispersion,
            "sub_periods": [
                {"label": s.label, "start": s.start, "end": s.end,
                 "return": s.total_return, "sharpe": s.annualized_sharpe,
                 "max_drawdown": s.max_drawdown}
                for s in mr.sub_periods
            ],
            "regime_performance": [
                {"regime": r.regime, "days": r.n_days, "return": r.total_return,
                 "sharpe": r.annualized_sharpe}
                for r in mr.regime_performance
            ],
            "findings": [{"severity": f.severity, "category": f.category, "text": f.finding}
                         for f in mr.findings],
        },
        "data_health": {
            "verdict": health.verdict,
            "checked": health.feeds_checked,
            "ok": health.ok,
            "degraded": health.degraded,
            "down": health.down,
            "feeds": [
                {"feed": f.feed, "source": f.source, "status": f.status,
                 "latest": f.latest_observation, "detail": f.detail}
                for f in health.feeds
            ],
        },
    }


def main():
    snapshot = build_snapshot()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, indent=2))
    print(f"\nWrote {OUT} ({OUT.stat().st_size:,} bytes)")
    print(f"  regime={snapshot['macro']['regime']}  positions={len(snapshot['portfolio']['positions'])}"
          f"  backtest={snapshot['backtest']['total_return']:+.2%}")


if __name__ == "__main__":
    main()
