from pydantic import BaseModel, Field


class Order(BaseModel):
    ticker: str
    side: str = Field(description="'buy' or 'sell'")
    target_weight: float
    current_weight: float
    delta_weight: float = Field(description="Signed change needed; the actual thing to execute.")
    notional: float = Field(description="Absolute dollar value of the order.")
    shares: float
    reference_price: float


class ExecutionSlice(BaseModel):
    """One child order in a scheduled parent order (TWAP/VWAP)."""

    ticker: str
    slice_index: int
    n_slices: int
    shares: float
    participation_rate: float = Field(
        description="This slice's shares / the interval's expected volume. Drives impact."
    )
    spread_cost: float
    impact_cost: float
    total_cost: float


class ExecutionPlan(BaseModel):
    as_of: str
    algo: str
    n_orders: int
    gross_notional: float = Field(description="Total absolute dollar value traded.")
    turnover: float = Field(description="Gross notional / portfolio value.")
    total_spread_cost: float
    total_impact_cost: float
    total_cost: float
    cost_bps: float = Field(description="Total cost in basis points of gross notional.")
    orders: list[Order]
    slices: list[ExecutionSlice]
    reasoning: list[str]
