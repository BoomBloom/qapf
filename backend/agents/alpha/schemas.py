from pydantic import BaseModel, Field


class FactorValue(BaseModel):
    """One factor's raw and cross-sectionally normalized value for one instrument."""

    name: str
    raw_value: float
    normalized_value: float = Field(
        description="Cross-sectional rank mapped to [-1, +1] across the universe."
    )


class AlphaSignal(BaseModel):
    """The standardized output contract every downstream agent consumes.

    `signal` is deliberately bounded to [-1, +1] so the Portfolio Manager can
    size positions without needing to know which factors produced it.
    """

    ticker: str
    as_of: str
    signal: float = Field(ge=-1.0, le=1.0, description="Combined alpha in [-1, +1].")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Agreement across factors: 1.0 = all factors point the same way.",
    )
    factors: list[FactorValue]


class SignalBundle(BaseModel):
    """A full cross-section of signals plus the regime context that shaped them."""

    as_of: str
    universe_size: int
    macro_regime: str
    risk_regime: str
    # Records the regime-conditional weights actually applied, so a signal can
    # be audited after the fact rather than being an unexplained number.
    factor_weights: dict[str, float]
    exposure_scale: float = Field(
        ge=0.0,
        le=1.0,
        description="Gross exposure multiplier from the risk regime (risk-off scales down).",
    )
    signals: list[AlphaSignal]
