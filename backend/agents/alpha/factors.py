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
    """Negated realized volatility (close-to-close) — the low-volatility
    anomaly says low-vol names earn higher risk-adjusted returns, so less vol
    is a positive signal. This is the FALLBACK used when open/high/low aren't
    available; `yang_zhang_volatility` below is preferred when they are (see
    `compute_raw_factors`) — validated 2026-08-20 via a real walk-forward
    backtest (`.scratch/wayfinder-real-capital/yang_zhang_diagnostic.py`) to
    materially reduce drawdown (-26.48% -> -17.64%) over this replacement
    alone, holding everything else in the pipeline fixed."""
    if len(prices) < VOL_WINDOW + 1:
        return None
    returns = prices.pct_change().dropna().iloc[-VOL_WINDOW:]
    if returns.empty:
        return None
    vol = float(returns.std(ddof=1))
    return -vol if np.isfinite(vol) else None


def yang_zhang_volatility(
    open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, window: int = VOL_WINDOW
) -> float | None:
    """Yang & Zhang (2000) range-based volatility estimator: drift-independent,
    unbiased in the continuous limit, and handles opening jumps -- unlike
    close-to-close std, which only sees where a name ended up, not how it got
    there. Kept on the same non-annualized daily scale `low_volatility` uses,
    so the two are directly comparable / swappable.

        o_i  = ln(O_i / C_{i-1})                                overnight return
        c_i  = ln(C_i / O_i)                                    open-to-close return
        rs_i = ln(H_i/C_i)*ln(H_i/O_i) + ln(L_i/C_i)*ln(L_i/O_i) Rogers-Satchell term
        k    = 0.34 / (1.34 + (n+1)/(n-1))
        sigma_YZ^2 = Var(o) + k*Var(c) + (1-k)*mean(rs)

    Returns None (never a fabricated number) on insufficient history or any
    non-positive OHLC value, since a log of a non-positive price is undefined
    -- silently emitting NaN-derived garbage here would corrupt every
    downstream cross-sectional rank silently, not loudly.
    """
    df = pd.DataFrame({"o": open_, "h": high, "l": low, "c": close}).dropna()
    if len(df) < window + 1:
        return None
    df = df.iloc[-(window + 1):]
    prev_c = df["c"].shift(1).iloc[1:]
    df = df.iloc[1:]

    if (df[["o", "h", "l", "c"]] <= 0).any().any() or (prev_c <= 0).any():
        return None

    o_i = np.log(df["o"] / prev_c)
    c_i = np.log(df["c"] / df["o"])
    rs_i = (
        np.log(df["h"] / df["c"]) * np.log(df["h"] / df["o"])
        + np.log(df["l"] / df["c"]) * np.log(df["l"] / df["o"])
    )

    n = len(df)
    if n < 2:
        return None
    var_o, var_c, mean_rs = float(o_i.var(ddof=1)), float(c_i.var(ddof=1)), float(rs_i.mean())
    k = 0.34 / (1.34 + (n + 1) / (n - 1))
    sigma_sq = var_o + k * var_c + (1 - k) * mean_rs
    if sigma_sq < 0 or not np.isfinite(sigma_sq):
        return None  # a real variance can't be negative; can happen on small/adversarial samples
    return -float(np.sqrt(sigma_sq))  # negated, matching low_volatility's sign convention


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
    opens: pd.DataFrame | None = None,
    highs: pd.DataFrame | None = None,
    lows: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Compute every factor for every ticker as of `as_of`.

    Returns a DataFrame indexed by ticker with one column per factor. Tickers
    without enough history yield NaN rather than being silently dropped, so the
    caller can see coverage.

    `opens`/`highs`/`lows` are optional and additive, not a breaking change:
    when all three are supplied, `low_volatility` uses the Yang-Zhang
    range-based estimator (validated 2026-08-20 to materially reduce
    drawdown); when any are missing, it falls back to the original
    close-to-close estimator exactly as before. Existing callers that only
    pass prices/volumes are unaffected.
    """
    px = _slice_to(prices, as_of)
    vol = _slice_to(volumes, as_of)
    op = _slice_to(opens, as_of) if opens is not None else None
    hi = _slice_to(highs, as_of) if highs is not None else None
    lo = _slice_to(lows, as_of) if lows is not None else None
    has_ohlc = op is not None and hi is not None and lo is not None

    if px.empty:
        raise ValueError(f"No price data at or before {as_of}.")

    rows = {}
    for ticker in px.columns:
        price_series = px[ticker].dropna()
        volume_series = vol[ticker].dropna() if ticker in vol.columns else pd.Series(dtype=float)
        values = {}
        for factor_name, (source, func) in FACTOR_FUNCTIONS.items():
            if factor_name == "low_volatility" and has_ohlc and ticker in op.columns and ticker in hi.columns and ticker in lo.columns:
                values[factor_name] = yang_zhang_volatility(
                    op[ticker], hi[ticker], lo[ticker], price_series
                )
                continue
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
