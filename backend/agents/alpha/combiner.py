"""Regime-conditional factor combination into a standardized [-1, +1] signal.

This is the first agent that consumes another agent's output: the macro regime
from Agent 6 (`agents.macro`) selects the factor weights, and the risk regime
scales gross exposure.

The regime->weight mapping encodes a standard, defensible premise: trend
factors (momentum) do well in expansions and break down in contractions —
momentum crashes cluster in stressed/transitional regimes — while defensive
factors (low volatility) hold up better when growth is contracting. These are
priors, not fitted parameters; they are deliberately hand-set and auditable
rather than optimized, so a bad backtest can't quietly tune them into
overfitting. Agent 9 is where they should be validated.
"""

import logging

import numpy as np
import pandas as pd

from agents.macro.schemas import MacroRegime, RiskRegime

from .factors import compute_raw_factors, cross_sectional_normalize
from .schemas import AlphaSignal, FactorValue, SignalBundle

logger = logging.getLogger(__name__)

REGIME_FACTOR_WEIGHTS: dict[MacroRegime, dict[str, float]] = {
    MacroRegime.INFLATIONARY_EXPANSION: {
        "momentum_12_1": 0.45,
        "reversal_5d": 0.15,
        "low_volatility": 0.20,
        "volume_trend": 0.20,
    },
    MacroRegime.DISINFLATIONARY_GROWTH: {
        "momentum_12_1": 0.50,
        "reversal_5d": 0.15,
        "low_volatility": 0.20,
        "volume_trend": 0.15,
    },
    MacroRegime.STAGFLATION: {
        "momentum_12_1": 0.15,
        "reversal_5d": 0.25,
        "low_volatility": 0.45,
        "volume_trend": 0.15,
    },
    MacroRegime.DEFLATIONARY_CONTRACTION: {
        "momentum_12_1": 0.10,
        "reversal_5d": 0.30,
        "low_volatility": 0.45,
        "volume_trend": 0.15,
    },
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
    ) -> SignalBundle:
        raw = compute_raw_factors(prices, volumes, as_of=as_of)
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
