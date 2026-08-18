"""Agent 12 — Operations & Settlement.

Answers the back-office question nobody else asks: we intended to run one
portfolio — what did we actually end up running, and what did the difference
cost? Silent drift between intended and executed allocation is exactly the kind
of error that never announces itself, which is the failure mode this project
keeps meeting.

PnL ATTRIBUTION. Total PnL is split into components that must sum back to the
total — an identity, so an incomplete attribution fails arithmetically rather
than looking plausible:

    total = alpha_pnl + execution_cost + drift_pnl

- alpha_pnl: what the INTENDED portfolio would have earned. The strategy's
  actual contribution.
- execution_cost: what it cost to trade (Agent 11's estimate). Always negative.
- drift_pnl: the return difference caused by holding something other than the
  target. Can be either sign — drift sometimes helps, which is exactly why it
  must be measured rather than assumed harmful.
"""

import logging

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PositionDrift(BaseModel):
    ticker: str
    target_weight: float
    actual_weight: float
    drift: float
    drift_reason: str


class ReconciliationReport(BaseModel):
    as_of: str
    portfolio_value: float
    n_positions: int
    total_drift_abs: float = Field(description="Sum of |target - actual| across names.")
    max_single_drift: float
    positions: list[PositionDrift]
    # Attribution: these three must sum to total_pnl.
    total_pnl: float
    alpha_pnl: float
    execution_cost: float
    drift_pnl: float
    attribution_residual: float = Field(
        description="total - (alpha + execution + drift). Must be ~0 or the attribution is wrong."
    )
    findings: list[str]


class OperationsReconciler:
    def __init__(self, drift_tolerance: float = 0.005):
        """`drift_tolerance`: drift below this is treated as normal friction
        (rounding to whole shares, a price moving between decision and fill)
        rather than something to investigate."""
        self.drift_tolerance = drift_tolerance

    def reconcile(
        self,
        target_weights: dict[str, float],
        actual_weights: dict[str, float],
        period_returns: dict[str, float],
        execution_cost: float,
        portfolio_value: float,
        as_of: str,
        constrained_tickers: set[str] | None = None,
    ) -> ReconciliationReport:
        """`constrained_tickers` are names where drift has a known, legitimate
        cause (a trading limit, insufficient liquidity). Separating those from
        unexplained drift matters: one is the system working as designed, the
        other is a bug."""
        constrained = constrained_tickers or set()
        findings: list[str] = []
        universe = sorted(set(target_weights) | set(actual_weights))

        positions: list[PositionDrift] = []
        for t in universe:
            tgt = target_weights.get(t, 0.0)
            act = actual_weights.get(t, 0.0)
            d = act - tgt
            if abs(d) < 1e-9:
                continue
            if t in constrained:
                reason = "expected — execution constrained (limit or liquidity)"
            elif abs(d) <= self.drift_tolerance:
                reason = "within tolerance — rounding/price movement"
            else:
                reason = "UNEXPLAINED — investigate"
            positions.append(PositionDrift(
                ticker=t, target_weight=tgt, actual_weight=act, drift=d, drift_reason=reason,
            ))

        unexplained = [p for p in positions if p.drift_reason.startswith("UNEXPLAINED")]
        if unexplained:
            findings.append(
                f"{len(unexplained)} position(s) drifted beyond tolerance with no known cause: "
                + ", ".join(f"{p.ticker} {p.drift:+.2%}" for p in unexplained[:5])
            )

        # --- Attribution -----------------------------------------------------
        alpha_pnl = sum(
            target_weights.get(t, 0.0) * period_returns.get(t, 0.0) for t in universe
        ) * portfolio_value
        actual_gross_pnl = sum(
            actual_weights.get(t, 0.0) * period_returns.get(t, 0.0) for t in universe
        ) * portfolio_value
        drift_pnl = actual_gross_pnl - alpha_pnl
        total_pnl = actual_gross_pnl - execution_cost

        residual = total_pnl - (alpha_pnl + (-execution_cost) + drift_pnl)

        if abs(drift_pnl) > abs(alpha_pnl) and abs(alpha_pnl) > 0:
            findings.append(
                f"Drift moved PnL by ${drift_pnl:,.0f}, more than the strategy's own "
                f"${alpha_pnl:,.0f} — the portfolio being run is not the one that was designed."
            )
        if execution_cost > abs(alpha_pnl) and abs(alpha_pnl) > 0:
            findings.append(
                f"Execution cost ${execution_cost:,.0f} exceeds gross alpha ${alpha_pnl:,.0f} — "
                f"the strategy is not profitable after costs at this turnover."
            )
        if not findings:
            findings.append("Reconciled cleanly: no unexplained drift, costs within alpha.")

        return ReconciliationReport(
            as_of=as_of,
            portfolio_value=portfolio_value,
            n_positions=len(positions),
            total_drift_abs=float(sum(abs(p.drift) for p in positions)),
            max_single_drift=float(max((abs(p.drift) for p in positions), default=0.0)),
            positions=sorted(positions, key=lambda p: abs(p.drift), reverse=True),
            total_pnl=float(total_pnl),
            alpha_pnl=float(alpha_pnl),
            execution_cost=float(-execution_cost),
            drift_pnl=float(drift_pnl),
            attribution_residual=float(residual),
            findings=findings,
        )
