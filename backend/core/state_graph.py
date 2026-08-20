"""Agent 1 — Lead Orchestrator (CIO). QAPF's fork of TradingAgents'
`GraphSetup`/`TradingAgentsGraph` (Apache-2.0) — the LangGraph `StateGraph`
wiring, checkpointing pattern, and provider-agnostic LLM client factory are
adapted directly, per README.md's roster call ("Adapt... directly reusable").

WHAT THIS GRAPH IS NOT, on purpose: the original TradingAgentsGraph wires 8+
LLM-persona nodes (market/social/news/fundamentals analysts, bull/bear
researchers, a research manager, aggressive/neutral/conservative risk
debators) that reach a trade decision through prose debate. QAPF already
replaced every one of those roles with a deterministic, verified agent of its
own — Agent 6 for macro, Agent 7 for signal generation, Agent 2 for
allocation, Agent 10 for risk. Rebuilding an LLM debate on top of that would
duplicate machinery this project already trusts more than free-form LLM
opinion, and would reintroduce exactly the kind of unverifiable judgment the
CRO's isolation rule exists to keep out of the risk path. So this graph has
exactly ONE LLM node — `cio_synthesis`, a single deep-thinking call at the end
that turns the deterministic pipeline's output into a human-readable decision
memo. Every other node is a thin LangGraph wrapper around an already-built,
already-verified QAPF agent; none of them reason freely.

PIPELINE SHAPE — deliberately narrower than "all 12 agents":
    macro -> alpha -> portfolio -> risk_gate -> [execution -> compliance] -> cio_synthesis -> END
Agents 3 (Research), 4 (Stats, used ad hoc inside Alpha/Backtest rather than
as a pipeline step), 9 (Backtest), 14 (Model Risk), and 15 (Data Infra) are
NOT nodes here, on purpose: they are periodic/independent functions that feed
or challenge this pipeline (research scans literature on its own cadence,
backtest validates historical windows, model risk and data infra watch
continuously), not steps in generating today's live allocation. Folding them
in as synchronous nodes would be a category error, not a completeness gap.
Agent 12 (Operations) is also absent for a concrete reason, not an oversight:
its `reconcile()` compares target positions to REAL fills, and this system has
no live broker connection yet (wayfinder ticket 09 chose Interactive Brokers,
2026-08-20, but the account/API-credential setup itself is still pending) —
including Agent 12 here would mean fabricating fill data, which CLAUDE.md's
"no placeholder data" rule forbids.

SLACK ALERTING (2026-08-20, "monitor by exception"): `cio_synthesis` posts
every memo it generates to a Slack webhook (`notifier.py`, fails soft --
a Slack outage never blocks the pipeline). This only fires on a real,
manually-triggered `python -m core` run; the daily launchd dashboard refresh
(`scripts/refresh_dashboard.sh`) does not call Agent 1 at all, so this can't
turn into automatic daily Slack spam by itself.

KILL-SWITCH ENFORCEMENT (wayfinder ticket 12): `risk_gate` is the choke point.
When the CRO's kill switch trips, the conditional edge below routes straight
to `cio_synthesis` — skipping `execution` and `compliance` entirely, so no
order is ever emitted for a halted state (fails closed). This is the
enforcement ticket 12 asked for, implemented here rather than inside
`ExecutionPlanner` itself, because gating at the graph level keeps the
execution/compliance agents simple and independently testable (e.g. for
Agent 9's backtests, which must keep running through drawdowns to measure
them) while still making a live, orchestrated run fail closed.

CRO isolation is preserved: `risk_gate` imports `risk.monitor`/`risk.schemas`
as plain Python calls from within a graph node. The isolation rule (CLAUDE.md)
is one-directional — `backend/risk/` must never import `backend.core` or
LangGraph; nothing forbids `backend/core` from calling into `backend/risk`.
The CRO still "reads state; it does not join the debate" — it has no idea
LangGraph exists.
"""

import logging

import pandas as pd
from langgraph.graph import END, START, StateGraph

from agents.alpha.combiner import AlphaCombiner
from agents.compliance.surveillance import ComplianceSurveillance
from agents.execution.planner import ExecutionPlanner
from agents.macro.regime import MacroRegimeClassifier
from agents.portfolio.allocator import PortfolioAllocator
from risk.monitor import RiskMonitor
from risk.schemas import RiskLimits

from .config import get_deep_llm
from .notifier import send_slack_alert
from .schemas import PipelineState

logger = logging.getLogger(__name__)

