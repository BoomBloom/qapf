"""Deterministic macro regime classification.

No LLM involved: this is rule-based so the same inputs always produce the same
regime call, and every call carries its reasoning. Downstream agents (Portfolio
Manager, Alpha Mining) need a stable, auditable regime flag — an LLM's
non-determinism would be a liability here, not a feature.
"""

import logging
from datetime import date

import numpy as np
import pandas as pd

from .fred_client import FredClient
from .schemas import (
    GrowthDirection,
    InflationDirection,
    MacroRegime,
    MacroRegimeAssessment,
    MacroSeriesSnapshot,
    RiskRegime,
)

logger = logging.getLogger(__name__)

# Scaling constants for turning raw macro changes into [-1, 1] scores.
# Each is roughly "the change that should read as a full-strength signal".
INDPRO_YOY_FULL_SCALE = 4.0  # +/-4% YoY industrial production is a strong move
PAYEMS_YOY_FULL_SCALE = 2.5  # +/-2.5% YoY payroll growth is a strong move
UNRATE_12M_FULL_SCALE = 1.0  # +/-1.0pp change in unemployment rate is a strong move
CPI_ACCEL_FULL_SCALE = 2.0  # +/-2pp change in the YoY inflation *rate*

VIX_RISK_ON_BELOW = 15.0
VIX_RISK_OFF_ABOVE = 25.0

# How far back to look when asking "is the inflation rate accelerating?"
INFLATION_ACCEL_LOOKBACK_MONTHS = 6


def _yoy_pct(series: pd.Series) -> float | None:
    """Year-over-year percent change using the observation ~12 months back."""
    if series.empty:
        return None
    latest_date = series.index[-1]
    target = latest_date - pd.DateOffset(months=12)
    prior = series[series.index <= target]
    if prior.empty or prior.iloc[-1] == 0:
        return None
    return float((series.iloc[-1] / prior.iloc[-1] - 1.0) * 100.0)


def _change_over_months(series: pd.Series, months: int) -> float | None:
    """Absolute change in the series level over roughly `months` months."""
    if series.empty:
        return None
    target = series.index[-1] - pd.DateOffset(months=months)
    prior = series[series.index <= target]
    if prior.empty:
        return None
    return float(series.iloc[-1] - prior.iloc[-1])


def _yoy_series(series: pd.Series) -> pd.Series:
    """Rolling YoY percent-change series, used to measure inflation acceleration.

    Uses DATE offsets, not row offsets. A positional ``shift(12)`` silently
    becomes a 13-month change whenever a monthly series has a gap — and real
    FRED series do: CPIAUCSL is missing 2025-10-01, which made ``shift(12)``
    report headline CPI YoY as 3.54% when the true 12-month figure was 3.30%.
    """
    prior_dates = series.index - pd.DateOffset(months=12)
    # asof() takes the last observation at or before each date, matching
    # _yoy_pct's semantics and tolerating gaps.
    prior_values = series.asof(prior_dates)
    prior_values.index = series.index
    yoy = (series / prior_values.replace(0, np.nan) - 1.0) * 100.0
    return yoy.dropna()


def _clamp(value: float) -> float:
    return float(np.clip(value, -1.0, 1.0))


def _snapshot(alias: str, series: pd.Series) -> MacroSeriesSnapshot:
    return MacroSeriesSnapshot(
        alias=alias,
        series_id=str(series.name),
        latest_value=float(series.iloc[-1]),
        latest_date=str(series.index[-1].date()),
        yoy_change_pct=_yoy_pct(series),
        yoy_change_pp=_change_over_months(series, 12),
        change_3m=_change_over_months(series, 3),
        n_observations=len(series),
    )


