from pydantic import BaseModel, Field


class CashYieldAssessment(BaseModel):
    """What idle cash actually earns, given a real broker's tiered structure
    — not "cash earns nothing," which every other agent's account-value math
    silently assumes by omission."""

    nav: float
    cash_balance: float
    uncompensated_threshold: float = Field(description="Cash below this earns $0, per the broker's real tier.")
    compensated_balance: float
    tier_rate_apy: float = Field(description="Full published rate for NAV at/above the broker's top tier.")
    proration_factor: float = Field(ge=0.0, le=1.0, description="1.0 if NAV clears the top tier; NAV/tier_floor otherwise.")
    effective_apy: float
    annual_interest: float
    daily_interest: float
    reasoning: list[str]


class MarginRequirement(BaseModel):
    """REG-T margin requirements for a real position set — standard SEC/FINRA
    formula, not broker-specific. QAPF's Portfolio Manager (Agent 2) is
    long-only/cash-account by deliberate decision (see allocator.py's
    docstring) and does not currently use this, but a real-capital system
    that might ever use margin needs this infrastructure to exist before it
    does, not retrofitted after a margin call."""

    gross_position_value: float
    initial_margin_required: float = Field(description="Reg T initial margin: 50% of long equity value.")
    maintenance_margin_required: float = Field(description="FINRA minimum maintenance: 25% of long equity value.")
    excess_liquidity: float = Field(description="NAV minus maintenance requirement. Negative = margin call.")
    margin_call: bool
    reasoning: list[str]
