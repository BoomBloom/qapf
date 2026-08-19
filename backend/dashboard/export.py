"""Generate the dashboard's data snapshot by running the real pipeline.

Writes frontend/data/snapshot.json. Every number in the UI comes from here, so
the dashboard shows what the agents actually computed — no mock values, per
CLAUDE.md's no-placeholder-data rule.

Run: cd backend && python -m dashboard.export
Needs the __main__ guard because it reaches Agent 9, which touches qlib.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parents[2]
TICKETS_DIR = REPO_ROOT / ".scratch" / "wayfinder-real-capital" / "tickets"
MAP_PATH = REPO_ROOT / ".scratch" / "wayfinder-real-capital" / "MAP.md"

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
    (1, "Lead Orchestrator", "live", "LangGraph pipeline; one Anthropic call per run for the CIO memo"),
    (2, "Portfolio Manager", "live", "Qlib optimizer + shrinkage covariance"),
    (3, "Academic Research", "live", "arXiv + GitHub ingestion"),
    (4, "Probability & Statistics", "live", "ADF/KPSS, cointegration, Deflated Sharpe, CUSUM filter"),
    (5, "Quantum & Optimization", "live", "QAOA subset selection, benchmarked vs. classical every run"),
    (6, "Fundamental & Macro", "live", "Keyless FRED regime classification"),
    (7, "Alpha Mining", "live", "Regime-conditional factor signals"),
    (8, "Quant Software Engineering", "live", "Code-gen, self-verified against a real test before acceptance"),
    (9, "Backtesting & Validation", "live", "Walk-forward on Qlib's engine"),
    (10, "Chief Risk Officer", "live", "VaR/CVaR + kill switch, isolation enforced"),
    (11, "Execution & Microstructure", "live", "TWAP/VWAP + square-root impact"),
    (12, "Operations & Settlement", "live", "Reconciliation + PnL attribution"),
    (13, "Compliance & Surveillance", "live", "Conduct rules + audit trail"),
    (14, "Model Risk & Validation", "live", "Independently challenges Agent 9"),
    (15, "Data Infrastructure", "live", "Feed staleness, gaps, schema drift"),
    (16, "Treasury & Funding", "live", "Cash yield + Reg T margin; no FX exposure to hedge yet"),
]

_TICKET_TITLE_RE = re.compile(r"^#\s*(\d+)\s*—\s*(.+)$", re.MULTILINE)
_TICKET_STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(.+)$", re.MULTILINE)
_TICKET_TYPE_RE = re.compile(r"^\*\*Type:\*\*\s*`?([^`\n]+)`?", re.MULTILINE)


def read_wayfinder_status() -> dict:
    """Parses the real ticket files rather than hand-summarizing them here —
    this section goes stale the moment a ticket closes if it's re-typed by
    hand, so it's derived straight from the same files the wayfinder process
    itself updates."""
    destination = ""
    if MAP_PATH.exists():
        map_text = MAP_PATH.read_text()
        m = re.search(r"## Destination\s*\n+(.+?)\n\n", map_text, re.DOTALL)
        if m:
            destination = m.group(1).strip()

    tickets = []
    if TICKETS_DIR.exists():
        for f in sorted(TICKETS_DIR.glob("*.md")):
            text = f.read_text()
            title_m = _TICKET_TITLE_RE.search(text)
            status_m = _TICKET_STATUS_RE.search(text)
            type_m = _TICKET_TYPE_RE.search(text)
            if not title_m:
                continue
            status_raw = status_m.group(1).strip() if status_m else "unknown"
            closed = status_raw.upper().startswith("CLOSED") or "DONE" in status_raw.upper()
            tickets.append({
                "n": int(title_m.group(1)),
                "title": title_m.group(2).strip(),
                "type": type_m.group(1).strip() if type_m else "",
                "status": status_raw,
                "closed": closed,
            })
    tickets.sort(key=lambda t: t["n"])
    return {
        "destination": destination,
        "tickets": tickets,
        "closed_count": sum(1 for t in tickets if t["closed"]),
        "total_count": len(tickets),
    }


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
    from agents.quantum.optimizer import QuantumPortfolioOptimizer
    from agents.treasury.manager import TreasuryManager
    from risk.metrics import historical_cvar, historical_var, max_drawdown, parametric_var
    from risk.monitor import RiskMonitor
    from risk.schemas import RiskLimits

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

    # --- Agent 5: quantum subset selection (kept small -- see optimizer.py's
    # module docstring on why QAOA doesn't scale past a modest qubit count) ---
    logger.info("Agent 5: quantum subset selection")
    covariance = PortfolioAllocator().estimate_covariance(prices, UNIVERSE)
    signal_map = {s.ticker: s.signal for s in bundle.signals}
    quantum_result = QuantumPortfolioOptimizer(max_candidates=6, reps=1, maxiter=50).select_subset(
        signal_map, covariance, k=3, risk_aversion=0.5,
    )

    # --- Agent 16: treasury (cash yield + margin infra, both at the real
    # $1,000 stage-3 size and at this dashboard's $1M illustrative size) ---
    logger.info("Agent 16: treasury")
    treasury = TreasuryManager()
    cash_yield_1k = treasury.assess_cash_yield(nav=1_000, cash_balance=alloc.cash_weight * 1_000)
    cash_yield_full = treasury.assess_cash_yield(
        nav=PORTFOLIO_VALUE, cash_balance=alloc.cash_weight * PORTFOLIO_VALUE)
    margin = treasury.assess_margin_requirement(
        gross_position_value=alloc.gross_exposure * PORTFOLIO_VALUE, nav=PORTFOLIO_VALUE)

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
    # Real limits from wayfinder ticket 01 (2026-08-19) -- same values as
    # backend/risk/__main__.py and backend/core/state_graph.py's LIVE_RISK_LIMITS.
    risk_assessment = RiskMonitor(RiskLimits(max_drawdown_pct=0.20, max_daily_loss_pct=0.06)).assess(daily_returns)

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
        "wayfinder": read_wayfinder_status(),
        "orchestrator": {
            "description": "LangGraph pipeline (macro -> alpha -> portfolio -> risk_gate -> "
                            "[execution -> compliance] -> cio_synthesis). Not run automatically on "
                            "every dashboard export -- its final node makes one real, paid Anthropic "
                            "call per invocation, and the cost-discipline decision behind this project "
                            "means that shouldn't happen just to refresh a snapshot.",
            "run_command": "cd backend && python -m core",
        },
        "codegen": {
            "description": "Generates and self-verifies Python from a spec (Groq-tier, escalates to "
                            "Anthropic only after 2 failed attempts). Demonstrated capability: the "
                            "symmetric CUSUM filter, generated and verified on the first attempt, now "
                            "live in agents.stats.toolkit.cusum_filter().",
            "run_command": "cd backend && python -m agents.codegen",
        },
        "quantum": {
            "universe": quantum_result.universe,
            "k": quantum_result.k,
            "brute_force_selected": quantum_result.brute_force.selected,
            "qaoa_selected": quantum_result.qaoa.selected,
            "qaoa_matches_optimum": quantum_result.qaoa_matches_brute_force,
            "qaoa_seconds": quantum_result.qaoa.wall_clock_seconds,
            "brute_force_seconds": quantum_result.brute_force.wall_clock_seconds,
            "reasoning": quantum_result.reasoning,
        },
        "treasury": {
            "cash_yield_at_1k": {
                "nav": cash_yield_1k.nav, "annual_interest": cash_yield_1k.annual_interest,
                "effective_apy": cash_yield_1k.effective_apy, "reasoning": cash_yield_1k.reasoning,
            },
            "cash_yield_at_portfolio_value": {
                "nav": cash_yield_full.nav, "annual_interest": cash_yield_full.annual_interest,
                "effective_apy": cash_yield_full.effective_apy,
            },
            "margin": {
                "gross_position_value": margin.gross_position_value,
                "initial_margin_required": margin.initial_margin_required,
                "maintenance_margin_required": margin.maintenance_margin_required,
                "margin_call": margin.margin_call,
                "reasoning": margin.reasoning,
            },
        },
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
            "kill_switch_armed": True,
            "limits_set": True,
            "max_drawdown_pct": 0.20,
            "max_daily_loss_pct": 0.06,
            "current_assessment": risk_assessment.kill_switch_triggered,
            "breaches": risk_assessment.breaches,
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
    print(f"  wayfinder: {snapshot['wayfinder']['closed_count']}/{snapshot['wayfinder']['total_count']} tickets closed"
          f"  quantum_matches_optimum={snapshot['quantum']['qaoa_matches_optimum']}"
          f"  cash_yield_at_1k=${snapshot['treasury']['cash_yield_at_1k']['annual_interest']:.2f}/yr")


if __name__ == "__main__":
    main()
