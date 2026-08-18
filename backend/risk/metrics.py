"""Pure risk-metric functions: no I/O, no agent state, nothing but numbers in,
numbers out. Kept separate from monitor.py's decision logic so each metric can
be verified against a case with a known analytical answer, independent of the
kill-switch rules built on top of it.
"""

import numpy as np
import pandas as pd
from scipy import stats as sp_stats


def historical_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Empirical VaR: the loss magnitude not exceeded (1-confidence) of the
    time in the observed sample. Returns a positive number (a loss size)."""
    returns = returns.dropna()
    return float(-np.percentile(returns, (1 - confidence) * 100))


def historical_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """Expected Shortfall: the average loss in the tail beyond the VaR
    threshold. Always >= VaR — it answers "how bad, on average, when it's
    bad" rather than VaR's "how bad, at this percentile"."""
    returns = returns.dropna()
    threshold = np.percentile(returns, (1 - confidence) * 100)
    tail = returns[returns <= threshold]
    if tail.empty:
        return float(-threshold)
    return float(-tail.mean())


def parametric_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Gaussian VaR, for comparison against historical_var. Real returns are
    fat-tailed (Agent 4 measured KO's daily kurtosis at ~5.1 vs. the normal
    distribution's 3.0), so this is expected to UNDERSTATE tail risk relative
    to the historical method on the same data — verified, not just asserted,
    in __main__.py."""
    returns = returns.dropna()
    mu, sigma = returns.mean(), returns.std(ddof=1)
    z = sp_stats.norm.ppf(1 - confidence)
    return float(-(mu + z * sigma))


def drawdown_series(returns: pd.Series) -> pd.Series:
    equity = (1 + returns).cumprod()
    running_max = equity.cummax()
    return (equity - running_max) / running_max


def max_drawdown(returns: pd.Series) -> float:
    return float(drawdown_series(returns).min())
