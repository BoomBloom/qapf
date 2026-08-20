"""Factor combination into a standardized [-1, +1] signal.

This is the first agent that consumes another agent's output: the macro regime
from Agent 6 (`agents.macro`) still selects the risk regime's gross-exposure
scale, but as of 2026-08-19 it no longer selects factor weights (see below).

FACTOR WEIGHTS ARE FLAT, NOT REGIME-CONDITIONAL (decided 2026-08-19, wayfinder
ticket 06 in .scratch/wayfinder-real-capital/). The original design weighted
momentum higher in expansions and low-volatility higher in contractions, on
the premise that trend factors do well in expansions and break down when
growth contracts. Two independent lines of evidence overturned that premise
before it reached real capital:

1. Agent 14 (Model Risk) measured the strategy's own regime-by-regime Sharpe
   and found the OPPOSITE of the design's assumption (+1.16 in contraction,
   -0.32 in growth) -- but that reading was itself later shown to be
   underpowered (a sub-1-year regime segment has SE(Sharpe) ~ 1.0, so the gap
   carries t < 1) and confounded by market beta, since the book is long-only.
   See docs/research/regime-factor-evidence.md.
2. A literature review (same doc) found the best-powered published test of
   growth x inflation quadrant conditioning -- a construction nearly identical
   to this one -- reports "for momentum, nothing is significant." Momentum's
   real, well-evidenced conditioner is MARKET state (Daniel & Moskowitz's
   bear-market x ex-ante-variance interaction), not macro quadrants.

Given that, inverting the weights (as Agent 14's raw numbers alone might
suggest) would have been wrong -- it would place maximum momentum weight
exactly where the literature measures the premium far lower. The chosen
response is to FLATTEN: remove the unsupported conditioner rather than guess
its sign. This is attempt 1 of a 5-attempt validation budget (ticket 02); if
flat factors clear the bar, regime conditioning was never needed. If they
fail, the problem is the factors themselves, not the conditioner -- which
determines whether attempt 2 re-instruments on market state (the
better-evidenced option) or looks for new factors entirely.

REGIME_FACTOR_WEIGHTS is kept as a dict keyed by regime -- not simplified to a
single flat dict -- so re-instrumenting later doesn't require rebuilding this
structure, only its values. Every regime maps to the identical weights below.
"""

import logging

import numpy as np
import pandas as pd

from agents.macro.schemas import MacroRegime, RiskRegime

from .factors import compute_raw_factors, cross_sectional_normalize
from .schemas import AlphaSignal, FactorValue, SignalBundle

logger = logging.getLogger(__name__)

_FLAT_WEIGHTS = {
    "momentum_12_1": 0.25,
    "reversal_5d": 0.25,
    "low_volatility": 0.25,
    "volume_trend": 0.25,
}

REGIME_FACTOR_WEIGHTS: dict[MacroRegime, dict[str, float]] = {
    MacroRegime.INFLATIONARY_EXPANSION: dict(_FLAT_WEIGHTS),
    MacroRegime.DISINFLATIONARY_GROWTH: dict(_FLAT_WEIGHTS),
    MacroRegime.STAGFLATION: dict(_FLAT_WEIGHTS),
    MacroRegime.DEFLATIONARY_CONTRACTION: dict(_FLAT_WEIGHTS),
}

RISK_EXPOSURE_SCALE: dict[RiskRegime, float] = {
    RiskRegime.RISK_ON: 1.0,
    RiskRegime.NEUTRAL: 0.7,
    RiskRegime.RISK_OFF: 0.4,
}


class AlphaCombiner:
    def __init__(self):
        for regime, weights in REGIME_FACTOR_WEIGHTS.items():
            total = sum(weights.values())
            if not np.isclose(total, 1.0):
                raise ValueError(f"Weights for {regime} sum to {total}, expected 1.0.")

    def generate(
        self,
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        macro_regime: MacroRegime,
        risk_regime: RiskRegime,
        as_of: pd.Timestamp | None = None,
        opens: pd.DataFrame | None = None,
        highs: pd.DataFrame | None = None,
        lows: pd.DataFrame | None = None,
    ) -> SignalBundle:
        """`opens`/`highs`/`lows` are optional -- when supplied, low_volatility
        uses the Yang-Zhang range estimator instead of close-to-close std (see
        factors.compute_raw_factors's docstring); existing callers that don't
        pass them are unaffected."""
        raw = compute_raw_factors(prices, volumes, as_of=as_of, opens=opens, highs=highs, lows=lows)
        normalized = pd.DataFrame(
            {col: cross_sectional_normalize(raw[col]) for col in raw.columns},
            index=raw.index,
        )

        weights = REGIME_FACTOR_WEIGHTS[macro_regime]
        exposure_scale = RISK_EXPOSURE_SCALE[risk_regime]
        effective_date = as_of if as_of is not None else prices.index[-1]

        signals: list[AlphaSignal] = []
        for ticker in normalized.index:
            factor_values: list[FactorValue] = []
            weighted_sum = 0.0
            abs_weighted_sum = 0.0
            weight_used = 0.0

            for factor_name, weight in weights.items():
                norm_value = normalized.at[ticker, factor_name]
                if pd.isna(norm_value):
                    continue
                factor_values.append(
                    FactorValue(
                        name=factor_name,
                        raw_value=float(raw.at[ticker, factor_name]),
                        normalized_value=float(norm_value),
                    )
                )
                weighted_sum += weight * float(norm_value)
                abs_weighted_sum += weight * abs(float(norm_value))
                weight_used += weight

            if weight_used == 0.0:
                # No usable factors (insufficient history) — emit no view rather
                # than a fabricated one.
                signals.append(
                    AlphaSignal(
                        ticker=ticker,
                        as_of=str(effective_date.date()),
                        signal=0.0,
                        confidence=0.0,
                        factors=[],
                    )
                )
                continue

            # Renormalize over the factors that were actually available so a
            # ticker missing one factor isn't systematically shrunk toward zero.
            combined = weighted_sum / weight_used
            # Agreement: 1.0 when every factor points the same way, ~0 when they
            # cancel out. Independent of the signal's magnitude.
            confidence = abs(weighted_sum) / abs_weighted_sum if abs_weighted_sum > 0 else 0.0

            signals.append(
                AlphaSignal(
                    ticker=ticker,
                    as_of=str(effective_date.date()),
                    signal=float(np.clip(combined * exposure_scale, -1.0, 1.0)),
                    confidence=float(np.clip(confidence, 0.0, 1.0)),
                    factors=factor_values,
                )
            )

        return SignalBundle(
            as_of=str(effective_date.date()),
            universe_size=len(normalized.index),
            macro_regime=macro_regime.value,
            risk_regime=risk_regime.value,
            factor_weights=weights,
            exposure_scale=exposure_scale,
            signals=sorted(signals, key=lambda s: s.signal, reverse=True),
        )
