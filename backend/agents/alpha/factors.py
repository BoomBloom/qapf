"""Factor computation in plain pandas.

Deliberately NOT using Qlib's expression engine (`Ref`/`Mean`/`Std`): that
engine silently returns empty results under the current numpy/pandas stack —
see `.claude/references/qlib-known-issues.md`. Computing factors here keeps the
alpha layer independent of that bug; Qlib is still used for backtesting, which
is verified working.

Every function takes an explicit `as_of` date and slices to it internally, so
a caller can pass a full history without leaking future data into a
point-in-time factor value. `test_no_lookahead_bias` in `__main__.py` verifies
this by corrupting post-`as_of` rows and asserting the output is unchanged.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Trading-day lookbacks.
MOMENTUM_LONG = 252  # ~12 months
MOMENTUM_SKIP = 21  # skip the most recent month: short-term reversal contaminates 12-1 momentum
REVERSAL_WINDOW = 5
VOL_WINDOW = 60
VOLUME_SHORT = 20
VOLUME_LONG = 60

MIN_HISTORY = MOMENTUM_LONG + 1


def _slice_to(df: pd.DataFrame, as_of: pd.Timestamp | None) -> pd.DataFrame:
    """Keep only rows at or before `as_of` — the point-in-time guarantee."""
    if as_of is None:
        return df
    return df.loc[df.index <= as_of]


def momentum_12_1(prices: pd.Series) -> float | None:
    """12-month return ending one month ago (Jegadeesh-Titman style).

    The one-month skip is the standard construction: including the most recent
    month mixes in short-term reversal, which points the opposite way.
    """
    if len(prices) < MOMENTUM_LONG + 1:
        return None
    recent = prices.iloc[-(MOMENTUM_SKIP + 1)]
    old = prices.iloc[-MOMENTUM_LONG]
    if old == 0 or pd.isna(recent) or pd.isna(old):
        return None
    return float(recent / old - 1.0)


def reversal_5d(prices: pd.Series) -> float | None:
    """Negated 5-day return: recent losers tend to bounce short-term."""
    if len(prices) < REVERSAL_WINDOW + 1:
        return None
    last, prior = prices.iloc[-1], prices.iloc[-(REVERSAL_WINDOW + 1)]
    if prior == 0 or pd.isna(last) or pd.isna(prior):
        return None
    return float(-(last / prior - 1.0))


def low_volatility(prices: pd.Series) -> float | None:
    """Negated realized volatility — the low-volatility anomaly says low-vol
    names earn higher risk-adjusted returns, so less vol is a positive signal."""
    if len(prices) < VOL_WINDOW + 1:
        return None
    returns = prices.pct_change().dropna().iloc[-VOL_WINDOW:]
    if returns.empty:
        return None
    vol = float(returns.std(ddof=1))
    return -vol if np.isfinite(vol) else None


def volume_trend(volumes: pd.Series) -> float | None:
    """Short-window average volume relative to a longer window: rising
    participation."""
    if len(volumes) < VOLUME_LONG:
        return None
    short = float(volumes.iloc[-VOLUME_SHORT:].mean())
    long = float(volumes.iloc[-VOLUME_LONG:].mean())
    if long == 0 or not np.isfinite(short) or not np.isfinite(long):
        return None
    return float(short / long - 1.0)


FACTOR_FUNCTIONS = {
    "momentum_12_1": ("price", momentum_12_1),
    "reversal_5d": ("price", reversal_5d),
    "low_volatility": ("price", low_volatility),
    "volume_trend": ("volume", volume_trend),
}


def compute_raw_factors(
    prices: pd.DataFrame,
    volumes: pd.DataFrame,
    as_of: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Compute every factor for every ticker as of `as_of`.

    Returns a DataFrame indexed by ticker with one column per factor. Tickers
    without enough history yield NaN rather than being silently dropped, so the
    caller can see coverage.
    """
    px = _slice_to(prices, as_of)
    vol = _slice_to(volumes, as_of)

    if px.empty:
        raise ValueError(f"No price data at or before {as_of}.")

    rows = {}
    for ticker in px.columns:
        price_series = px[ticker].dropna()
        volume_series = vol[ticker].dropna() if ticker in vol.columns else pd.Series(dtype=float)
        values = {}
        for factor_name, (source, func) in FACTOR_FUNCTIONS.items():
            series = price_series if source == "price" else volume_series
            values[factor_name] = func(series)
        rows[ticker] = values

    return pd.DataFrame.from_dict(rows, orient="index")


def cross_sectional_normalize(factor_values: pd.Series) -> pd.Series:
    """Map a factor's cross-section to [-1, +1] by rank.

    Rank-based rather than z-score: a single extreme outlier would dominate a
    z-score and distort every other name's signal, whereas ranks are bounded
    by construction. With a single valid observation there is no cross-section
    to rank, so it maps to 0.0 (no view) rather than an arbitrary extreme.
    """
    valid = factor_values.dropna()
    if valid.empty:
        return pd.Series(np.nan, index=factor_values.index, dtype=float)
    if len(valid) == 1:
        out = pd.Series(np.nan, index=factor_values.index, dtype=float)
        out.loc[valid.index[0]] = 0.0
        return out

    ranks = valid.rank(method="average")
    scaled = (ranks - 1.0) / (len(valid) - 1.0) * 2.0 - 1.0
    return scaled.reindex(factor_values.index)
