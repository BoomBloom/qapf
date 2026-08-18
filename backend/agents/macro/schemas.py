from enum import StrEnum

from pydantic import BaseModel


class GrowthDirection(StrEnum):
    EXPANDING = "expanding"
    CONTRACTING = "contracting"


class InflationDirection(StrEnum):
    RISING = "rising"
    FALLING = "falling"


class MacroRegime(StrEnum):
    """The classic growth x inflation quadrant framework."""

    # growth up, inflation up
    INFLATIONARY_EXPANSION = "inflationary_expansion"
    # growth down, inflation up
    STAGFLATION = "stagflation"
    # growth up, inflation down -- the "goldilocks" quadrant
    DISINFLATIONARY_GROWTH = "disinflationary_growth"
    # growth down, inflation down
    DEFLATIONARY_CONTRACTION = "deflationary_contraction"


class RiskRegime(StrEnum):
    RISK_ON = "risk_on"
    NEUTRAL = "neutral"
    RISK_OFF = "risk_off"


class MacroSeriesSnapshot(BaseModel):
    """One FRED series reduced to the few numbers a regime call needs."""

    alias: str
    series_id: str
    latest_value: float
    latest_date: str
    # Relative (percent) YoY change — the meaningful figure for LEVEL series
    # (CPI index, industrial production, payroll counts).
    yoy_change_pct: float | None = None
    # Absolute (percentage-point) YoY change — the meaningful figure for RATE
    # series (unemployment rate, VIX, the 10y-2y spread), where a relative
    # percent change is easy to misread: unemployment moving 4.3% -> 4.1% is
    # -0.20pp, but "-4.65%" as a relative change.
    yoy_change_pp: float | None = None
    change_3m: float | None = None
    n_observations: int


class MacroRegimeAssessment(BaseModel):
    as_of: str
    regime: MacroRegime
    growth_direction: GrowthDirection
    inflation_direction: InflationDirection
    risk_regime: RiskRegime
    # Signed strength in [-1, 1] so downstream agents can weight the call
    # rather than treating every regime label as equally confident.
    growth_score: float
    inflation_score: float
    yield_curve_spread: float | None = None
    yield_curve_inverted: bool | None = None
    vix_level: float | None = None
    reasoning: list[str]
    inputs: list[MacroSeriesSnapshot]


class FundamentalSnapshot(BaseModel):
    ticker: str
    company_name: str | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    trailing_pe: float | None = None
    forward_pe: float | None = None
    price_to_book: float | None = None
    profit_margin: float | None = None
    return_on_equity: float | None = None
    revenue_growth: float | None = None
    earnings_growth: float | None = None
    debt_to_equity: float | None = None
    free_cashflow: float | None = None
    dividend_yield: float | None = None
    beta: float | None = None
