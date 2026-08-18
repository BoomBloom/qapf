import warnings

import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from statsmodels.tsa.stattools import adfuller, coint, kpss
from statsmodels.tsa.vector_ar.vecm import coint_johansen

from .schemas import (
    CointegrationResult,
    DeflatedSharpeResult,
    JohansenResult,
    StationarityResult,
)

EULER_MASCHERONI = 0.5772156649015329


class ProbabilityStatisticsToolkit:
    """Statistical rigor layer for the alpha pipeline: stationarity and
    cointegration tests for pairs/signal candidates, and the Deflated Sharpe
    Ratio for catching backtest overfitting before a strategy reaches the
    Backtest Validation agent."""

    def test_stationarity(self, series: pd.Series, name: str = "series") -> StationarityResult:
        series = series.dropna()
        adf_stat, adf_p, *_ = adfuller(series, autolag="AIC")
        # KPSS emits an InterpolationWarning whenever the p-value falls
        # outside its lookup table's range (very common at the extremes) --
        # that's expected behavior, not a computation error.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            kpss_stat, kpss_p, *_ = kpss(series, regression="c", nlags="auto")

        adf_stationary = adf_p < 0.05
        kpss_stationary = kpss_p > 0.05

        return StationarityResult(
            series_name=name,
            adf_statistic=float(adf_stat),
            adf_pvalue=float(adf_p),
            adf_is_stationary=adf_stationary,
            kpss_statistic=float(kpss_stat),
            kpss_pvalue=float(kpss_p),
            kpss_is_stationary=kpss_stationary,
            agree=adf_stationary == kpss_stationary,
        )

    def test_cointegration_engle_granger(
        self, series_a: pd.Series, series_b: pd.Series, name_a: str = "a", name_b: str = "b"
    ) -> CointegrationResult:
        df = pd.concat([series_a, series_b], axis=1).dropna()
        a, b = df.iloc[:, 0].to_numpy(), df.iloc[:, 1].to_numpy()
        test_stat, pvalue, _ = coint(a, b)
        hedge_ratio = float(np.polyfit(b, a, 1)[0])  # OLS: a = hedge_ratio * b + const

        return CointegrationResult(
            series_a=name_a,
            series_b=name_b,
            method="engle-granger",
            test_statistic=float(test_stat),
            pvalue=float(pvalue),
            is_cointegrated=pvalue < 0.05,
            hedge_ratio=hedge_ratio,
        )

    def test_cointegration_johansen(
        self, df: pd.DataFrame, names: list[str] | None = None
    ) -> JohansenResult:
        df = df.dropna()
        # statsmodels' eigenvalue decomposition here routinely produces
        # eigenvalues with a negligible (floating-point-noise) imaginary part,
        # which it then casts to real -- a known, harmless quirk of this
        # specific function, not a sign of a computation error.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=np.exceptions.ComplexWarning)
            result = coint_johansen(df, det_order=0, k_ar_diff=1)
        trace_stats = [float(x) for x in result.lr1]
        critical_values_95 = [float(x) for x in result.cvt[:, 1]]  # column 1 = 95% level
        rank = sum(t > c for t, c in zip(trace_stats, critical_values_95))

        return JohansenResult(
            series_names=names or list(df.columns),
            trace_statistics=trace_stats,
            critical_values_95=critical_values_95,
            cointegrating_rank=rank,
        )

    def deflated_sharpe_ratio(self, returns: pd.Series, n_trials: int) -> DeflatedSharpeResult:
        """Bailey & Lopez de Prado (2014), "The Deflated Sharpe Ratio: Correcting
        for Selection Bias, Backtest Overfitting, and Non-Normality". Answers:
        given this Sharpe ratio was the best of `n_trials` attempts, what's the
        probability it's genuinely positive rather than the best of pure noise?
        """
        returns = returns.dropna()
        n = len(returns)
        sr = float(returns.mean() / returns.std(ddof=1))
        skew = float(sp_stats.skew(returns))
        kurt = float(sp_stats.kurtosis(returns, fisher=False))  # non-excess; normal == 3

        if n_trials > 1:
            z_a = sp_stats.norm.ppf(1 - 1.0 / n_trials)
            z_b = sp_stats.norm.ppf(1 - 1.0 / (n_trials * np.e))
            expected_max_sr = ((1 - EULER_MASCHERONI) * z_a + EULER_MASCHERONI * z_b) / np.sqrt(n)
        else:
            expected_max_sr = 0.0

        sr_variance_term = 1 - skew * sr + (kurt - 1) / 4 * sr**2
        sr_std = np.sqrt(sr_variance_term / (n - 1)) if sr_variance_term > 0 else np.nan
        dsr = float(sp_stats.norm.cdf((sr - expected_max_sr) / sr_std)) if sr_std and sr_std > 0 else 0.0

        return DeflatedSharpeResult(
            observed_sharpe=sr,
            n_trials=n_trials,
            n_observations=n,
            skewness=skew,
            kurtosis=kurt,
            expected_max_sharpe=float(expected_max_sr),
            deflated_sharpe_ratio=dsr,
            is_significant=dsr > 0.95,
        )
