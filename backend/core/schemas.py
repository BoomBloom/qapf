"""Shared state threaded through Agent 1's pipeline.

A Pydantic model, not a TypedDict -- LangGraph's StateGraph accepts either,
and this project's "Pydantic v2 everywhere" rule (CLAUDE.md) applies to graph
state exactly as it does to every other inter-agent contract. `arbitrary_types
_allowed` is required because prices/volumes/returns are pandas objects, not
JSON-serializable Pydantic types -- this state is passed in-process between
graph nodes, never serialized over a wire (that's what backend/api/ would be
for, not yet built).
"""

import pandas as pd
from pydantic import BaseModel, ConfigDict

from agents.alpha.schemas import SignalBundle
from agents.compliance.surveillance import ComplianceReport
from agents.execution.schemas import ExecutionPlan
from agents.macro.schemas import MacroRegimeAssessment
from agents.portfolio.schemas import PortfolioAllocation


class PipelineState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # --- Inputs, set once at invocation ---
    universe: list[str]
    prices: pd.DataFrame
    volumes: pd.DataFrame
    portfolio_value: float
    current_weights: dict[str, float] = {}
    restricted_list: set[str] = set()
    # Real portfolio daily-return history for the CRO to assess drawdown
    # against. None is a legitimate, expected value before any capital has
    # actually traded (paper or real) -- see state_graph.py's risk_gate node
    # for how that's handled honestly rather than faked.
    daily_returns: pd.Series | None = None

    # --- Filled by nodes, in pipeline order ---
    macro_assessment: MacroRegimeAssessment | None = None
    signal_bundle: SignalBundle | None = None
    allocation: PortfolioAllocation | None = None

    risk_breaches: list[str] = []
    kill_switch_triggered: bool = False
    risk_reasoning: list[str] = []
    halted: bool = False
    halt_reason: str | None = None

    compliance_report: ComplianceReport | None = None
    execution_plan: ExecutionPlan | None = None
    cio_memo: str | None = None