# Set live via wayfinder ticket 01 (2026-08-19) -- see backend/risk/__main__.py
# for the same values and the reasoning behind them. Duplicated here (not
# imported from risk/__main__.py, which is a manual verification script, not
# a config module) so the orchestrator's real risk gate doesn't depend on a
# test runner's module-level state.
LIVE_RISK_LIMITS = RiskLimits(max_drawdown_pct=0.20, max_daily_loss_pct=0.06)


def macro_node(state: PipelineState) -> dict:
    assessment = MacroRegimeClassifier().assess()
    logger.info("macro_node: regime=%s risk=%s", assessment.regime.value, assessment.risk_regime.value)
    return {"macro_assessment": assessment}


def alpha_node(state: PipelineState) -> dict:
    combiner = AlphaCombiner()
    bundle = combiner.generate(
        state.prices, state.volumes,
        state.macro_assessment.regime, state.macro_assessment.risk_regime,
    )
    logger.info("alpha_node: %d signals generated", len(bundle.signals))
    return {"signal_bundle": bundle}


def portfolio_node(state: PipelineState) -> dict:
    allocator = PortfolioAllocator()
    allocation = allocator.allocate(
        state.signal_bundle, state.prices,
        state.macro_assessment.regime, state.macro_assessment.risk_regime,
    )
    logger.info(
        "portfolio_node: %d positions, %.1f%% gross exposure",
        allocation.n_positions, allocation.gross_exposure * 100,
    )
    return {"allocation": allocation}


def risk_gate_node(state: PipelineState) -> dict:
    """The kill-switch choke point (ticket 12). See module docstring."""
    if state.daily_returns is None or state.daily_returns.dropna().empty:
        reasoning = [
            "No real portfolio return history available yet (no paper or live "
            "trading has started) -- the CRO cannot evaluate drawdown against "
            "a track record that doesn't exist. Running risk-blind: NOT halted, "
            "but this is a real gap, not a pass. See wayfinder ticket 01/12."
        ]
        logger.warning("risk_gate_node: no daily_returns supplied, running risk-blind")
        return {"risk_breaches": [], "kill_switch_triggered": False, "risk_reasoning": reasoning, "halted": False}

    assessment = RiskMonitor(LIVE_RISK_LIMITS).assess(state.daily_returns, portfolio_value=state.portfolio_value)
    halted = assessment.kill_switch_triggered
    halt_reason = None
    if halted:
        halt_reason = (
            "Kill switch triggered: " + "; ".join(assessment.reasoning) +
            " Per wayfinder ticket 01, trading stays halted until the strategy "
            "is re-run through ticket 02's validation bar on fresh data -- not "
            "resumable by operator override alone."
        )
        logger.warning("risk_gate_node: HALTED -- %s", halt_reason)
    else:
        logger.info("risk_gate_node: no breach, %d/%d checked", 0, 1)
    return {
        "risk_breaches": assessment.breaches,
        "kill_switch_triggered": halted,
        "risk_reasoning": assessment.reasoning,
        "halted": halted,
        "halt_reason": halt_reason,
    }


def execution_node(state: PipelineState) -> dict:
    planner = ExecutionPlanner()
    plan = planner.plan(
        state.allocation, state.prices, state.volumes,
        state.portfolio_value, state.current_weights,
    )
    logger.info("execution_node: %d orders, %.1fbp total cost", plan.n_orders, plan.cost_bps)
    return {"execution_plan": plan}


def compliance_node(state: PipelineState) -> dict:
    plan = state.execution_plan
    order_history = pd.DataFrame([
        {"date": plan.as_of, "ticker": o.ticker, "side": o.side, "notional": o.notional}
        for o in plan.orders
    ])
    target_weights = {p.ticker: p.weight for p in state.allocation.positions}
    surveillance = ComplianceSurveillance(restricted_list=state.restricted_list)
    report = surveillance.review(order_history, target_weights, as_of=plan.as_of)
    logger.info(
        "compliance_node: %d violation(s), %d warning(s), clean=%s",
        report.violations, report.warnings, report.clean,
    )
    return {"compliance_report": report}


