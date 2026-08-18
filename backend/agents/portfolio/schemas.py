from pydantic import BaseModel, Field


class PositionWeight(BaseModel):
    ticker: str
    weight: float = Field(description="Fraction of portfolio capital. Long-only: always >= 0.")
    signal: float = Field(description="The Agent 7 signal that informed this weight, kept for audit.")


class PortfolioAllocation(BaseModel):
    """Target portfolio produced from a cross-section of alpha signals.

    Records the regime and optimizer method that produced it, so an allocation
    can be explained after the fact rather than being an unexplained vector.
    """

    as_of: str
    macro_regime: str
    risk_regime: str
    optimizer_method: str
    covariance_estimator: str
    gross_exposure: float = Field(description="Sum of weights; < 1.0 means cash is held.")
    cash_weight: float
    n_positions: int
    positions: list[PositionWeight]
    reasoning: list[str]