class MacroRegimeClassifier:
    """Ingests macro series from FRED and classifies the growth x inflation regime."""

    def __init__(self, client: FredClient | None = None):
        self.client = client or FredClient()

    def assess(self, start_date: str = "2015-01-01") -> MacroRegimeAssessment:
        aliases = [
            "industrial_production",
            "nonfarm_payrolls",
            "unemployment_rate",
            "cpi",
            "core_cpi",
            "yield_curve",
            "vix",
        ]
        series_map: dict[str, pd.Series] = {}
        for alias in aliases:
            try:
                series_map[alias] = self.client.fetch_series(alias, start_date=start_date)
            except Exception as e:
                # A single unavailable series shouldn't void the whole assessment;
                # the scores below average over whatever inputs did arrive, and
                # the reasoning records what was missing.
                logger.warning("Could not fetch %s: %s", alias, e)

        if not series_map:
            raise RuntimeError("No macro series could be fetched; cannot assess regime.")

        reasoning: list[str] = []

        # --- Growth ---
        growth_components: list[float] = []
        if (s := series_map.get("industrial_production")) is not None:
            if (yoy := _yoy_pct(s)) is not None:
                growth_components.append(_clamp(yoy / INDPRO_YOY_FULL_SCALE))
                reasoning.append(f"Industrial production YoY: {yoy:+.2f}%")
        if (s := series_map.get("nonfarm_payrolls")) is not None:
            if (yoy := _yoy_pct(s)) is not None:
                growth_components.append(_clamp(yoy / PAYEMS_YOY_FULL_SCALE))
                reasoning.append(f"Nonfarm payrolls YoY: {yoy:+.2f}%")
        if (s := series_map.get("unemployment_rate")) is not None:
            if (chg := _change_over_months(s, 12)) is not None:
                # Rising unemployment is contractionary, hence the sign flip.
                growth_components.append(_clamp(-chg / UNRATE_12M_FULL_SCALE))
                reasoning.append(
                    f"Unemployment rate 12m change: {chg:+.2f}pp "
                    f"(latest {s.iloc[-1]:.1f}%) — rising is contractionary"
                )

        if not growth_components:
            raise RuntimeError("No growth indicators available; cannot assess regime.")
        growth_score = float(np.mean(growth_components))

        # --- Inflation ---
        # Direction is about the *rate* accelerating or decelerating, not whether
        # inflation is positive (CPI YoY is almost always positive).
        inflation_components: list[float] = []
        for alias, label in (("cpi", "Headline CPI"), ("core_cpi", "Core CPI")):
            s = series_map.get(alias)
            if s is None:
                continue
            yoy_series = _yoy_series(s)
            if yoy_series.empty:
                continue
            current_yoy = float(yoy_series.iloc[-1])
            target = yoy_series.index[-1] - pd.DateOffset(months=INFLATION_ACCEL_LOOKBACK_MONTHS)
            prior_window = yoy_series[yoy_series.index <= target]
            if prior_window.empty:
                continue
            accel = current_yoy - float(prior_window.iloc[-1])
            inflation_components.append(_clamp(accel / CPI_ACCEL_FULL_SCALE))
            reasoning.append(
                f"{label} YoY: {current_yoy:.2f}% now vs {prior_window.iloc[-1]:.2f}% "
                f"{INFLATION_ACCEL_LOOKBACK_MONTHS}m ago ({accel:+.2f}pp acceleration)"
            )

        if not inflation_components:
            raise RuntimeError("No inflation indicators available; cannot assess regime.")
        inflation_score = float(np.mean(inflation_components))

        # --- Quadrant ---
        growth_direction = (
            GrowthDirection.EXPANDING if growth_score >= 0 else GrowthDirection.CONTRACTING
        )
        inflation_direction = (
            InflationDirection.RISING if inflation_score >= 0 else InflationDirection.FALLING
        )
        regime = {
            (GrowthDirection.EXPANDING, InflationDirection.RISING): MacroRegime.INFLATIONARY_EXPANSION,
            (GrowthDirection.CONTRACTING, InflationDirection.RISING): MacroRegime.STAGFLATION,
            (GrowthDirection.EXPANDING, InflationDirection.FALLING): MacroRegime.DISINFLATIONARY_GROWTH,
            (GrowthDirection.CONTRACTING, InflationDirection.FALLING): MacroRegime.DEFLATIONARY_CONTRACTION,
        }[(growth_direction, inflation_direction)]

        # --- Risk regime (yield curve + volatility) ---
        curve_spread = None
        curve_inverted = None
        if (s := series_map.get("yield_curve")) is not None:
            curve_spread = float(s.iloc[-1])
            curve_inverted = curve_spread < 0
            reasoning.append(
                f"10y-2y spread: {curve_spread:+.2f}pp "
                f"({'INVERTED' if curve_inverted else 'normal'})"
            )

        vix_level = None
        if (s := series_map.get("vix")) is not None:
            vix_level = float(s.iloc[-1])
            reasoning.append(f"VIX: {vix_level:.2f}")

        if curve_inverted or (vix_level is not None and vix_level > VIX_RISK_OFF_ABOVE):
            risk_regime = RiskRegime.RISK_OFF
        elif vix_level is not None and vix_level < VIX_RISK_ON_BELOW:
            risk_regime = RiskRegime.RISK_ON
        else:
            risk_regime = RiskRegime.NEUTRAL

        return MacroRegimeAssessment(
            as_of=str(date.today()),
            regime=regime,
            growth_direction=growth_direction,
            inflation_direction=inflation_direction,
            risk_regime=risk_regime,
            growth_score=round(growth_score, 4),
            inflation_score=round(inflation_score, 4),
            yield_curve_spread=curve_spread,
            yield_curve_inverted=curve_inverted,
            vix_level=vix_level,
            reasoning=reasoning,
            inputs=[_snapshot(a, s) for a, s in series_map.items()],
        )