def cio_synthesis_node(state: PipelineState) -> dict:
    """The one LLM call in this graph. Synthesizes the deterministic
    pipeline's output into a decision memo -- never overrides it. The CRO's
    verdict and the compliance report are stated as facts in the prompt, not
    questions for the model to second-guess; this node explains and
    contextualizes a decision already made by deterministic code, exactly the
    boundary the CRO isolation rule exists to protect."""
    lines = [
        f"Macro regime: {state.macro_assessment.regime.value} "
        f"(risk regime: {state.macro_assessment.risk_regime.value})",
        f"Regime reasoning: {'; '.join(state.macro_assessment.reasoning)}",
    ]
    if state.allocation:
        top = sorted(state.allocation.positions, key=lambda p: -p.weight)[:5]
        lines.append(
            f"Target allocation: {state.allocation.n_positions} positions, "
            f"{state.allocation.gross_exposure:.0%} gross, "
            f"{state.allocation.cash_weight:.0%} cash. Top names: " +
            ", ".join(f"{p.ticker}={p.weight:.1%}" for p in top)
        )
    if state.halted:
        lines.append(f"RISK GATE: HALTED. {state.halt_reason}")
    else:
        lines.append(f"Risk gate: no breach. {'; '.join(state.risk_reasoning)}")
    if state.execution_plan:
        lines.append(
            f"Execution: {state.execution_plan.n_orders} orders, "
            f"{state.execution_plan.turnover:.1%} turnover, "
            f"{state.execution_plan.cost_bps:.1f}bp total cost."
        )
    if state.compliance_report:
        lines.append(
            f"Compliance: {state.compliance_report.violations} violation(s), "
            f"{state.compliance_report.warnings} warning(s). "
            f"clean={state.compliance_report.clean}"
        )
    facts = "\n".join(f"- {line}" for line in lines)

    llm = get_deep_llm()
    prompt = (
        "You are the CIO of a systematic quant fund reviewing today's pipeline "
        "output before it's logged. The numbers below are already final and "
        "deterministic -- your job is a concise (under 200 words) decision memo "
        "explaining what happened and why, in plain English for the operator. "
        "Do not invent numbers not given below. If trading was halted, say so "
        "plainly and state that resuming requires re-validation, not just a "
        "manual override.\n\n" + facts
    )
    response = llm.invoke(prompt)
    memo = response.content if hasattr(response, "content") else str(response)
    logger.info("cio_synthesis_node: memo generated (%d chars)", len(memo))

    # "Monitor by exception" (2026-08-20 wayfinder discussion): the operator
    # gets paged on every real Agent 1 run, not left to check a terminal.
    # This only fires when someone actually runs `python -m core` -- the
    # daily launchd dashboard refresh does NOT call Agent 1 (real Anthropic
    # cost per call), so this can't turn into daily Slack spam by itself.
    header = "🚨 QAPF HALTED" if state.halted else "QAPF — CIO memo"
    send_slack_alert(f"*{header}*\n{memo}")

    return {"cio_memo": memo}


def route_after_risk_gate(state: PipelineState) -> str:
    return "cio_synthesis" if state.halted else "execution"


def build_graph() -> StateGraph:
    workflow = StateGraph(PipelineState)

    workflow.add_node("macro", macro_node)
    workflow.add_node("alpha", alpha_node)
    workflow.add_node("portfolio", portfolio_node)
    workflow.add_node("risk_gate", risk_gate_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("compliance", compliance_node)
    workflow.add_node("cio_synthesis", cio_synthesis_node)

    workflow.add_edge(START, "macro")
    workflow.add_edge("macro", "alpha")
    workflow.add_edge("alpha", "portfolio")
    workflow.add_edge("portfolio", "risk_gate")
    workflow.add_conditional_edges(
        "risk_gate", route_after_risk_gate,
        {"execution": "execution", "cio_synthesis": "cio_synthesis"},
    )
    workflow.add_edge("execution", "compliance")
    workflow.add_edge("compliance", "cio_synthesis")
    workflow.add_edge("cio_synthesis", END)

    return workflow


class QAPFOrchestrator:
    """Compiles and runs the pipeline. A thin class, not because LangGraph
    needs one, but to match TradingAgentsGraph's own shape (compile once,
    `.run()` many times) since that's the pattern this module forks."""

    def __init__(self):
        self.workflow = build_graph()
        self.graph = self.workflow.compile()

    def run(
        self,
        universe: list[str],
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        portfolio_value: float,
        current_weights: dict[str, float] | None = None,
        daily_returns: pd.Series | None = None,
        restricted_list: set[str] | None = None,
    ) -> PipelineState:
        init_state = PipelineState(
            universe=universe, prices=prices, volumes=volumes,
            portfolio_value=portfolio_value,
            current_weights=current_weights or {},
            daily_returns=daily_returns,
            restricted_list=restricted_list or set(),
        )
        result = self.graph.invoke(init_state)
        return PipelineState.model_validate(result)
