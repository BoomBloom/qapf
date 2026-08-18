from pydantic import BaseModel, Field


class RiskLimits(BaseModel):
    """Hard risk limits enforced by the CRO. These encode risk appetite, not a
    technical fact — there is no data-derived "correct" value, only how much
    loss is tolerable before trading halts. Set deliberately, not defaulted."""

    max_drawdown_pct: float = Field(gt=0, le=1, description="Halt if drawdown from peak exceeds this.")
    max_daily_loss_pct: float = Field(gt=0, le=1, description="Halt if a single day's loss exceeds this.")
    var_confidence: float = Field(default=0.95, gt=0, lt=1)


class RiskAssessment(BaseModel):
    as_of: str
    portfolio_value: float
    daily_return: float
    current_drawdown: float
    worst_drawdown: float
    historical_var: float
    historical_cvar: float
    parametric_var: float
    var_confidence: float
    breaches: list[str]
    kill_switch_triggered: bool
    reasoning: list[str]
