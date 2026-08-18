from pydantic import BaseModel, Field


class SubPeriodPerformance(BaseModel):
    label: str
    start: str
    end: str
    n_days: int
    total_return: float
    annualized_sharpe: float
    max_drawdown: float


class RegimePerformance(BaseModel):
    regime: str
    n_days: int
    total_return: float
    annualized_sharpe: float


class ModelRiskFinding(BaseModel):
    severity: str = Field(description="'critical' | 'warning' | 'info'")
    category: str
    finding: str


class ModelRiskReport(BaseModel):
    """An independent challenge to a backtest result.

    Agent 9 asks "did this perform well?"; this asks "could this be
    systematically wrong in ways the backtest can't reveal?"
    """

    as_of: str
    n_observations: int
    headline_sharpe: float
    # Decay: is the edge stable, or concentrated in one lucky stretch?
    sub_periods: list[SubPeriodPerformance]
    sharpe_dispersion: float = Field(
        description="Std dev of sub-period Sharpes. High = the headline number hides instability."
    )
    # Regime conditioning: was this validated in regimes it will actually meet?
    regime_performance: list[RegimePerformance]
    regimes_never_tested: list[str]
    # Concentration: does a handful of days carry the whole result?
    top_5_days_pct_of_return: float = Field(
        description="Top 5 days as a share of TOTAL ABSOLUTE movement (not net return, whose "
                    "near-zero denominator makes the ratio unstable)."
    )
    return_without_top_5_days: float
    findings: list[ModelRiskFinding]
    verdict: str
