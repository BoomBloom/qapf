"""Deterministic, isolated risk enforcement.

CRO ISOLATION RULE (CLAUDE.md, non-negotiable): this module and everything
under backend/risk/ must NEVER import from backend.core or any LangGraph
module. The CRO reads portfolio state and decides; it does not participate in
agent debate, and nothing outside this package can override its verdict.
"""

import pandas as pd

from . import metrics
from .schemas import RiskAssessment, RiskLimits


class RiskMonitor:
    def __init__(self, limits: RiskLimits):
        self.limits = limits

    def assess(self, returns: pd.Series, portfolio_value: float | None = None) -> RiskAssessment:
        """Assess risk using only the data in `returns` -- pass a point-in-time
        slice (not the full future history) when scanning historical dates,
        the same discipline Agents 6/7/9 already established."""
        returns = returns.dropna()
        if returns.empty:
            raise ValueError("No return observations to assess.")

        dd_series = metrics.drawdown_series(returns)
        current_dd = float(dd_series.iloc[-1])
        worst_dd = float(dd_series.min())
        latest_return = float(returns.iloc[-1])

        breaches: list[str] = []
        reasoning: list[str] = []

        if abs(current_dd) >= self.limits.max_drawdown_pct:
            breaches.append("max_drawdown")
            reasoning.append(
                f"Current drawdown {current_dd:.2%} breaches the "
                f"{self.limits.max_drawdown_pct:.2%} limit."
            )
        if latest_return < 0 and abs(latest_return) >= self.limits.max_daily_loss_pct:
            breaches.append("max_daily_loss")
            reasoning.append(
                f"Latest daily loss {latest_return:.2%} breaches the "
                f"{self.limits.max_daily_loss_pct:.2%} limit."
            )
        if not breaches:
            reasoning.append("No hard limits breached.")

        last_idx = returns.index[-1]
        return RiskAssessment(
            as_of=str(last_idx.date()) if hasattr(last_idx, "date") else str(last_idx),
            portfolio_value=portfolio_value if portfolio_value is not None else float("nan"),
            daily_return=latest_return,
            current_drawdown=current_dd,
            worst_drawdown=worst_dd,
            historical_var=metrics.historical_var(returns, self.limits.var_confidence),
            historical_cvar=metrics.historical_cvar(returns, self.limits.var_confidence),
            parametric_var=metrics.parametric_var(returns, self.limits.var_confidence),
            var_confidence=self.limits.var_confidence,
            breaches=breaches,
            kill_switch_triggered=len(breaches) > 0,
            reasoning=reasoning,
        )

    def assess_history(self, returns: pd.Series) -> list[RiskAssessment]:
        """Run assess() as-of every date in the series, each using only data up
        to that date -- lets a backtest be scanned for exactly when a breach
        WOULD have fired, not just checked once at the final date."""
        returns = returns.dropna()
        return [self.assess(returns.iloc[: i + 1]) for i in range(len(returns))]
